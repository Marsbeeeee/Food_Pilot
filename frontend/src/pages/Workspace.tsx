
import React, { useState, useEffect, useRef } from 'react';
import { ChatSession, Message, IngredientResult } from '../types/types';
import { GoogleGenAI, Type } from "@google/genai";

interface WorkspaceProps {
  sessions: ChatSession[];
  setSessions: React.Dispatch<React.SetStateAction<ChatSession[]>>;
  activeSessionId: string;
  setActiveSessionId: (id: string) => void;
}

export const Workspace: React.FC<WorkspaceProps> = ({ sessions, setSessions, activeSessionId, setActiveSessionId }) => {
  const [activeSessionIdState, setActiveSessionIdState] = useState<string>(activeSessionId);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isRenameModalOpen, setIsRenameModalOpen] = useState(false);
  const [renamingTitle, setRenamingTitle] = useState('');
  
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (sessions.length > 0 && !activeSessionId) {
      setActiveSessionId(sessions[0].id);
    } else if (sessions.length === 0) {
      setActiveSessionId('');
    }
  }, [sessions]);

  const activeSession = sessions.find(s => s.id === activeSessionId) || (sessions.length > 0 ? sessions[0] : null);

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
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleNewAnalysis = () => {
    const newId = Math.floor(1000 + Math.random() * 9000).toString();
    const newSession: ChatSession = {
      id: newId,
      title: '新对话',
      icon: 'chat_bubble',
      timestamp: new Date(),
      messages: []
    };
    setSessions([newSession, ...sessions]);
    setActiveSessionId(newId);
  };

  const performAnalysis = async (query: string, sessionId: string) => {
    setIsTyping(true);
    try {
      const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
      const response = await ai.models.generateContent({
        model: "gemini-3-flash-preview",
        contents: query,
        config: {
          systemInstruction: "你叫 Food Pilot，是一个友好且专业的营养指导助手。你的目标是提供清晰、鼓励性的热量估算。请务必细分食材，并提供针对健康或替代选择的后续建议。所有回复必须使用中文。",
          responseMimeType: "application/json",
          responseSchema: {
            type: Type.OBJECT,
            properties: {
              title: { type: Type.STRING },
              description: { type: Type.STRING },
              confidence: { type: Type.STRING, description: "例如：高准确度" },
              items: {
                type: Type.ARRAY,
                items: {
                  type: Type.OBJECT,
                  properties: {
                    name: { type: Type.STRING },
                    portion: { type: Type.STRING },
                    energy: { type: Type.STRING }
                  },
                  required: ["name", "portion", "energy"]
                }
              },
              totalCalories: { type: Type.STRING },
              suggestion: { type: Type.STRING, description: "友好的后续建议或问题" }
            },
            required: ["title", "description", "confidence", "items", "totalCalories", "suggestion"]
          }
        }
      });

      const data = JSON.parse(response.text || "{}");
      
      const assistantMessage: Message = {
        role: 'assistant',
        isResult: true,
        title: data.title,
        confidence: data.confidence,
        description: data.description,
        items: data.items,
        total: data.totalCalories,
        content: data.suggestion,
        time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
      };

      setSessions(prev => prev.map(s => 
        s.id === sessionId ? { ...s, messages: [...s.messages, assistantMessage] } : s
      ));
    } catch (error) {
      console.error("Analysis Error:", error);
      const errorMessage: Message = {
        role: 'assistant',
        content: "抱歉，我现在无法处理该请求。能请你再次描述一下这顿餐食吗？",
        time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
      };
      setSessions(prev => prev.map(s => 
        s.id === sessionId ? { ...s, messages: [...s.messages, errorMessage] } : s
      ));
    } finally {
      setIsTyping(false);
    }
  };

  const handleSendMessage = (text?: string) => {
    const finalQuery = text || inputValue.trim();
    if (!finalQuery || isTyping) return;

    const newMessage: Message = {
      role: 'user',
      content: finalQuery,
      time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
    };

    if (sessions.length === 0 || !activeSessionId) {
       const newId = Math.floor(1000 + Math.random() * 9000).toString();
       const newSession: ChatSession = {
         id: newId,
         title: finalQuery.length > 20 ? finalQuery.substring(0, 20) + '...' : finalQuery,
         icon: 'chat_bubble',
         timestamp: new Date(),
         messages: [newMessage]
       };
       setSessions([newSession]);
       setActiveSessionId(newId);
       setInputValue('');
       performAnalysis(finalQuery, newId);
       return;
    }

    setSessions(prev => prev.map(s => {
      if (s.id === activeSessionId) {
        const isFirstMessage = s.messages.length === 0;
        return {
          ...s,
          title: isFirstMessage ? (finalQuery.length > 20 ? finalQuery.substring(0, 20) + '...' : finalQuery) : s.title,
          messages: [...s.messages, newMessage]
        };
      }
      return s;
    }));

    setInputValue('');
    performAnalysis(finalQuery, activeSessionId);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleDeleteSession = (id: string) => {
    const remainingSessions = sessions.filter(s => s.id !== id);
    if (remainingSessions.length === 0) {
      setSessions([]);
      setActiveSessionId('');
    } else {
      if (id === activeSessionId) {
        setActiveSessionId(remainingSessions[0].id);
      }
      setSessions(remainingSessions);
    }
    setIsMenuOpen(false);
  };

  const handleRenameSession = () => {
    if (!renamingTitle.trim()) return;
    setSessions(prev => prev.map(s => s.id === activeSessionId ? { ...s, title: renamingTitle.trim() } : s));
    setIsRenameModalOpen(false);
    setIsMenuOpen(false);
  };

  const openRenameModal = () => {
    if (!activeSession) return;
    setRenamingTitle(activeSession.title);
    setIsRenameModalOpen(true);
    setIsMenuOpen(false);
  };

  return (
    <div className="flex flex-1 overflow-hidden h-full relative">
      <aside className="w-72 flex flex-col border-r border-[#4A453E]/5 bg-[#FFFDF5] shrink-0">
        <div className="p-6 flex flex-col gap-6 h-full">
          <button 
            onClick={handleNewAnalysis}
            className="bg-[#FF8A65] text-white rounded-[20px] flex w-full items-center justify-center gap-2 h-12 px-4 text-sm font-bold shadow-lg shadow-[#FF8A65]/10 hover:shadow-xl hover:translate-y-[-1px] transition-all active:scale-95 active:translate-y-0"
          >
            <span className="material-symbols-outlined text-[20px]">add_circle</span>
            <span>开启新对话</span>
          </button>
          
          <div className="flex flex-col gap-6 overflow-y-auto custom-scrollbar pr-2 pb-10">
            <div>
              <h3 className="px-3 text-[10px] font-bold uppercase tracking-[0.2em] text-[#4A453E]/30 mb-4">历史记录</h3>
              <div className="flex flex-col gap-1">
                {sessions.map(session => {
                  const lastResult = [...session.messages].reverse().find(m => m.isResult);
                  return (
                    <div 
                      key={session.id}
                      onClick={() => setActiveSessionId(session.id)}
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
                          <span className="text-[10px] text-[#4A453E]/30 font-bold uppercase tracking-wider">{session.messages.length > 0 ? '已记录' : '空'}</span>
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
                  <p className="px-3 text-[11px] text-[#4A453E]/30 italic">暂无历史记录。</p>
                )}
              </div>
            </div>
          </div>
        </div>
      </aside>

      <section className="flex-1 flex flex-col bg-[#FFFDF5] relative min-w-[500px]">
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
                    重命名
                  </button>
                  <div className="h-[1px] bg-[#4A453E]/5 mx-2 my-1"></div>
                  <button 
                    onClick={() => handleDeleteSession(activeSessionId)}
                    className="w-full flex items-center gap-3 px-4 py-3 text-sm font-bold text-red-400 hover:bg-red-50 transition-colors"
                  >
                    <span className="material-symbols-outlined text-[18px]">delete</span>
                    删除
                  </button>
                </div>
              )}
            </div>
          </div>
        )}

        <div 
          ref={chatContainerRef}
          className="flex-1 overflow-y-auto px-6 py-10 md:px-16 flex flex-col gap-10 custom-scrollbar scroll-smooth"
        >
          {(!activeSession || activeSession.messages.length === 0) ? (
            <div className="flex-1 flex flex-col items-center justify-center text-center py-20">
              <div className="size-20 bg-white rounded-[40px] shadow-sm flex items-center justify-center mb-8 border border-[#4A453E]/05">
                <span className="material-symbols-outlined text-4xl text-[#FF8A65]">restaurant</span>
              </div>
              <h3 className="text-3xl font-serif-brand font-bold text-[#4A453E] mb-3 italic">你盘子里装了什么？</h3>
              <p className="max-w-md text-[#4A453E]/50 text-base leading-relaxed">
                描述你的饮食，我将为你分析营养成分并估算热量。
              </p>
              <div className="mt-10 grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-lg">
                <button onClick={() => handleSendMessage("经典的牛油果吐司包含哪些营养？")} className="p-4 bg-white rounded-[20px] border border-[#4A453E]/05 text-left hover:border-[#FF8A65]/30 hover:bg-[#F7F3E9]/20 transition-all group">
                  <p className="text-[13px] font-bold text-[#4A453E] mb-1">标准查询</p>
                  <p className="text-xs text-[#4A453E]/40 group-hover:text-[#4A453E]/60">"经典的牛油果吐司包含哪些营养？"</p>
                </button>
                <button onClick={() => handleSendMessage("一份波奇饭大约有多少热量？")} className="p-4 bg-white rounded-[20px] border border-[#4A453E]/05 text-left hover:border-[#FF8A65]/30 hover:bg-[#F7F3E9]/20 transition-all group">
                  <p className="text-[13px] font-bold text-[#4A453E] mb-1">餐食估算</p>
                  <p className="text-xs text-[#4A453E]/40 group-hover:text-[#4A453E]/60">"一份波奇饭大约有多少热量？"</p>
                </button>
              </div>
            </div>
          ) : (
            activeSession.messages.map((msg, i) => (
              <div key={i} className={`flex items-start gap-5 ${msg.role === 'user' ? 'justify-end' : ''}`}>
                {msg.role === 'assistant' && (
                  <div className="bg-white border border-[#4A453E]/10 flex items-center justify-center rounded-2xl size-10 shrink-0 shadow-sm mt-1">
                    <span className="material-symbols-outlined text-[#FF8A65] text-[22px]">auto_awesome</span>
                  </div>
                )}
                
                <div className={`flex flex-col gap-3 ${msg.role === 'user' ? 'items-end max-w-[80%]' : 'items-start max-w-[95%]'}`}>
                  {msg.isResult ? (
                    <div className="bg-white rounded-[32px] shadow-sm border border-[#4A453E]/05 w-full overflow-hidden">
                      <div className="p-8 border-b border-[#4A453E]/5">
                        <div className="flex items-center justify-between mb-4">
                          <h3 className="text-2xl text-[#4A453E] font-serif-brand font-bold italic">{msg.title}</h3>
                          <span className="bg-[#81C784]/10 text-[#81C784] text-[10px] font-bold px-3 py-1.5 rounded-full uppercase border border-[#81C784]/10 tracking-widest">
                            {msg.confidence}
                          </span>
                        </div>
                        <p className="text-[16px] text-[#4A453E]/70 leading-relaxed font-medium">{msg.description}</p>
                      </div>
                      <div className="p-0">
                        <table className="w-full text-left">
                          <thead className="bg-[#F7F3E9]/30 text-[#4A453E]/40 text-[10px] font-bold uppercase tracking-widest">
                            <tr>
                              <th className="px-8 py-4">食材</th>
                              <th className="px-8 py-4">份量</th>
                              <th className="px-8 py-4 text-right">估算热量</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-[#4A453E]/5 text-[14px]">
                            {msg.items?.map((item, idx) => (
                              <tr key={idx} className="hover:bg-[#F7F3E9]/10 transition-colors">
                                <td className="px-8 py-4 font-bold text-[#4A453E]">{item.name}</td>
                                <td className="px-8 py-4 text-[#4A453E]/50 font-medium">{item.portion}</td>
                                <td className="px-8 py-4 text-right font-bold text-[#4A453E]">{item.energy}</td>
                              </tr>
                            ))}
                          </tbody>
                          <tfoot className="bg-[#FFFDF5] font-bold border-t border-[#4A453E]/10">
                            <tr>
                              <td className="px-8 py-6 text-[#4A453E] text-lg" colSpan={2}>预估总量</td>
                              <td className="px-8 py-6 text-right text-[#FF8A65] text-3xl font-serif-brand italic">{msg.total}</td>
                            </tr>
                          </tfoot>
                        </table>
                      </div>
                    </div>
                  ) : (
                    <div className={`text-[15px] leading-relaxed rounded-[24px] px-6 py-4 shadow-sm border ${
                      msg.role === 'user' 
                        ? 'bg-[#F7F3E9] text-[#4A453E] border-[#4A453E]/5 rounded-tr-[4px]' 
                        : 'bg-white text-[#4A453E] border-[#4A453E]/08 rounded-tl-[4px]'
                    }`}>
                      {msg.content}
                    </div>
                  )}
                  <span className="text-[#4A453E]/20 text-[9px] font-bold uppercase tracking-widest px-1">{msg.time || '刚刚'}</span>
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

        <div className="px-10 pb-10 pt-4 bg-gradient-to-t from-[#FFFDF5] via-[#FFFDF5] to-transparent z-20">
          <div className="max-w-4xl mx-auto">
            <div className="relative flex items-end bg-white rounded-[28px] border border-[#4A453E]/10 focus-within:border-[#FF8A65]/40 transition-all shadow-xl shadow-[#4A453E]/05 overflow-hidden">
              <textarea 
                className="flex-1 bg-transparent border-none focus:ring-0 text-[16px] py-6 pl-8 text-[#4A453E] placeholder-[#4A453E]/30 resize-none max-h-40 custom-scrollbar leading-relaxed" 
                placeholder="和 Food Pilot 聊聊... (例如：我的寿司里有什么？)" 
                rows={1}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={handleKeyDown}
              ></textarea>
              <div className="p-3">
                <button 
                  onClick={() => handleSendMessage()}
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
              你的均衡饮食助手。
            </p>
          </div>
        </div>
      </section>

      {isRenameModalOpen && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/20 backdrop-blur-sm px-6">
          <div className="bg-white rounded-[32px] p-8 w-full max-w-md shadow-2xl border border-[#4A453E]/10 animate-in fade-in zoom-in duration-200">
            <h3 className="text-2xl font-serif-brand font-bold text-[#4A453E] mb-6 italic">重命名对话</h3>
            <input 
              type="text" 
              value={renamingTitle}
              onChange={(e) => setRenamingTitle(e.target.value)}
              autoFocus
              className="w-full bg-[#F7F3E9]/40 border border-[#4A453E]/10 rounded-[18px] px-6 py-4 font-bold text-[#4A453E] focus:ring-2 focus:ring-[#FF8A65]/20 focus:bg-white outline-none transition-all mb-8"
              onKeyDown={(e) => e.key === 'Enter' && handleRenameSession()}
            />
            <div className="flex gap-3">
              <button onClick={() => setIsRenameModalOpen(false)} className="flex-1 py-3 bg-white text-[#4A453E]/40 font-bold text-sm rounded-full border border-[#4A453E]/10 hover:bg-[#F7F3E9] transition-all">取消</button>
              <button onClick={handleRenameSession} className="flex-1 py-3 bg-[#FF8A65] text-white font-bold text-sm rounded-full shadow-lg shadow-[#FF8A65]/20 hover:translate-y-[-1px] transition-all">保存</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};