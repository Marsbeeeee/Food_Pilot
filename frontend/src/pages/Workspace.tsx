import React, { useEffect, useRef, useState } from 'react';

import {
  applyChatExchange,
  ChatApiError,
  createChatMessage,
  createChatSession,
  deleteChatSession,
  getChatSession,
  mergeSessionIntoList,
  renameChatSession,
  sendChatMessage,
} from '../api/chat';
import { ChatSession } from '../types/types';

interface WorkspaceProps {
  sessions: ChatSession[];
  setSessions: React.Dispatch<React.SetStateAction<ChatSession[]>>;
  activeSessionId: string;
  setActiveSessionId: (id: string) => void;
  profileId?: number;
}

export const Workspace: React.FC<WorkspaceProps> = ({
  sessions,
  setSessions,
  activeSessionId,
  setActiveSessionId,
  profileId,
}) => {
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isRenameModalOpen, setIsRenameModalOpen] = useState(false);
  const [renamingTitle, setRenamingTitle] = useState('');
  const [isCreatingSession, setIsCreatingSession] = useState(false);
  const [isLoadingSessionId, setIsLoadingSessionId] = useState<string | null>(null);

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

    setIsTyping(true);
    setInputValue('');

    try {
      if (!activeSessionId || sessions.length === 0) {
        const exchange = await createChatMessage(finalQuery, profileId);
        setSessions((prev) => applyChatExchange(prev, exchange));
        setActiveSessionId(exchange.session.id);
        return;
      }

      const active = sessions.find((session) => session.id === activeSessionId);
      if (active && !active.hasLoadedMessages) {
        await loadSessionDetail(active.id);
      }

      const exchange = await sendChatMessage(activeSessionId, finalQuery, profileId);
      setSessions((prev) => applyChatExchange(prev, exchange));
      setActiveSessionId(exchange.session.id);
    } catch (error) {
      setInputValue(finalQuery);
      handleChatError(error, 'Unable to send this message right now.');
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

  const handleDeleteSession = async (sessionId: string) => {
    try {
      await deleteChatSession(sessionId);
      const remainingSessions = sessions.filter((session) => session.id !== sessionId);
      setSessions(remainingSessions);
      if (remainingSessions.length === 0) {
        setActiveSessionId('');
      } else if (sessionId === activeSessionId) {
        setActiveSessionId(remainingSessions[0].id);
      }
      setIsMenuOpen(false);
    } catch (error) {
      handleChatError(error, 'Unable to delete this chat right now.');
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
          ? {
              ...session,
              title: renamedSession.title,
              timestamp: renamedSession.timestamp,
            }
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
            <span>寮€鍚柊瀵硅瘽</span>
          </button>

          <div className="custom-scrollbar flex min-h-0 flex-1 flex-col gap-6 overflow-y-auto pr-2 pb-10">
            <div>
              <h3 className="px-3 text-[10px] font-bold uppercase tracking-[0.2em] text-[#4A453E]/30 mb-4">鍘嗗彶璁板綍</h3>
              <div className="flex flex-col gap-1">
                {sessions.map((session) => {
                  const lastResult = [...session.messages].reverse().find((message) => message.isResult);
                  return (
                    <div
                      key={session.id}
                      onClick={() => void handleSelectSession(session.id)}
                      className={`group flex items-start gap-4 p-4 rounded-[16px] cursor-pointer transition-all border ${
                        activeSessionId === session.id
                          ? 'bg-[#F7F3E9] border-[#4A453E]/10'
                          : 'bg-transparent border-transparent hover:bg-[#F7F3E9]/60'
                      }`}
                    >
                      <div className={`mt-1.5 rounded-full size-2 shrink-0 ${activeSessionId === session.id ? 'bg-[#FF8A65]' : 'bg-[#4A453E]/10'}`}></div>
                      <div className="flex-1 min-w-0">
                        <p className={`text-[13px] truncate mb-1 ${activeSessionId === session.id ? 'font-bold text-[#4A453E]' : 'font-medium text-[#4A453E]/60 group-hover:text-[#4A453E]/80'}`}>
                          {session.title}
                        </p>
                        <div className="flex justify-between items-center">
                          <span className="text-[10px] text-[#4A453E]/30 font-bold uppercase tracking-wider">
                            {isLoadingSessionId === session.id
                              ? '鍔犺浇涓?...'
                              : session.messages.length > 0
                                ? '宸茶褰?'
                                : '绌?'}
                          </span>
                          {lastResult?.total && (
                            <span className="text-[10px] bg-white/60 text-[#4A453E]/50 px-1.5 py-0.5 rounded border border-[#4A453E]/05 font-bold">
                              {lastResult.total}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
                {sessions.length === 0 && (
                  <p className="px-3 text-[11px] text-[#4A453E]/30 italic">鏆傛棤鍘嗗彶璁板綍銆?/p>
                )}
              </div>
            </div>
          </div>
        </div>
      </aside>

      <section className="relative flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden bg-[#FFFDF5]">
        {activeSession && (
          <div className="flex items-center justify-between px-10 py-4 border-b border-[#4A453E]/5 bg-white/40 backdrop-blur-sm z-10">
            <div className="flex items-center gap-3">
              <span className="text-[#4A453E]/20 material-symbols-outlined text-[20px]">auto_awesome</span>
              <span className="text-[#4A453E] text-[13px] font-bold font-serif-brand italic tracking-wide">
                {activeSession.title}
              </span>
            </div>
            <div className="relative flex items-center gap-2" ref={menuRef}>
              <button
                onClick={() => setIsMenuOpen(!isMenuOpen)}
                className={`p-1 transition-colors rounded-full ${isMenuOpen ? 'text-[#FF8A65] bg-[#FF8A65]/10' : 'text-[#4A453E]/30 hover:text-[#FF8A65] hover:bg-[#FF8A65]/5'}`}
              >
                <span className="material-symbols-outlined text-[20px]">more_vert</span>
              </button>

              {isMenuOpen && (
                <div className="absolute right-0 top-full mt-2 w-48 bg-white rounded-[20px] shadow-xl border border-[#4A453E]/10 py-2 z-50 overflow-hidden animate-in fade-in slide-in-from-top-2 duration-200">
                  <button
                    onClick={openRenameModal}
                    className="w-full flex items-center gap-3 px-4 py-3 text-sm font-bold text-[#4A453E]/70 hover:bg-[#F7F3E9] hover:text-[#4A453E] transition-colors"
                  >
                    <span className="material-symbols-outlined text-[18px]">edit</span>
                    閲嶅懡鍚?
                  </button>
                  <div className="h-[1px] bg-[#4A453E]/5 mx-2 my-1"></div>
                  <button
                    onClick={() => void handleDeleteSession(activeSessionId)}
                    className="w-full flex items-center gap-3 px-4 py-3 text-sm font-bold text-red-400 hover:bg-red-50 transition-colors"
                  >
                    <span className="material-symbols-outlined text-[18px]">delete</span>
                    鍒犻櫎
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
            <div className="flex-1 flex flex-col items-center justify-center text-center py-20">
              <div className="size-20 bg-white rounded-[40px] shadow-sm flex items-center justify-center mb-8 border border-[#4A453E]/05">
                <span className="material-symbols-outlined text-4xl text-[#FF8A65]">restaurant</span>
              </div>
              <h3 className="text-3xl font-serif-brand font-bold text-[#4A453E] mb-3 italic">浣犵洏瀛愰噷瑁呬簡浠€涔堬紵</h3>
              <p className="max-w-md text-[#4A453E]/50 text-base leading-relaxed">
                鎻忚堪浣犵殑楗锛屾垜灏嗕负浣犲垎鏋愯惀鍏绘垚鍒嗗苟浼扮畻鐑噺銆?
              </p>
              <div className="mt-10 grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-lg">
                <button onClick={() => void handleSendMessage('缁忓吀鐨勭墰娌规灉鍚愬徃鍖呭惈鍝簺钀ュ吇锛?')} className="p-4 bg-white rounded-[20px] border border-[#4A453E]/05 text-left hover:border-[#FF8A65]/30 hover:bg-[#F7F3E9]/20 transition-all group">
                  <p className="text-[13px] font-bold text-[#4A453E] mb-1">鏍囧噯鏌ヨ</p>
                  <p className="text-xs text-[#4A453E]/40 group-hover:text-[#4A453E]/60">"缁忓吀鐨勭墰娌规灉鍚愬徃鍖呭惈鍝簺钀ュ吇锛?"</p>
                </button>
                <button onClick={() => void handleSendMessage('涓€浠芥尝濂囬キ澶х害鏈夊灏戠儹閲忥紵')} className="p-4 bg-white rounded-[20px] border border-[#4A453E]/05 text-left hover:border-[#FF8A65]/30 hover:bg-[#F7F3E9]/20 transition-all group">
                  <p className="text-[13px] font-bold text-[#4A453E] mb-1">椁愰浼扮畻</p>
                  <p className="text-xs text-[#4A453E]/40 group-hover:text-[#4A453E]/60">"涓€浠芥尝濂囬キ澶х害鏈夊灏戠儹閲忥紵"</p>
                </button>
              </div>
            </div>
          ) : (
            activeSession.messages.map((message, index) => (
              <div key={message.id ?? index} className={`flex items-start gap-5 ${message.role === 'user' ? 'justify-end' : ''}`}>
                {message.role === 'assistant' && (
                  <div className="bg-white border border-[#4A453E]/10 flex items-center justify-center rounded-2xl size-10 shrink-0 shadow-sm mt-1">
                    <span className="material-symbols-outlined text-[#FF8A65] text-[22px]">auto_awesome</span>
                  </div>
                )}

                <div className={`flex flex-col gap-3 ${message.role === 'user' ? 'items-end max-w-[80%]' : 'items-start max-w-[95%]'}`}>
                  {message.isResult ? (
                    <div className="bg-white rounded-[32px] shadow-sm border border-[#4A453E]/05 w-full overflow-hidden">
                      <div className="p-8 border-b border-[#4A453E]/5">
                        <div className="flex items-center justify-between mb-4">
                          <h3 className="text-2xl text-[#4A453E] font-serif-brand font-bold italic">{message.title}</h3>
                          <span className="bg-[#81C784]/10 text-[#81C784] text-[10px] font-bold px-3 py-1.5 rounded-full uppercase border border-[#81C784]/10 tracking-widest">
                            {message.confidence}
                          </span>
                        </div>
                        <p className="text-[16px] text-[#4A453E]/70 leading-relaxed font-medium">{message.description}</p>
                      </div>
                      <div className="p-0">
                        <table className="w-full text-left">
                          <thead className="bg-[#F7F3E9]/30 text-[#4A453E]/40 text-[10px] font-bold uppercase tracking-widest">
                            <tr>
                              <th className="px-8 py-4">椋熸潗</th>
                              <th className="px-8 py-4">浠介噺</th>
                              <th className="px-8 py-4 text-right">浼扮畻鐑噺</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-[#4A453E]/5 text-[14px]">
                            {message.items?.map((item, itemIndex) => (
                              <tr key={itemIndex} className="hover:bg-[#F7F3E9]/10 transition-colors">
                                <td className="px-8 py-4 font-bold text-[#4A453E]">{item.name}</td>
                                <td className="px-8 py-4 text-[#4A453E]/50 font-medium">{item.portion}</td>
                                <td className="px-8 py-4 text-right font-bold text-[#4A453E]">{item.energy}</td>
                              </tr>
                            ))}
                          </tbody>
                          <tfoot className="bg-[#FFFDF5] font-bold border-t border-[#4A453E]/10">
                            <tr>
                              <td className="px-8 py-6 text-[#4A453E] text-lg" colSpan={2}>棰勪及鎬婚噺</td>
                              <td className="px-8 py-6 text-right text-[#FF8A65] text-3xl font-serif-brand italic">{message.total}</td>
                            </tr>
                          </tfoot>
                        </table>
                      </div>
                    </div>
                  ) : (
                    <div className={`text-[15px] leading-relaxed rounded-[24px] px-6 py-4 shadow-sm border ${
                      message.role === 'user'
                        ? 'bg-[#F7F3E9] text-[#4A453E] border-[#4A453E]/5 rounded-tr-[4px]'
                        : 'bg-white text-[#4A453E] border-[#4A453E]/08 rounded-tl-[4px]'
                    }`}>
                      {message.content}
                    </div>
                  )}
                  <span className="text-[#4A453E]/20 text-[9px] font-bold uppercase tracking-widest px-1">{message.time || '鍒氬垰'}</span>
                </div>
              </div>
            ))
          )}
          {isTyping && (
            <div className="flex items-start gap-5">
              <div className="bg-white border border-[#4A453E]/10 flex items-center justify-center rounded-2xl size-10 shrink-0 shadow-sm mt-1">
                <span className="material-symbols-outlined text-[#FF8A65] text-[22px] animate-pulse">auto_awesome</span>
              </div>
              <div className="bg-white rounded-[24px] rounded-tl-[4px] px-8 py-5 shadow-sm border border-[#4A453E]/05">
                <div className="flex gap-1.5">
                  <span className="size-2 bg-[#FF8A65] rounded-full animate-bounce [animation-delay:-0.3s]"></span>
                  <span className="size-2 bg-[#FF8A65] rounded-full animate-bounce [animation-delay:-0.15s]"></span>
                  <span className="size-2 bg-[#FF8A65] rounded-full animate-bounce"></span>
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="shrink-0 bg-gradient-to-t from-[#FFFDF5] via-[#FFFDF5] to-transparent px-10 pb-10 pt-4 z-20">
          <div className="max-w-4xl mx-auto">
            <div className="relative flex items-end bg-white rounded-[28px] border border-[#4A453E]/10 focus-within:border-[#FF8A65]/40 transition-all shadow-xl shadow-[#4A453E]/05 overflow-hidden">
              <textarea
                className="flex-1 bg-transparent border-none focus:ring-0 text-[16px] py-6 pl-8 text-[#4A453E] placeholder-[#4A453E]/30 resize-none max-h-40 custom-scrollbar leading-relaxed"
                placeholder="鍜?Food Pilot 鑱婅亰... (渚嬪锛氭垜鐨勫鍙搁噷鏈変粈涔堬紵)"
                rows={1}
                value={inputValue}
                onChange={(event) => setInputValue(event.target.value)}
                onKeyDown={handleKeyDown}
              ></textarea>
              <div className="p-3">
                <button
                  onClick={() => void handleSendMessage()}
                  disabled={!inputValue.trim() || isTyping}
                  className={`size-12 rounded-[20px] flex items-center justify-center transition-all active:scale-95 ${
                    !inputValue.trim() || isTyping
                      ? 'bg-[#4A453E]/05 text-[#4A453E]/20 cursor-not-allowed'
                      : 'bg-[#FF8A65] text-white hover:bg-[#FF8A65]/90 shadow-lg shadow-[#FF8A65]/20'
                  }`}
                >
                  <span className="material-symbols-outlined text-[24px]">arrow_upward</span>
                </button>
              </div>
            </div>
            <p className="text-center text-[10px] text-[#4A453E]/30 mt-4 font-bold uppercase tracking-[0.2em]">
              浣犵殑鍧囪　楗鍔╂墜銆?
            </p>
          </div>
        </div>
      </section>

      {isRenameModalOpen && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/20 backdrop-blur-sm px-6">
          <div className="bg-white rounded-[32px] p-8 w-full max-w-md shadow-2xl border border-[#4A453E]/10 animate-in fade-in zoom-in duration-200">
            <h3 className="text-2xl font-serif-brand font-bold text-[#4A453E] mb-6 italic">閲嶅懡鍚嶅璇?/h3>
            <input
              type="text"
              value={renamingTitle}
              onChange={(event) => setRenamingTitle(event.target.value)}
              autoFocus
              className="w-full bg-[#F7F3E9]/40 border border-[#4A453E]/10 rounded-[18px] px-6 py-4 font-bold text-[#4A453E] focus:ring-2 focus:ring-[#FF8A65]/20 focus:bg-white outline-none transition-all mb-8"
              onKeyDown={(event) => event.key === 'Enter' && void handleRenameSession()}
            />
            <div className="flex gap-3">
              <button onClick={() => setIsRenameModalOpen(false)} className="flex-1 py-3 bg-white text-[#4A453E]/40 font-bold text-sm rounded-full border border-[#4A453E]/10 hover:bg-[#F7F3E9] transition-all">鍙栨秷</button>
              <button onClick={() => void handleRenameSession()} className="flex-1 py-3 bg-[#FF8A65] text-white font-bold text-sm rounded-full shadow-lg shadow-[#FF8A65]/20 hover:translate-y-[-1px] transition-all">淇濆瓨</button>
            </div>
          </div>
        </div>
      )}
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
