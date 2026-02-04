
import React, { useState, useEffect, useRef } from 'react';
import { Logo } from './Logo';
import { AppView } from '../main';

interface HeaderProps {
  currentView: AppView;
  onViewChange: (view: AppView) => void;
  isLoggedIn: boolean;
  onLogin: () => void;
  onLogout: () => void;
}

export const Header: React.FC<HeaderProps> = ({ currentView, onViewChange, isLoggedIn, onLogin, onLogout }) => {
  const [isAvatarMenuOpen, setIsAvatarMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsAvatarMenuOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <header className="flex items-center justify-between border-b border-[#4A453E]/5 px-6 py-3 bg-white/80 backdrop-blur-sm sticky top-0 z-[60] h-16">
      <Logo />
      
      <div className="flex items-center gap-8">
        <nav className="flex items-center gap-6 hidden md:flex">
          <button 
            onClick={() => onViewChange(AppView.WORKSPACE)}
            className={`text-sm font-semibold relative py-1 transition-colors ${
              currentView === AppView.WORKSPACE ? 'text-[#FF8A65] after:absolute after:bottom-0 after:left-0 after:w-full after:h-0.5 after:bg-[#FF8A65]' : 'text-[#4A453E]/60 hover:text-[#FF8A65]'
            }`}
          >
            咨询 FoodPilot
          </button>
          <button 
            onClick={() => onViewChange(AppView.EXPLORER)}
            className={`text-sm font-semibold relative py-1 transition-colors ${
              currentView === AppView.EXPLORER ? 'text-[#FF8A65] after:absolute after:bottom-0 after:left-0 after:w-full after:h-0.5 after:bg-[#FF8A65]' : 'text-[#4A453E]/60 hover:text-[#FF8A65]'
            }`}
          >
            我的饮食日志
          </button>
          <button 
            onClick={() => onViewChange(AppView.PROFILE)}
            className={`text-sm font-semibold relative py-1 transition-colors ${
              currentView === AppView.PROFILE ? 'text-[#FF8A65] after:absolute after:bottom-0 after:left-0 after:w-full after:h-0.5 after:bg-[#FF8A65]' : 'text-[#4A453E]/60 hover:text-[#FF8A65]'
            }`}
          >
            个人档案
          </button>
        </nav>

        <div className="flex items-center gap-4 relative" ref={menuRef}>
          {isLoggedIn ? (
            <>
              <div className="flex items-center bg-[#F7F3E9] rounded-full px-3 py-1 gap-2 border border-[#4A453E]/5">
                <span className="flex h-2 w-2 rounded-full bg-[#81C784] animate-pulse"></span>
                <span className="text-[10px] font-bold uppercase text-[#4A453E]/70 tracking-widest">在线</span>
              </div>
              
              <button 
                onClick={() => setIsAvatarMenuOpen(!isAvatarMenuOpen)}
                className={`bg-center bg-no-repeat aspect-square bg-cover rounded-full size-9 border transition-all ${
                  isAvatarMenuOpen ? 'ring-2 ring-[#FF8A65] ring-offset-2 border-transparent' : 'border-[#4A453E]/10 shadow-sm hover:border-[#FF8A65]/50'
                }`}
                style={{ backgroundImage: 'url("https://picsum.photos/seed/user123/100/100")' }}
              ></button>

              {isAvatarMenuOpen && (
                <div className="absolute right-0 top-full mt-3 w-52 bg-white rounded-[24px] shadow-2xl border border-[#4A453E]/10 py-2 z-[70] overflow-hidden animate-in fade-in slide-in-from-top-2 duration-200">
                  <div className="px-4 py-3 border-b border-[#4A453E]/05 mb-1">
                    <p className="text-[11px] font-bold text-[#4A453E]/30 uppercase tracking-widest mb-0.5">登录身份</p>
                    <p className="text-sm font-bold text-[#4A453E] truncate">alex_pilot@example.com</p>
                  </div>
                  <button 
                    onClick={() => {
                      onViewChange(AppView.PROFILE);
                      setIsAvatarMenuOpen(false);
                    }}
                    className="w-full flex items-center gap-3 px-4 py-3 text-sm font-bold text-[#4A453E]/70 hover:bg-[#F7F3E9] hover:text-[#4A453E] transition-colors"
                  >
                    <span className="material-symbols-outlined text-[18px]">account_circle</span>
                    编辑头像
                  </button>
                  <div className="h-[1px] bg-[#4A453E]/5 mx-2 my-1"></div>
                  <button 
                    onClick={() => {
                      setIsAvatarMenuOpen(false);
                      onLogout();
                    }}
                    className="w-full flex items-center gap-3 px-4 py-3 text-sm font-bold text-red-400 hover:bg-red-50 transition-colors"
                  >
                    <span className="material-symbols-outlined text-[18px]">logout</span>
                    退出登录
                  </button>
                </div>
              )}
            </>
          ) : (
            <button 
              onClick={onLogin}
              className="px-6 py-2 bg-[#FF8A65] text-white rounded-full text-sm font-bold shadow-lg shadow-[#FF8A65]/20 hover:bg-[#FF8A65]/90 transition-all"
            >
              登录
            </button>
          )}
        </div>
      </div>
    </header>
  );
};