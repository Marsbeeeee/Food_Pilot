import React, { useEffect, useState } from 'react';

import { clearSession, restoreSession } from '../api/auth';
import { clearStoredProfile } from '../api/profile';
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

const MOCK_USER_SESSIONS: ChatSession[] = [
  {
    id: '8291',
    title: 'Mediterranean lunch bowl',
    icon: 'restaurant',
    timestamp: new Date(),
    messages: [
      {
        role: 'user',
        content: 'Estimate the calories in a chicken salad with half an avocado and one small apple.',
        time: '12:45 PM',
      },
      {
        role: 'assistant',
        isResult: true,
        title: 'Analysis complete',
        confidence: 'High confidence',
        description:
          'Using standard portions, this meal is a balanced mix of lean protein, healthy fat, and fiber.',
        items: [
          { name: 'Grilled chicken breast', portion: '150g', energy: '248 kcal' },
          { name: 'Mixed greens', portion: '2 cups', energy: '20 kcal' },
          { name: 'Avocado', portion: '0.5 medium', energy: '160 kcal' },
          { name: 'Apple', portion: '1 small', energy: '75 kcal' },
        ],
        total: '503 kcal',
        time: '12:46 PM',
      },
    ],
  },
];

const MOCK_USER_LOG: FoodLogEntry[] = [
  {
    id: '1',
    name: 'Herb chicken grain bowl',
    description: 'Grilled chicken with quinoa, kale, and a lemon sesame dressing.',
    calories: '480',
    date: 'Today',
    time: '1:15 PM',
    image:
      'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&q=80&w=400',
    protein: '32g',
    carbs: '45g',
    fat: '18g',
    sessionId: '8291',
    breakdown: [
      { name: 'Grilled chicken', portion: '150g', energy: '248 kcal' },
      { name: 'Quinoa', portion: '1 cup', energy: '222 kcal' },
      { name: 'Kale and dressing', portion: '1.5 cups', energy: '10 kcal' },
    ],
  },
];

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

  const resetUnauthenticatedState = (nextMode: AuthScreenMode) => {
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
    setSession(nextSession);
    setAuthStatus('authenticated');
    setSessions(createInitialSessions());
    setFoodLog(createInitialFoodLog());
    setProfile(createDefaultProfile());
    setCurrentView(AppView.WORKSPACE);
    setActiveSessionId(MOCK_USER_SESSIONS[0]?.id || '');
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
    if (authStatus === 'loading') {
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
              Checking whether there is a valid FoodPilot login on this device.
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
          />
        );
    }
  };

  return (
    <div className="flex min-h-screen flex-col overflow-hidden bg-[#FFFDF5]">
      <Header
        currentView={currentView}
        onViewChange={setCurrentView}
        isLoggedIn={authStatus === 'authenticated'}
        currentUser={session?.user ?? null}
        authMode={authMode}
        onAuthModeChange={setAuthMode}
        onLogout={handleLogout}
      />
      <main className="flex h-[calc(100vh-64px)] flex-1 overflow-hidden">{renderView()}</main>
    </div>
  );
};

function createInitialSessions(): ChatSession[] {
  return MOCK_USER_SESSIONS.map((session) => ({
    ...session,
    timestamp: new Date(session.timestamp),
    messages: session.messages.map((message) => ({ ...message })),
  }));
}

function createInitialFoodLog(): FoodLogEntry[] {
  return MOCK_USER_LOG.map((entry) => ({
    ...entry,
    breakdown: entry.breakdown.map((item) => ({ ...item })),
  }));
}

function createDefaultProfile(): UserProfileForm {
  return {
    ...DEFAULT_PROFILE,
    allergies: [...DEFAULT_PROFILE.allergies],
  };
}

export default App;
