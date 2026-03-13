import React, { useEffect, useState } from 'react';

import { clearSession, restoreSession } from '../api/auth';
import { clearStoredProfile, loadStoredProfile, ProfileApiError, toProfileForm } from '../api/profile';
import { loadUserFoodLog, loadUserSessions, saveUserFoodLog, saveUserSessions } from '../api/userData';
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
      const userId = session.user.id;
      const storedSessions = loadUserSessions(userId);
      const storedFoodLog = loadUserFoodLog(userId);

      if (!cancelled) {
        setSessions(storedSessions);
        setFoodLog(storedFoodLog);
        setActiveSessionId((currentId) =>
          storedSessions.some((item) => item.id === currentId)
            ? currentId
            : storedSessions[0]?.id || '',
        );
      }

      try {
        const storedProfile = await loadStoredProfile();
        if (cancelled) {
          return;
        }
        setProfile(storedProfile ? toProfileForm(storedProfile) : createDefaultProfile());
      } catch (error) {
        if (cancelled) {
          return;
        }
        if (!(error instanceof ProfileApiError && error.status === 404)) {
          console.error('Failed to load profile:', error);
        }
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

  useEffect(() => {
    if (authStatus !== 'authenticated' || !session || isBootstrappingData) {
      return;
    }
    saveUserSessions(session.user.id, sessions);
  }, [authStatus, isBootstrappingData, session, sessions]);

  useEffect(() => {
    if (authStatus !== 'authenticated' || !session || isBootstrappingData) {
      return;
    }
    saveUserFoodLog(session.user.id, foodLog);
  }, [authStatus, foodLog, isBootstrappingData, session]);

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

  const handleLogout = () => {
    clearSession();
    clearStoredProfile();
    resetUnauthenticatedState('login');
  };

  const handleAuthenticated = (nextSession: AuthSession) => {
    applyAuthenticatedState(nextSession);
  };

  const handleNavigateToSession = (sessionId: string) => {
    setActiveSessionId(sessionId);
    setCurrentView(AppView.WORKSPACE);
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
            setFoodLog={setFoodLog}
            activeSessionId={activeSessionId}
            setActiveSessionId={setActiveSessionId}
            profileId={profile.id}
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
            setFoodLog={setFoodLog}
            activeSessionId={activeSessionId}
            setActiveSessionId={setActiveSessionId}
            profileId={profile.id}
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
