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
  onChangeDisplayName: (displayName: string) => Promise<void>;
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
  onChangeDisplayName,
  onDeleteAccount,
  isDeletingAccount,
}) => {
  const [isAvatarMenuOpen, setIsAvatarMenuOpen] = useState(false);
  const [isChangingName, setIsChangingName] = useState(false);
  const [isChangeNameModalOpen, setIsChangeNameModalOpen] = useState(false);
  const [nextDisplayName, setNextDisplayName] = useState('');
  const [changeNameError, setChangeNameError] = useState<string | null>(null);
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

  const openChangeNameModal = () => {
    if (!currentUser || isChangingName) {
      return;
    }
    setNextDisplayName(currentUser.displayName);
    setChangeNameError(null);
    setIsAvatarMenuOpen(false);
    setIsChangeNameModalOpen(true);
  };

  const closeChangeNameModal = () => {
    if (isChangingName) {
      return;
    }
    setIsChangeNameModalOpen(false);
    setChangeNameError(null);
  };

  const handleSubmitChangeName = async () => {
    if (!currentUser || isChangingName) {
      return;
    }

    const normalizedName = nextDisplayName.trim();
    if (!normalizedName) {
      setChangeNameError('Display name cannot be empty.');
      return;
    }

    if (normalizedName === currentUser.displayName) {
      closeChangeNameModal();
      return;
    }

    setChangeNameError(null);
    setIsChangingName(true);
    try {
      await onChangeDisplayName(normalizedName);
      closeChangeNameModal();
    } catch (error) {
      setChangeNameError(error instanceof Error && error.message
        ? error.message
        : 'Failed to change display name. Please try again.');
    } finally {
      setIsChangingName(false);
    }
  };

  useEffect(() => {
    if (!isChangeNameModalOpen) {
      return undefined;
    }

    const handleEscapeKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        closeChangeNameModal();
      }
    };

    document.addEventListener('keydown', handleEscapeKey);
    return () => document.removeEventListener('keydown', handleEscapeKey);
  }, [isChangeNameModalOpen, isChangingName]);

  return (
    <>
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
                      onClick={openChangeNameModal}
                      disabled={isChangingName}
                      className={`flex w-full items-center gap-3 px-4 py-3 text-left text-sm font-bold transition-colors ${
                        isChangingName
                          ? 'cursor-not-allowed text-[#4A453E]/35'
                          : 'text-[#4A453E]/70 hover:bg-[#F7F3E9] hover:text-[#4A453E]'
                      }`}
                    >
                      <span className="material-symbols-outlined text-[18px]">edit</span>
                      <span className="flex min-w-0 flex-col">
                        <span>{isChangingName ? 'changing...' : 'change name'}</span>
                        <span className="max-w-[170px] truncate text-xs font-medium text-[#4A453E]/45">
                          {currentUser?.displayName ?? 'Unknown user'}
                        </span>
                      </span>
                    </button>
                    {currentUser?.isAdmin && (
                      <button
                        onClick={() => {
                          onViewChange(AppView.ADMIN_DISH_IMAGES);
                          setIsAvatarMenuOpen(false);
                        }}
                        className="flex w-full items-center gap-3 px-4 py-3 text-sm font-bold text-[#4A453E]/70 transition-colors hover:bg-[#F7F3E9] hover:text-[#4A453E]"
                      >
                        <span className="material-symbols-outlined text-[18px]">gallery_thumbnail</span>
                        Review dish images
                      </button>
                    )}
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

      {isChangeNameModalOpen && (
        <div
          className="fixed inset-0 z-[120] flex items-center justify-center bg-[#4A453E]/35 px-6 backdrop-blur-[2px]"
          onClick={closeChangeNameModal}
        >
          <div
            className="w-full max-w-md overflow-hidden rounded-[28px] border border-[#4A453E]/10 bg-[#FFFDF5] shadow-[0_28px_70px_rgba(74,69,62,0.18)]"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="h-1.5 bg-[linear-gradient(90deg,#FF8A65,#FFD180,#81C784)]" />
            <div className="p-6">
              <div className="mb-5">
                <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-[#4A453E]/30">
                  Account
                </p>
                <h3 className="mt-2 text-xl font-bold text-[#4A453E]">Change Name</h3>
                <p className="mt-1 text-sm text-[#4A453E]/55">
                  Update the name shown in your account menu.
                </p>
              </div>

              <label className="mb-2 block text-[10px] font-bold uppercase tracking-[0.2em] text-[#4A453E]/35">
                Display name
              </label>
              <input
                type="text"
                value={nextDisplayName}
                onChange={(event) => setNextDisplayName(event.target.value)}
                onKeyDown={(event) => event.key === 'Enter' && void handleSubmitChangeName()}
                autoFocus
                disabled={isChangingName}
                className="w-full rounded-[16px] border border-[#4A453E]/10 bg-white px-4 py-3 text-sm font-semibold text-[#4A453E] outline-none transition-all placeholder:text-[#4A453E]/25 focus:border-[#FF8A65]/40 focus:ring-2 focus:ring-[#FF8A65]/15 disabled:cursor-not-allowed disabled:bg-[#F7F3E9]/70 disabled:text-[#4A453E]/45"
                placeholder="How people see your name"
              />
              {changeNameError && (
                <p className="mt-3 rounded-[14px] border border-red-200 bg-red-50 px-3 py-2 text-xs font-semibold text-red-500">
                  {changeNameError}
                </p>
              )}

              <div className="mt-6 flex justify-end gap-3">
                <button
                  onClick={closeChangeNameModal}
                  disabled={isChangingName}
                  className="rounded-[14px] border border-[#4A453E]/10 bg-white px-4 py-2.5 text-sm font-semibold text-[#4A453E]/55 transition-colors hover:bg-[#F7F3E9] disabled:cursor-not-allowed disabled:text-[#4A453E]/30"
                >
                  Cancel
                </button>
                <button
                  onClick={() => void handleSubmitChangeName()}
                  disabled={isChangingName}
                  className={`rounded-[14px] px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-[#FF8A65]/20 transition-colors ${
                    isChangingName
                      ? 'cursor-not-allowed bg-[#FF8A65]/55'
                      : 'bg-[#FF8A65] hover:bg-[#FF8A65]/90'
                  }`}
                >
                  {isChangingName ? 'Saving...' : 'Save'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

function getUserInitial(user: AuthUser | null): string {
  const source = user?.displayName || user?.email || 'U';
  return source.charAt(0).toUpperCase();
}
