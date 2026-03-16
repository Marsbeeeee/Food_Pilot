import React, { useEffect, useRef, useState } from 'react';

import { AppView, AuthScreenMode, AuthUser } from '../types/types';
import { Logo } from './Logo';

interface HeaderProps {
  currentView: AppView;
  onViewChange: (view: AppView) => void;
  isLoggedIn: boolean;
  currentUser: AuthUser | null;
  authMode: AuthScreenMode;
  onAuthModeChange: (mode: AuthScreenMode) => void;
  onLogout: () => void;
  onDeleteAccount: () => void;
  isDeletingAccount: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  currentView,
  onViewChange,
  isLoggedIn,
  currentUser,
  authMode,
  onAuthModeChange,
  onLogout,
  onDeleteAccount,
  isDeletingAccount,
}) => {
  const [isAvatarMenuOpen, setIsAvatarMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsAvatarMenuOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <header className="sticky top-0 z-[60] flex h-16 items-center justify-between border-b border-[#4A453E]/5 bg-white/80 px-6 py-3 backdrop-blur-sm">
      <Logo />

      <div className="flex items-center gap-8">
        <nav className="hidden items-center gap-6 md:flex">
          <button
            onClick={() => onViewChange(AppView.WORKSPACE)}
            className={`relative py-1 text-sm font-semibold transition-colors ${
              currentView === AppView.WORKSPACE
                ? 'text-[#FF8A65] after:absolute after:bottom-0 after:left-0 after:h-0.5 after:w-full after:bg-[#FF8A65]'
                : 'text-[#4A453E]/60 hover:text-[#FF8A65]'
            }`}
          >
            Chat
          </button>
          <button
            onClick={() => onViewChange(AppView.EXPLORER)}
            className={`relative py-1 text-sm font-semibold transition-colors ${
              currentView === AppView.EXPLORER
                ? 'text-[#FF8A65] after:absolute after:bottom-0 after:left-0 after:h-0.5 after:w-full after:bg-[#FF8A65]'
                : 'text-[#4A453E]/60 hover:text-[#FF8A65]'
            }`}
          >
            Food Log
          </button>
          <button
            onClick={() => onViewChange(AppView.INSIGHTS)}
            className={`relative py-1 text-sm font-semibold transition-colors ${
              currentView === AppView.INSIGHTS
                ? 'text-[#FF8A65] after:absolute after:bottom-0 after:left-0 after:h-0.5 after:w-full after:bg-[#FF8A65]'
                : 'text-[#4A453E]/60 hover:text-[#FF8A65]'
            }`}
          >
            Insights
          </button>
          <button
            onClick={() => onViewChange(AppView.PROFILE)}
            className={`relative py-1 text-sm font-semibold transition-colors ${
              currentView === AppView.PROFILE
                ? 'text-[#FF8A65] after:absolute after:bottom-0 after:left-0 after:h-0.5 after:w-full after:bg-[#FF8A65]'
                : 'text-[#4A453E]/60 hover:text-[#FF8A65]'
            }`}
          >
            Profile
          </button>
        </nav>

        <div className="relative flex items-center gap-4" ref={menuRef}>
          {isLoggedIn ? (
            <>
              <div className="flex items-center gap-2 rounded-full border border-[#4A453E]/5 bg-[#F7F3E9] px-3 py-1">
                <span className="flex h-2 w-2 rounded-full bg-[#81C784] animate-pulse" />
                <span className="text-[10px] font-bold uppercase tracking-widest text-[#4A453E]/70">
                  Signed in
                </span>
              </div>

              <button
                onClick={() => setIsAvatarMenuOpen((prev) => !prev)}
                className={`flex size-9 items-center justify-center rounded-full border text-sm font-black uppercase transition-all ${
                  isAvatarMenuOpen
                    ? 'border-transparent bg-[#FF8A65] text-white ring-2 ring-[#FF8A65] ring-offset-2'
                    : 'border-[#4A453E]/10 bg-[#F7F3E9] text-[#4A453E] shadow-sm hover:border-[#FF8A65]/50'
                }`}
              >
                {getUserInitial(currentUser)}
              </button>

              {isAvatarMenuOpen && (
                <div className="absolute right-0 top-full z-[70] mt-3 w-60 overflow-hidden rounded-[24px] border border-[#4A453E]/10 bg-white py-2 shadow-2xl">
                  <div className="mb-1 border-b border-[#4A453E]/5 px-4 py-3">
                    <p className="mb-1 text-[11px] font-bold uppercase tracking-widest text-[#4A453E]/30">
                      Current account
                    </p>
                    <p className="truncate text-sm font-bold text-[#4A453E]">
                      {currentUser?.displayName ?? 'Unknown user'}
                    </p>
                    <p className="truncate text-xs font-medium text-[#4A453E]/45">
                      {currentUser?.email ?? 'No email'}
                    </p>
                  </div>
                  <button
                    onClick={() => {
                      onViewChange(AppView.PROFILE);
                      setIsAvatarMenuOpen(false);
                    }}
                    className="flex w-full items-center gap-3 px-4 py-3 text-sm font-bold text-[#4A453E]/70 transition-colors hover:bg-[#F7F3E9] hover:text-[#4A453E]"
                  >
                    <span className="material-symbols-outlined text-[18px]">account_circle</span>
                    Open profile
                  </button>
                  <div className="mx-2 my-1 h-px bg-[#4A453E]/5" />
                  <button
                    onClick={() => {
                      setIsAvatarMenuOpen(false);
                      onLogout();
                    }}
                    className="flex w-full items-center gap-3 px-4 py-3 text-sm font-bold text-red-400 transition-colors hover:bg-red-50"
                  >
                    <span className="material-symbols-outlined text-[18px]">logout</span>
                    Sign out
                  </button>
                  <div className="mx-2 my-1 h-px bg-[#4A453E]/5" />
                  <button
                    onClick={() => {
                      setIsAvatarMenuOpen(false);
                      onDeleteAccount();
                    }}
                    disabled={isDeletingAccount}
                    className={`flex w-full items-center gap-3 px-4 py-3 text-sm font-bold transition-colors ${
                      isDeletingAccount
                        ? 'cursor-not-allowed text-red-300'
                        : 'text-red-500 hover:bg-red-50'
                    }`}
                  >
                    <span className="material-symbols-outlined text-[18px]">delete_forever</span>
                    {isDeletingAccount ? 'Deleting account...' : 'Delete account'}
                  </button>
                </div>
              )}
            </>
          ) : (
            <div className="flex items-center gap-2">
              <button
                onClick={() => onAuthModeChange('login')}
                className={`rounded-full px-4 py-2 text-sm font-bold transition-all ${
                  authMode === 'login'
                    ? 'bg-[#4A453E] text-white'
                    : 'border border-[#4A453E]/10 bg-white text-[#4A453E]/60 hover:text-[#4A453E]'
                }`}
              >
                Sign in
              </button>
              <button
                onClick={() => onAuthModeChange('register')}
                className={`rounded-full px-4 py-2 text-sm font-bold transition-all ${
                  authMode === 'register'
                    ? 'bg-[#FF8A65] text-white shadow-lg shadow-[#FF8A65]/15'
                    : 'bg-[#FF8A65]/10 text-[#FF8A65] hover:bg-[#FF8A65]/15'
                }`}
              >
                Create account
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

function getUserInitial(user: AuthUser | null): string {
  const source = user?.displayName || user?.email || 'U';
  return source.charAt(0).toUpperCase();
}
