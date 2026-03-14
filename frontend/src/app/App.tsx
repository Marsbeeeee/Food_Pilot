import React, { useEffect, useState } from 'react';

import { AuthApiError, clearSession, deleteCurrentAccount, restoreSession } from '../api/auth';
import { buildFoodLogNavigationState } from './foodLogNavigation';
import { getChatSession, listChatSessions } from '../api/chat';
import { listFoodLogs } from '../api/foodLog';
import { clearStoredProfile, loadStoredProfile, ProfileApiError, toProfileForm } from '../api/profile';
import { Header } from '../components/Header';
import { AuthPage } from '../pages/Auth';
import { Explorer } from '../pages/Explorer';
import { Profile } from '../pages/Profile';
import { Workspace } from '../pages/Workspace';
import {
  AppView,
  AuthScreenMode,
  AuthSession,
  AuthStatus,
  ChatSession,
  FoodLogEntry,
  UserProfileForm,
} from '../types/types';

const DEFAULT_PROFILE: UserProfileForm = {
  age: '',
  height: '',
  weight: '',
  sex: 'Prefer not to say',
  activityLevel: 'Sedentary',
  exerciseType: 'Minimal',
  goal: 'General health',
  pace: 'Moderate',
  kcalTarget: '2000',
  dietStyle: 'Balanced',
  allergies: [],
};

