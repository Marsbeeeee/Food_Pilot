import React, { useEffect, useRef, useState } from 'react';

import { resolveFoodLogSavePresentation } from '../app/workspaceFoodLogState';
import {
  ChatApiError,
  createChatMessage,
  createChatSession,
  deleteChatSession,
  getChatSession,
  mergeSessionIntoList,
  renameChatSession,
  sendChatMessage,
} from '../api/chat';
import { FoodLogApiError, saveFoodLogEntry } from '../api/foodLog';
import { ConfirmDialog } from '../components/ConfirmDialog';
import { ChatMessageType, ChatSession, FoodLogEntry, Message } from '../types/types';

interface WorkspaceProps {
  sessions: ChatSession[];
  setSessions: React.Dispatch<React.SetStateAction<ChatSession[]>>;
  foodLog: FoodLogEntry[];
  activeSessionId: string;
  setActiveSessionId: (id: string) => void;
  profileId?: number;
  refreshFoodLog: () => Promise<void>;
  onDeleteFoodLog: (entryId: string) => Promise<void>;
  unlinkDeletedChatFromFoodLog: (sessionId: string) => Promise<void>;
}

export const Workspace: React.FC<WorkspaceProps> = ({
  sessions,
  setSessions,
  foodLog,
  activeSessionId,
  setActiveSessionId,
  profileId,
  refreshFoodLog,
  onDeleteFoodLog,
  unlinkDeletedChatFromFoodLog,
}) => {
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isRenameModalOpen, setIsRenameModalOpen] = useState(false);
  const [renamingTitle, setRenamingTitle] = useState('');
  const [deleteSessionId, setDeleteSessionId] = useState<string | null>(null);
  const [isDeletingSession, setIsDeletingSession] = useState(false);
  const [isCreatingSession, setIsCreatingSession] = useState(false);
  const [isLoadingSessionId, setIsLoadingSessionId] = useState<string | null>(null);
  const [savingFoodLogMessageIds, setSavingFoodLogMessageIds] = useState<string[]>([]);
  const [savedFoodLogMessageIds, setSavedFoodLogMessageIds] = useState<Record<string, string>>({});
  const [failedFoodLogSaves, setFailedFoodLogSaves] = useState<Record<string, string>>({});
  const [deletingFoodLogMessageIds, setDeletingFoodLogMessageIds] = useState<string[]>([]);

  const chatContainerRef = useRef<HTMLDivElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (sessions.length > 0 && !activeSessionId) {
      setActiveSessionId(sessions[0].id);
    } else if (sessions.length === 0) {
      setActiveSessionId('');
    }
  }, [activeSessionId, sessions, setActiveSessionId]);

  const activeSession = sessions.find((session) => session.id === activeSessionId)
    || (sessions.length > 0 ? sessions[0] : null);
  const deleteSessionTarget = deleteSessionId
    ? sessions.find((session) => session.id === deleteSessionId) ?? null
    : null;
  const persistedSavedFoodLogEntriesByMessageId = new Map<string, FoodLogEntry>(
    foodLog
      .filter((entry): entry is FoodLogEntry & { sourceMessageId: string } => Boolean(entry.sourceMessageId))
      .map((entry) => [entry.sourceMessageId, entry]),
  );

  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [activeSession?.messages, isTyping]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsMenuOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  useEffect(() => {
    if (!isRenameModalOpen) {
      return undefined;
    }

    const handleEscapeKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setIsRenameModalOpen(false);
      }
    };

    document.addEventListener('keydown', handleEscapeKey);
    return () => document.removeEventListener('keydown', handleEscapeKey);
  }, [isRenameModalOpen]);

  const handleNewAnalysis = async () => {
    if (isCreatingSession) {
      return;
    }

    setIsCreatingSession(true);
    try {
      const newSession = await createChatSession();
      setSessions((prev) => mergeSessionIntoList(prev, newSession));
      setActiveSessionId(newSession.id);
    } catch (error) {
      handleChatError(error, 'Unable to create a new chat right now.');
    } finally {
      setIsCreatingSession(false);
    }
  };

  const handleSendMessage = async (text?: string) => {
    const finalQuery = text || inputValue.trim();
    if (!finalQuery || isTyping) {
      return;
    }

    const previousActiveSessionId = activeSessionId;
    const optimisticMessageId = `temp-user-${Date.now()}`;
    const optimisticMessage = buildOptimisticUserMessage(optimisticMessageId, finalQuery);
    const needsTemporarySession = !activeSessionId || sessions.length === 0;
    const optimisticSessionId = needsTemporarySession ? `temp-session-${Date.now()}` : null;
    const originalSession = !needsTemporarySession
      ? sessions.find((session) => session.id === activeSessionId) ?? null
      : null;

    if (originalSession && !originalSession.hasLoadedMessages) {
      await loadSessionDetail(originalSession.id);
    }

    setSessions((prev) => applyOptimisticUserMessage(
      prev,
      optimisticMessage,
      finalQuery,
      previousActiveSessionId,
      optimisticSessionId,
    ));
    if (optimisticSessionId) {
      setActiveSessionId(optimisticSessionId);
    }

    setIsTyping(true);
    setInputValue('');

    try {
      if (needsTemporarySession) {
        const exchange = await createChatMessage(finalQuery, profileId);
        setSessions((prev) => applyResolvedExchange(
          prev,
          exchange,
          optimisticMessageId,
          optimisticSessionId,
        ));
        setActiveSessionId(exchange.session.id);
        return;
      }

      const exchange = await sendChatMessage(previousActiveSessionId, finalQuery, profileId);
      setSessions((prev) => applyResolvedExchange(
        prev,
        exchange,
        optimisticMessageId,
        null,
      ));
      setActiveSessionId(exchange.session.id);
    } catch (error) {
      setInputValue(finalQuery);
      setSessions((prev) => rollbackOptimisticUserMessage(
        prev,
        optimisticMessageId,
        optimisticSessionId,
        previousActiveSessionId,
        originalSession,
      ));
      setActiveSessionId(previousActiveSessionId);
      handleChatError(error, '这条消息暂时发送失败，请稍后重试。');
    } finally {
      setIsTyping(false);
    }
  };

  const handleKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      void handleSendMessage();
    }
  };

  const openDeleteSessionDialog = (sessionId: string) => {
    if (!sessionId) {
      return;
    }

    setDeleteSessionId(sessionId);
    setIsMenuOpen(false);
  };

  const closeDeleteSessionDialog = () => {
    if (isDeletingSession) {
      return;
    }

    setDeleteSessionId(null);
  };

  const handleDeleteSession = async () => {
    if (!deleteSessionId || isDeletingSession) {
      return;
    }

    const sessionId = deleteSessionId;
    setIsDeletingSession(true);

    try {
      await deleteChatSession(sessionId);
      const remainingSessions = sessions.filter((session) => session.id !== sessionId);
      setSessions(remainingSessions);
      if (remainingSessions.length === 0) {
        setActiveSessionId('');
      } else if (sessionId === activeSessionId) {
        setActiveSessionId(remainingSessions[0].id);
      }
      await unlinkDeletedChatFromFoodLog(sessionId);
      setDeleteSessionId(null);
      setIsMenuOpen(false);
    } catch (error) {
      handleChatError(error, 'Unable to delete this chat right now.');
    } finally {
      setIsDeletingSession(false);
    }
  };

  const handleRenameSession = async () => {
    if (!activeSessionId || !renamingTitle.trim()) {
      return;
    }

    try {
      const renamedSession = await renameChatSession(activeSessionId, renamingTitle.trim());
      setSessions((prev) => prev.map((session) => (
        session.id === activeSessionId
          ? { ...session, title: renamedSession.title, timestamp: renamedSession.timestamp }
          : session
      )));
      setIsRenameModalOpen(false);
      setIsMenuOpen(false);
    } catch (error) {
      handleChatError(error, 'Unable to rename this chat right now.');
    }
  };

  const openRenameModal = () => {
    if (!activeSession) {
      return;
    }

    setRenamingTitle(activeSession.title);
    setIsRenameModalOpen(true);
    setIsMenuOpen(false);
  };

  const handleSelectSession = async (sessionId: string) => {
    setActiveSessionId(sessionId);
    const selectedSession = sessions.find((session) => session.id === sessionId);
    if (!selectedSession || selectedSession.hasLoadedMessages) {
      return;
    }

    await loadSessionDetail(sessionId);
  };

  const loadSessionDetail = async (sessionId: string) => {
    setIsLoadingSessionId(sessionId);
    try {
      const detailedSession = await getChatSession(sessionId);
      setSessions((prev) => prev.map((session) => (
        session.id === sessionId ? detailedSession : session
      )));
    } catch (error) {
      handleChatError(error, 'Unable to load this chat right now.');
    } finally {
      setIsLoadingSessionId((current) => (current === sessionId ? null : current));
    }
  };

  const handleSaveFoodLogEntry = async (
    sessionId: string,
    message: Message,
    mealDescription: string,
  ) => {
    if (getMessageType(message) !== 'meal_estimate') {
      return;
    }

    if (!message.id || !message.title || !message.description || !message.total || !message.items?.length) {
      return;
    }

    setSavingFoodLogMessageIds((current) => (
      current.includes(message.id as string) ? current : [...current, message.id as string]
    ));
    setFailedFoodLogSaves((current) => {
      const next = { ...current };
      delete next[message.id as string];
      return next;
    });

    try {
      const savedEntry = await saveFoodLogEntry({
        sourceType: 'chat_message',
        mealDescription,
        resultTitle: message.title,
        resultConfidence: message.confidence,
        resultDescription: message.description,
        totalCalories: message.total,
        ingredients: message.items,
        sessionId: Number(sessionId),
        sourceMessageId: Number(message.id),
        assistantSuggestion: message.content,
      });
      setSavedFoodLogMessageIds((current) => ({
        ...current,
        [message.id as string]: savedEntry.id,
      }));
      setFailedFoodLogSaves((current) => {
        const next = { ...current };
        delete next[message.id as string];
        return next;
      });
      await refreshFoodLog();
    } catch (error) {
      setFailedFoodLogSaves((current) => ({
        ...current,
        [message.id as string]: resolveFoodLogErrorMessage(
          error,
          '这条估算结果暂时无法保存到 Food Log，请稍后重试。',
        ),
      }));
    } finally {
      setSavingFoodLogMessageIds((current) => current.filter((item) => item !== message.id));
    }
  };

  const handleUndoFoodLogSave = async (messageId: string) => {
    const persistedEntry = persistedSavedFoodLogEntriesByMessageId.get(messageId);
    const entryId = persistedEntry?.id ?? savedFoodLogMessageIds[messageId];
    if (!entryId) {
      return;
    }

    setDeletingFoodLogMessageIds((current) => (
      current.includes(messageId) ? current : [...current, messageId]
    ));

    try {
      await onDeleteFoodLog(entryId);
      setSavedFoodLogMessageIds((current) => {
        const next = { ...current };
        delete next[messageId];
        return next;
      });
      setFailedFoodLogSaves((current) => {
        const next = { ...current };
        delete next[messageId];
        return next;
      });
    } catch (error) {
      handleFoodLogError(error, '暂时无法撤销这条 Food Log 保存记录，请稍后重试。');
    } finally {
      setDeletingFoodLogMessageIds((current) => current.filter((item) => item !== messageId));
    }
  };

  return (
    <div className="relative flex h-full min-h-0 flex-1 overflow-hidden">
      <aside className="flex min-h-0 w-72 shrink-0 flex-col border-r border-[#4A453E]/5 bg-[#FFFDF5]">
        <div className="flex h-full min-h-0 flex-col gap-6 p-6">
          <button
            onClick={() => void handleNewAnalysis()}
            disabled={isCreatingSession}
            className="bg-[#FF8A65] text-white rounded-[20px] flex w-full items-center justify-center gap-2 h-12 px-4 text-sm font-bold shadow-lg shadow-[#FF8A65]/10 hover:shadow-xl hover:translate-y-[-1px] transition-all active:scale-95 active:translate-y-0 disabled:cursor-not-allowed disabled:opacity-70"
          >
            <span className="material-symbols-outlined text-[20px]">add_circle</span>
            <span>Start New Chat</span>
          </button>

          <div className="custom-scrollbar flex min-h-0 flex-1 flex-col gap-6 overflow-y-auto pr-2 pb-10">
            <div>
              <h3 className="mb-4 px-3 text-[10px] font-bold uppercase tracking-[0.2em] text-[#4A453E]/30">Chats</h3>
              <div className="flex flex-col gap-1">
                {sessions.map((session) => {
                  const lastResult = [...session.messages].reverse().find(isMealEstimateMessage);
                  const sessionStatus = getSessionStatusLabel(
                    session,
                    isLoadingSessionId === session.id,
                  );

                  return (
                    <div
                      key={session.id}
                      onClick={() => void handleSelectSession(session.id)}
                      className={`group flex items-start gap-4 rounded-[16px] border p-4 transition-all ${
                        activeSessionId === session.id
                          ? 'bg-[#F7F3E9] border-[#4A453E]/10'
                          : 'bg-transparent border-transparent hover:bg-[#F7F3E9]/60'
                      }`}
                    >
                      <div className={`mt-1.5 size-2 shrink-0 rounded-full ${activeSessionId === session.id ? 'bg-[#FF8A65]' : 'bg-[#4A453E]/10'}`}></div>
                      <div className="min-w-0 flex-1">
                        <p className={`mb-1 truncate text-[13px] ${activeSessionId === session.id ? 'font-bold text-[#4A453E]' : 'font-medium text-[#4A453E]/60 group-hover:text-[#4A453E]/80'}`}>
                          {session.title}
                        </p>
                        <div className="flex items-center justify-between">
                          <span className="text-[10px] font-bold uppercase tracking-wider text-[#4A453E]/30">
                            {sessionStatus}
                          </span>
                          {lastResult?.total && (
                            <span className="rounded border border-[#4A453E]/5 bg-white/60 px-1.5 py-0.5 text-[10px] font-bold text-[#4A453E]/50">
                              {lastResult.total}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
                {sessions.length === 0 && (
                  <p className="px-3 text-[11px] italic text-[#4A453E]/30">No chats yet.</p>
                )}
              </div>
            </div>
          </div>
        </div>
      </aside>

      <section className="relative flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden bg-[#FFFDF5]">
        {activeSession && (
          <div className="z-10 flex items-center justify-between border-b border-[#4A453E]/5 bg-white/40 px-10 py-4 backdrop-blur-sm">
            <div className="flex items-center gap-3">
              <span className="material-symbols-outlined text-[20px] text-[#4A453E]/20">auto_awesome</span>
              <span className="font-serif-brand text-[13px] font-bold italic tracking-wide text-[#4A453E]">
                {activeSession.title}
              </span>
            </div>
            <div className="relative flex items-center gap-2" ref={menuRef}>
              <button
                onClick={() => setIsMenuOpen(!isMenuOpen)}
                className={`rounded-full p-1 transition-colors ${isMenuOpen ? 'text-[#FF8A65] bg-[#FF8A65]/10' : 'text-[#4A453E]/30 hover:text-[#FF8A65] hover:bg-[#FF8A65]/5'}`}
              >
                <span className="material-symbols-outlined text-[20px]">more_vert</span>
              </button>

              {isMenuOpen && (
                <div className="absolute right-0 top-full z-50 mt-2 w-48 overflow-hidden rounded-[20px] border border-[#4A453E]/10 bg-white py-2 shadow-xl animate-in fade-in slide-in-from-top-2 duration-200">
                  <button
                    onClick={openRenameModal}
                    className="flex w-full items-center gap-3 px-4 py-3 text-sm font-bold text-[#4A453E]/70 transition-colors hover:bg-[#F7F3E9] hover:text-[#4A453E]"
                  >
                    <span className="material-symbols-outlined text-[18px]">edit</span>
                    Rename
                  </button>
                  <div className="mx-2 my-1 h-[1px] bg-[#4A453E]/5"></div>
                  <button
                    onClick={() => openDeleteSessionDialog(activeSessionId)}
                    className="flex w-full items-center gap-3 px-4 py-3 text-sm font-bold text-red-400 transition-colors hover:bg-red-50"
                  >
                    <span className="material-symbols-outlined text-[18px]">delete</span>
                    Delete
                  </button>
                </div>
              )}
            </div>
          </div>
        )}

        <div
          ref={chatContainerRef}
          className="custom-scrollbar flex min-h-0 flex-1 flex-col gap-10 overflow-y-auto px-6 py-10 scroll-smooth md:px-16"
        >
          {(!activeSession || activeSession.messages.length === 0) ? (
            <div className="flex flex-1 flex-col items-center justify-center py-20 text-center">
              <div className="mb-8 flex size-20 items-center justify-center rounded-[40px] border border-[#4A453E]/5 bg-white shadow-sm">
                <span className="material-symbols-outlined text-4xl text-[#FF8A65]">restaurant</span>
              </div>
              <h3 className="mb-3 font-serif-brand text-3xl font-bold italic text-[#4A453E]">从一餐描述、一个问题或一个目标开始。</h3>
              <p className="max-w-md text-base leading-relaxed text-[#4A453E]/50">
                你可以直接描述吃了什么、询问大概热量和营养，或让 Food Pilot 帮你推荐更合适的吃法。
                值得保留的估算结果可以再保存到 Food Log。
              </p>
              <div className="mt-10 grid w-full max-w-lg grid-cols-1 gap-3 sm:grid-cols-2">
                <button onClick={() => void handleSendMessage('一份牛油果吐司大概有什么营养？')} className="group rounded-[20px] border border-[#4A453E]/5 bg-white p-4 text-left transition-all hover:border-[#FF8A65]/30 hover:bg-[#F7F3E9]/20">
                  <p className="mb-1 text-[13px] font-bold text-[#4A453E]">估算这餐</p>
                  <p className="text-xs text-[#4A453E]/40 group-hover:text-[#4A453E]/60">“一份牛油果吐司大概有什么营养？”</p>
                </button>
                <button onClick={() => void handleSendMessage('晚饭在 poke 和拉面之间怎么选更合适？')} className="group rounded-[20px] border border-[#4A453E]/5 bg-white p-4 text-left transition-all hover:border-[#FF8A65]/30 hover:bg-[#F7F3E9]/20">
                  <p className="mb-1 text-[13px] font-bold text-[#4A453E]">推荐怎么吃</p>
                  <p className="text-xs text-[#4A453E]/40 group-hover:text-[#4A453E]/60">“晚饭在 poke 和拉面之间怎么选更合适？”</p>
                </button>
              </div>
            </div>
          ) : (
            activeSession.messages.map((message, index) => (
              (() => {
                const messageType = getMessageType(message);
                const isMealEstimate = messageType === 'meal_estimate';
                const isMealRecommendation = messageType === 'meal_recommendation';
                const mealDescription = isMealEstimate
                  ? resolveMealDescription(activeSession.messages, index, message)
                  : null;
                const savedFoodLogEntryId = message.id
                  ? (
                    savedFoodLogMessageIds[message.id]
                    || persistedSavedFoodLogEntriesByMessageId.get(message.id)?.id
                    || null
                  )
                  : null;
                const saveFailureMessage = message.id
                  ? failedFoodLogSaves[message.id]
                  : undefined;
                const isSavedToFoodLog = Boolean(savedFoodLogEntryId);
                const isSavingToFoodLog = Boolean(message.id && savingFoodLogMessageIds.includes(message.id));
                const isSaveFailedToFoodLog = Boolean(
                  message.id
                  && failedFoodLogSaves[message.id]
                  && !isSavingToFoodLog
                  && !isSavedToFoodLog,
                );
                const isDeletingSavedFoodLog = Boolean(
                  message.id && deletingFoodLogMessageIds.includes(message.id),
                );
                const savePresentation = resolveFoodLogSavePresentation({
                  savedEntryId: savedFoodLogEntryId,
                  isSaving: isSavingToFoodLog,
                  failedMessage: isSaveFailedToFoodLog ? saveFailureMessage : undefined,
                });
                const saveState = savePresentation.state;

                return (
                  <div key={message.id ?? index} className={`flex items-start gap-5 ${message.role === 'user' ? 'justify-end' : ''}`}>
                    {message.role === 'assistant' && (
                      <div className="mt-1 flex size-10 shrink-0 items-center justify-center rounded-2xl border border-[#4A453E]/10 bg-white shadow-sm">
                        <span className="material-symbols-outlined text-[22px] text-[#FF8A65]">auto_awesome</span>
                      </div>
                    )}

                    <div className={`flex max-w-[95%] flex-col gap-3 ${message.role === 'user' ? 'items-end max-w-[80%]' : 'items-start'}`}>
                      {isMealEstimate ? (
                        <div className="w-full overflow-hidden rounded-[32px] border border-[#4A453E]/5 bg-white shadow-sm">
                          <div className="border-b border-[#4A453E]/5 p-8">
                            <div className="mb-4 flex items-center justify-between">
                              <h3 className="font-serif-brand text-2xl font-bold italic text-[#4A453E]">{message.title}</h3>
                              <span className="rounded-full border border-[#81C784]/10 bg-[#81C784]/10 px-3 py-1.5 text-[10px] font-bold uppercase tracking-widest text-[#81C784]">
                                {message.confidence}
                              </span>
                            </div>
                            <p className="text-[16px] font-medium leading-relaxed text-[#4A453E]/70">{message.description}</p>
                          </div>
                          <div className="p-0">
                            <table className="w-full text-left">
                              <thead className="bg-[#F7F3E9]/30 text-[10px] font-bold uppercase tracking-widest text-[#4A453E]/40">
                                <tr>
                                  <th className="px-8 py-4">食材</th>
                                  <th className="px-8 py-4">份量</th>
                                  <th className="px-8 py-4 text-right">估算热量</th>
                                </tr>
                              </thead>
                              <tbody className="divide-y divide-[#4A453E]/5 text-[14px]">
                                {message.items?.map((item, itemIndex) => (
                                  <tr key={itemIndex} className="transition-colors hover:bg-[#F7F3E9]/10">
                                    <td className="px-8 py-4 font-bold text-[#4A453E]">{item.name}</td>
                                    <td className="px-8 py-4 font-medium text-[#4A453E]/50">{item.portion}</td>
                                    <td className="px-8 py-4 text-right font-bold text-[#4A453E]">{item.energy}</td>
                                  </tr>
                                ))}
                              </tbody>
                              <tfoot className="border-t border-[#4A453E]/10 bg-[#FFFDF5] font-bold">
                                <tr>
                                  <td className="px-8 py-6 text-lg text-[#4A453E]" colSpan={2}>估算总热量</td>
                                  <td className="px-8 py-6 text-right font-serif-brand text-3xl italic text-[#FF8A65]">{message.total}</td>
                                </tr>
                              </tfoot>
                            </table>
                          </div>
                          <div className="flex flex-col items-end gap-2 border-t border-[#4A453E]/5 bg-white px-8 py-5">
                            <div className="flex w-full flex-col gap-3 md:flex-row md:items-center md:justify-between">
                              <div className={`inline-flex items-center gap-2 self-end rounded-full border px-4 py-2 text-sm font-bold md:self-auto ${
                                saveState === 'saved'
                                  ? 'border-[#81C784]/20 bg-[#81C784]/10 text-[#4E9E63]'
                                  : saveState === 'saving'
                                    ? 'border-[#4A453E]/10 bg-[#F7F3E9] text-[#4A453E]/55'
                                    : saveState === 'failed'
                                      ? 'border-red-200 bg-red-50 text-red-500'
                                      : 'border-[#4A453E]/10 bg-[#FFFDF5] text-[#4A453E]/60'
                              }`}>
                                <span className="material-symbols-outlined text-[18px]">
                                  {savePresentation.badgeIcon}
                                </span>
                                <span>{savePresentation.badgeLabel}</span>
                              </div>

                              <div className="flex flex-wrap items-center justify-end gap-2 text-[11px] font-semibold">
                                {isSavedToFoodLog ? (
                                  <button
                                    type="button"
                                    onClick={() => message.id && void handleUndoFoodLogSave(message.id)}
                                    disabled={isDeletingSavedFoodLog}
                                    className={`rounded-full border px-3 py-1.5 transition-all ${
                                      isDeletingSavedFoodLog
                                        ? 'cursor-wait border-[#4A453E]/10 bg-[#F7F3E9] text-[#4A453E]/40'
                                        : 'border-red-200 bg-red-50 text-red-500 hover:bg-red-100'
                                    }`}
                                  >
                                    {isDeletingSavedFoodLog ? '撤销中...' : '撤销保存'}
                                  </button>
                                ) : (
                                  <button
                                    type="button"
                                    onClick={() => mealDescription && void handleSaveFoodLogEntry(activeSession.id, message, mealDescription)}
                                    disabled={!mealDescription || isSavingToFoodLog}
                                    className={`inline-flex h-11 items-center gap-2 rounded-full px-5 text-sm font-bold transition-all ${
                                      isSavingToFoodLog
                                        ? 'cursor-wait border border-[#4A453E]/10 bg-[#F7F3E9] text-[#4A453E]/50'
                                        : saveState === 'failed'
                                          ? 'border border-red-200 bg-red-50 text-red-500 hover:bg-red-100'
                                          : 'border border-[#FF8A65]/15 bg-[#FF8A65] text-white shadow-lg shadow-[#FF8A65]/15 hover:bg-[#FF8A65]/90'
                                    }`}
                                  >
                                    <span className="material-symbols-outlined text-[18px]">
                                      {savePresentation.saveActionIcon}
                                    </span>
                                    <span>{savePresentation.saveActionLabel}</span>
                                  </button>
                                )}
                              </div>
                            </div>
                            <p className="w-full text-right text-[11px] leading-5 text-[#4A453E]/40">
                              {savePresentation.helperText}
                            </p>
                          </div>
                        </div>
                      ) : isMealRecommendation ? (
                        <div className="w-full overflow-hidden rounded-[28px] border border-[#4A453E]/5 bg-white shadow-sm">
                          <div className="border-b border-[#4A453E]/5 px-8 py-6">
                            <div className="mb-3 flex items-center justify-between gap-4">
                              <div>
                                <p className="mb-2 text-[10px] font-bold uppercase tracking-[0.24em] text-[#4A453E]/35">
                                  餐食推荐
                                </p>
                                <h3 className="font-serif-brand text-2xl font-bold italic text-[#4A453E]">
                                  {message.title || '推荐建议'}
                                </h3>
                              </div>
                              <span className="rounded-full border border-[#FF8A65]/15 bg-[#FF8A65]/8 px-3 py-1.5 text-[10px] font-bold uppercase tracking-widest text-[#FF8A65]">
                                建议
                              </span>
                            </div>
                            {message.description && (
                              <div className="rounded-[20px] border border-[#4A453E]/5 bg-[#FFFDF5] px-5 py-4">
                                <p className="mb-1 text-[10px] font-bold uppercase tracking-[0.2em] text-[#4A453E]/35">
                                  为什么这样选
                                </p>
                                <p className="text-[16px] font-medium leading-relaxed text-[#4A453E]/70">
                                  {message.description}
                                </p>
                              </div>
                            )}
                          </div>
                          {message.content && (
                            <div className="px-8 py-6">
                              <p className="mb-2 text-[10px] font-bold uppercase tracking-[0.2em] text-[#4A453E]/35">
                                推荐怎么吃
                              </p>
                              <p className="text-[15px] leading-relaxed text-[#4A453E]/75">
                                {message.content}
                              </p>
                            </div>
                          )}
                        </div>
                      ) : (
                        <div className={`rounded-[24px] px-6 py-4 text-[15px] leading-relaxed shadow-sm border ${
                          message.role === 'user'
                            ? 'bg-[#F7F3E9] text-[#4A453E] border-[#4A453E]/5 rounded-tr-[4px]'
                            : 'bg-white text-[#4A453E] border-[#4A453E]/8 rounded-tl-[4px]'
                        }`}>
                          {message.content}
                        </div>
                      )}
                      <span className="px-1 text-[9px] font-bold uppercase tracking-widest text-[#4A453E]/20">{message.time || 'Just now'}</span>
                    </div>
                  </div>
                );
              })()
            ))
          )}
          {isTyping && (
            <div className="flex items-start gap-5">
              <div className="mt-1 flex size-10 shrink-0 items-center justify-center rounded-2xl border border-[#4A453E]/10 bg-white shadow-sm">
                <span className="material-symbols-outlined animate-pulse text-[22px] text-[#FF8A65]">auto_awesome</span>
              </div>
              <div className="rounded-[24px] rounded-tl-[4px] border border-[#4A453E]/5 bg-white px-8 py-5 shadow-sm">
                <div className="flex gap-1.5">
                  <span className="size-2 animate-bounce rounded-full bg-[#FF8A65] [animation-delay:-0.3s]"></span>
                  <span className="size-2 animate-bounce rounded-full bg-[#FF8A65] [animation-delay:-0.15s]"></span>
                  <span className="size-2 animate-bounce rounded-full bg-[#FF8A65]"></span>
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="z-20 bg-gradient-to-t from-[#FFFDF5] via-[#FFFDF5] to-transparent px-10 pb-10 pt-4">
          <div className="mx-auto max-w-4xl">
            <div className="relative flex items-end overflow-hidden rounded-[28px] border border-[#4A453E]/10 bg-white shadow-xl shadow-[#4A453E]/05 transition-all focus-within:border-[#FF8A65]/40">
              <textarea
                className="custom-scrollbar max-h-40 flex-1 resize-none border-none bg-transparent py-6 pl-8 text-[16px] leading-relaxed text-[#4A453E] placeholder-[#4A453E]/30 focus:ring-0"
                placeholder="描述你吃了什么，或问这餐大概多少热量 / 营养..."
                rows={1}
                value={inputValue}
                onChange={(event) => setInputValue(event.target.value)}
                onKeyDown={handleKeyDown}
              ></textarea>

              <div className="p-3">
                <button
                  onClick={() => void handleSendMessage()}
                  disabled={!inputValue.trim() || isTyping}
                  className={`flex size-12 items-center justify-center rounded-[20px] transition-all active:scale-95 ${
                    !inputValue.trim() || isTyping
                      ? 'cursor-not-allowed bg-[#4A453E]/05 text-[#4A453E]/20'
                      : 'bg-[#FF8A65] text-white shadow-lg shadow-[#FF8A65]/20 hover:bg-[#FF8A65]/90'
                  }`}
                >
                  <span className="material-symbols-outlined text-[24px]">arrow_upward</span>
                </button>
              </div>
            </div>

            <p className="mt-4 text-center text-[10px] font-bold uppercase tracking-[0.2em] text-[#4A453E]/30">
              Your conversational nutrition assistant.
            </p>
          </div>
        </div>
      </section>

      {isRenameModalOpen && (
        <div
          className="fixed inset-0 z-[100] flex items-center justify-center bg-black/30 px-6"
          onClick={() => setIsRenameModalOpen(false)}
        >
          <div
            className="w-full max-w-sm rounded-[24px] border border-[#4A453E]/10 bg-[#FFFDF5] p-6 shadow-[0_28px_70px_rgba(74,69,62,0.18)]"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="mb-5">
              <h3 className="text-lg font-bold text-[#4A453E]">Rename Chat</h3>
              <p className="mt-1 text-sm text-[#4A453E]/50">
                Update the conversation title shown in your chats.
              </p>
            </div>
            <input
              type="text"
              value={renamingTitle}
              onChange={(event) => setRenamingTitle(event.target.value)}
              autoFocus
              className="mb-6 w-full rounded-[16px] border border-[#4A453E]/10 bg-white px-4 py-3 text-sm font-medium text-[#4A453E] outline-none transition-all focus:border-[#FF8A65]/40 focus:ring-2 focus:ring-[#FF8A65]/15"
              onKeyDown={(event) => event.key === 'Enter' && void handleRenameSession()}
            />
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setIsRenameModalOpen(false)}
                className="rounded-[14px] border border-[#4A453E]/10 bg-white px-4 py-2.5 text-sm font-semibold text-[#4A453E]/55 transition-colors hover:bg-[#F7F3E9]"
              >
                Cancel
              </button>
              <button
                onClick={() => void handleRenameSession()}
                className="rounded-[14px] bg-[#FF8A65] px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-[#FF8A65]/20 transition-colors hover:bg-[#FF8A65]/90"
              >
                Save
              </button>
            </div>
          </div>
        </div>
      )}

      <ConfirmDialog
        open={Boolean(deleteSessionTarget)}
        title="Delete Chat Permanently?"
        description={(
          <>
            This chat cannot be recovered after deletion. Saved Food Log entries will remain,
            but they will no longer be able to open{' '}
            <span className="font-bold text-[#4A453E]">
              {deleteSessionTarget?.title ?? 'this chat'}
            </span>
            .
          </>
        )}
        confirmLabel={isDeletingSession ? 'Deleting...' : 'Delete Permanently'}
        icon="delete"
        isConfirming={isDeletingSession}
        onClose={closeDeleteSessionDialog}
        onConfirm={() => void handleDeleteSession()}
      />
    </div>
  );
};

function handleChatError(error: unknown, fallbackMessage: string): void {
  console.error('Chat Error:', error);
  const message = error instanceof ChatApiError
    ? error.message
    : error instanceof Error
      ? error.message
      : fallbackMessage;
  window.alert(message || fallbackMessage);
}

function handleFoodLogError(error: unknown, fallbackMessage: string): void {
  console.error('Food Log Error:', error);
  const message = resolveFoodLogErrorMessage(error, fallbackMessage);
  window.alert(message || fallbackMessage);
}

function resolveFoodLogErrorMessage(error: unknown, fallbackMessage: string): string {
  return error instanceof FoodLogApiError
    ? error.message
    : error instanceof Error
      ? error.message
      : fallbackMessage;
}

function buildOptimisticUserMessage(id: string, content: string): Message {
  return {
    id,
    role: 'user',
    messageType: 'text',
    content,
    payload: { text: content },
    time: formatOptimisticTime(),
    isResult: false,
  };
}

function applyOptimisticUserMessage(
  sessions: ChatSession[],
  optimisticMessage: Message,
  content: string,
  activeSessionId: string,
  optimisticSessionId: string | null,
): ChatSession[] {
  if (optimisticSessionId) {
    return mergeSessionIntoList(sessions, {
      id: optimisticSessionId,
      title: buildOptimisticSessionTitle(content),
      messages: [optimisticMessage],
      timestamp: new Date(),
      icon: 'chat_bubble',
      hasLoadedMessages: true,
    });
  }

  return sessions.map((session) => {
    if (session.id !== activeSessionId) {
      return session;
    }

    const shouldRenameEmptySession = session.messages.length === 0;
    return {
      ...session,
      title: shouldRenameEmptySession ? buildOptimisticSessionTitle(content) : session.title,
      timestamp: new Date(),
      hasLoadedMessages: true,
      messages: [...session.messages, optimisticMessage],
    };
  });
}

function applyResolvedExchange(
  sessions: ChatSession[],
  exchange: {
    session: ChatSession;
    userMessage: Message;
    assistantMessage: Message;
  },
  optimisticMessageId: string,
  optimisticSessionId: string | null,
): ChatSession[] {
  const baseSessions = sessions.filter((session) => (
    session.id !== exchange.session.id
    && session.id !== optimisticSessionId
  ));

  const existingSession = sessions.find((session) => session.id === exchange.session.id);
  const existingMessages = existingSession?.messages ?? [];
  const nextMessages = optimisticSessionId
    ? [exchange.userMessage, exchange.assistantMessage]
    : [
      ...existingMessages.filter((message) => message.id !== optimisticMessageId),
      exchange.userMessage,
      exchange.assistantMessage,
    ];

  return mergeSessionIntoList(baseSessions, {
    ...exchange.session,
    messages: nextMessages,
    hasLoadedMessages: true,
  });
}

function rollbackOptimisticUserMessage(
  sessions: ChatSession[],
  optimisticMessageId: string,
  optimisticSessionId: string | null,
  activeSessionId: string,
  originalSession: ChatSession | null,
): ChatSession[] {
  if (optimisticSessionId) {
    return sessions.filter((session) => session.id !== optimisticSessionId);
  }

  return sessions.map((session) => {
    if (session.id !== activeSessionId) {
      return session;
    }

    return {
      ...(originalSession ?? session),
      messages: session.messages.filter((message) => message.id !== optimisticMessageId),
    };
  });
}

function buildOptimisticSessionTitle(content: string): string {
  const normalized = content.trim().replace(/\s+/g, ' ');
  return normalized.length > 120 ? `${normalized.slice(0, 117)}...` : normalized;
}

function formatOptimisticTime(): string {
  return new Date().toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
  });
}

function getMessageType(message: Message): ChatMessageType {
  return message.messageType ?? 'text';
}

function isMealEstimateMessage(message: Message): boolean {
  return getMessageType(message) === 'meal_estimate';
}

function resolveMealDescription(
  messages: Message[],
  resultIndex: number,
  resultMessage: Message,
): string | null {
  for (let index = resultIndex - 1; index >= 0; index -= 1) {
    const candidate = messages[index];
    if (candidate.role === 'user' && candidate.content?.trim()) {
      return candidate.content.trim();
    }
  }

  if (resultMessage.title?.trim()) {
    return resultMessage.title.trim();
  }

  return null;
}

function getSessionStatusLabel(
  session: ChatSession,
  isLoading: boolean,
): string {
  if (isLoading) {
    return 'Loading...';
  }

  if (session.messages.length > 0) {
    return 'Started';
  }

  return 'Empty';
}