const App: React.FC = () => {
  const [currentView, setCurrentView] = useState<AppView>(AppView.WORKSPACE);
  const [authStatus, setAuthStatus] = useState<AuthStatus>('loading');
  const [authMode, setAuthMode] = useState<AuthScreenMode>('login');
  const [session, setSession] = useState<AuthSession | null>(null);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [foodLog, setFoodLog] = useState<FoodLogEntry[]>([]);
  const [profile, setProfile] = useState<UserProfileForm>(createDefaultProfile());
  const [isBootstrappingData, setIsBootstrappingData] = useState(false);
  const [isDeletingAccount, setIsDeletingAccount] = useState(false);
  const [activeSessionId, setActiveSessionId] = useState<string>('');

  useEffect(() => {
    let cancelled = false;

    const initializeAuth = async () => {
      setAuthStatus('loading');

      try {
        const restoredSession = await restoreSession();
        if (cancelled) {
          return;
        }

        if (restoredSession) {
          applyAuthenticatedState(restoredSession);
        } else {
          resetUnauthenticatedState('login');
        }
      } catch (error) {
        console.error('Failed to restore session:', error);
        if (!cancelled) {
          resetUnauthenticatedState('login');
        }
      }
    };

    initializeAuth();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (authStatus !== 'authenticated' || !session) {
      return;
    }

    let cancelled = false;

    const hydrateUserData = async () => {
      setIsBootstrappingData(true);

      try {
        const [storedProfile, sessionSummaries, foodLogEntries] = await Promise.all([
          loadStoredProfile(),
          listChatSessions(),
          listFoodLogs(),
        ]);
        if (cancelled) {
          return;
        }

        setProfile(storedProfile ? toProfileForm(storedProfile) : createDefaultProfile());
        setSessions(sessionSummaries);
        setFoodLog(foodLogEntries);
        setActiveSessionId((currentId) =>
          sessionSummaries.some((item) => item.id === currentId)
            ? currentId
            : sessionSummaries[0]?.id || '',
        );

        if (sessionSummaries.length > 0) {
          const detailedSessions = await Promise.all(
            sessionSummaries.map(async (chatSession) => {
              try {
                return await getChatSession(chatSession.id);
              } catch (error) {
                console.error(`Failed to load chat session ${chatSession.id}:`, error);
                return chatSession;
              }
            }),
          );

          if (!cancelled) {
            setSessions(detailedSessions);
            setActiveSessionId((currentId) =>
              detailedSessions.some((item) => item.id === currentId)
                ? currentId
                : detailedSessions[0]?.id || '',
            );
          }
        }
      } catch (error) {
        if (cancelled) {
          return;
        }
        if (!(error instanceof ProfileApiError && error.status === 404)) {
          console.error('Failed to load profile:', error);
        }
        console.error('Failed to load chat sessions:', error);
        setSessions([]);
        setFoodLog([]);
        setProfile(createDefaultProfile());
      } finally {
        if (!cancelled) {
          setIsBootstrappingData(false);
        }
      }
    };

    hydrateUserData();

    return () => {
      cancelled = true;
    };
  }, [authStatus, session]);

  const resetUnauthenticatedState = (nextMode: AuthScreenMode) => {
    setIsBootstrappingData(false);
    setAuthStatus('unauthenticated');
    setAuthMode(nextMode);
    setSession(null);
    setSessions([]);
    setFoodLog([]);
    setProfile(createDefaultProfile());
    setCurrentView(AppView.WORKSPACE);
    setActiveSessionId('');
  };

  const applyAuthenticatedState = (nextSession: AuthSession) => {
    setIsBootstrappingData(true);
    setSession(nextSession);
    setAuthStatus('authenticated');
    setSessions([]);
    setFoodLog([]);
    setProfile(createDefaultProfile());
    setCurrentView(AppView.WORKSPACE);
    setActiveSessionId('');
  };

  const refreshFoodLog = async () => {
    try {
      const entries = await listFoodLogs();
      setFoodLog(entries);
    } catch (error) {
      console.error('Failed to load food log:', error);
    }
  };

  const handleLogout = () => {
    clearSession();
    clearStoredProfile();
    resetUnauthenticatedState('login');
  };

  const handleDeleteAccount = async () => {
    if (!session || isDeletingAccount) {
      return;
    }

    const shouldDelete = window.confirm(
      'Delete this account permanently? Your profile and this device\'s saved chat history will be removed.',
    );
    if (!shouldDelete) {
      return;
    }

    setIsDeletingAccount(true);

    try {
      await deleteCurrentAccount();
      clearSession();
      clearStoredProfile();
      resetUnauthenticatedState('register');
      window.alert('Your account has been deleted.');
    } catch (error) {
      const message = error instanceof AuthApiError
        ? error.message
        : error instanceof Error
          ? error.message
          : 'Failed to delete this account. Please try again.';
      window.alert(message);
    } finally {
      setIsDeletingAccount(false);
    }
  };

  const handleAuthenticated = (nextSession: AuthSession) => {
    applyAuthenticatedState(nextSession);
  };

  const handleNavigateToSession = (sessionId: string) => {
    const nextState = buildFoodLogNavigationState(sessionId) as {
      activeSessionId: string;
      currentView: AppView;
    };
    setActiveSessionId(nextState.activeSessionId);
    setCurrentView(nextState.currentView);
  };

  const renderView = () => {
    if (authStatus === 'loading' || (authStatus === 'authenticated' && isBootstrappingData)) {
      return (
        <div className="flex flex-1 items-center justify-center bg-[radial-gradient(circle_at_top,_rgba(255,138,101,0.14),_transparent_35%),#FFFDF5]">
          <div className="rounded-[32px] border border-[#4A453E]/8 bg-white/75 px-8 py-10 text-center shadow-[0_20px_60px_rgba(74,69,62,0.08)]">
            <div className="mx-auto mb-4 flex size-14 items-center justify-center rounded-full bg-[#FF8A65]/10">
              <span className="material-symbols-outlined animate-spin text-2xl text-[#FF8A65]">
                progress_activity
              </span>
            </div>
            <h2 className="font-serif-brand text-2xl font-bold text-[#4A453E]">Restoring session</h2>
            <p className="mt-2 text-sm text-[#4A453E]/50">
              {authStatus === 'loading'
                ? 'Checking whether there is a valid FoodPilot login on this device.'
                : 'Loading your profile, sessions, and food log.'}
            </p>
          </div>
        </div>
      );
    }

    if (authStatus !== 'authenticated' || !session) {
      return (
        <AuthPage
          mode={authMode}
          onModeChange={setAuthMode}
          onAuthenticated={handleAuthenticated}
        />
      );
    }

    switch (currentView) {
      case AppView.WORKSPACE:
        return (
          <Workspace
            sessions={sessions}
            setSessions={setSessions}
            activeSessionId={activeSessionId}
            setActiveSessionId={setActiveSessionId}
            profileId={profile.id}
            refreshFoodLog={refreshFoodLog}
          />
        );
      case AppView.EXPLORER:
        return (
          <Explorer
            logEntries={foodLog}
            onNavigateToSession={handleNavigateToSession}
          />
        );
      case AppView.PROFILE:
        return <Profile profile={profile} setProfile={setProfile} />;
      default:
        return (
          <Workspace
            sessions={sessions}
            setSessions={setSessions}
            activeSessionId={activeSessionId}
            setActiveSessionId={setActiveSessionId}
            profileId={profile.id}
            refreshFoodLog={refreshFoodLog}
          />
        );
    }
  };

  return (
    <div className="flex h-screen flex-col overflow-hidden bg-[#FFFDF5]">
      <Header
        currentView={currentView}
        onViewChange={setCurrentView}
        isLoggedIn={authStatus === 'authenticated'}
        currentUser={session?.user ?? null}
        authMode={authMode}
        onAuthModeChange={setAuthMode}
        onLogout={handleLogout}
        onDeleteAccount={handleDeleteAccount}
        isDeletingAccount={isDeletingAccount}
      />
      <main className="flex min-h-0 flex-1 overflow-hidden">{renderView()}</main>
    </div>
  );
};

function createDefaultProfile(): UserProfileForm {
  return {
    ...DEFAULT_PROFILE,
    allergies: [...DEFAULT_PROFILE.allergies],
  };
}

export default App;
