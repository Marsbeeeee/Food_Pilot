import React, { useEffect, useState } from 'react';

import { AuthApiError, login, register } from '../api/auth';
import { AuthScreenMode, AuthSession } from '../types/types';

interface AuthPageProps {
  mode: AuthScreenMode;
  onModeChange: (mode: AuthScreenMode) => void;
  onAuthenticated: (session: AuthSession) => void;
}

type FormStatus = 'idle' | 'submitting' | 'error';

const INPUT_CLASSNAME =
  'w-full rounded-[20px] border border-[#4A453E]/10 bg-white/90 px-5 py-4 text-sm font-semibold text-[#4A453E] outline-none transition-all placeholder:text-[#4A453E]/25 focus:border-[#FF8A65]/40 focus:ring-4 focus:ring-[#FF8A65]/10';

export const AuthPage: React.FC<AuthPageProps> = ({
  mode,
  onModeChange,
  onAuthenticated,
}) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [status, setStatus] = useState<FormStatus>('idle');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    setStatus('idle');
    setErrorMessage(null);
  }, [mode]);

  const isRegister = mode === 'register';
  const isSubmitting = status === 'submitting';

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (isSubmitting) {
      return;
    }

    setStatus('submitting');
    setErrorMessage(null);

    try {
      const session = isRegister
        ? await register({ email, password, displayName })
        : await login({ email, password });
      onAuthenticated(session);
    } catch (error) {
      setStatus('error');
      setErrorMessage(getErrorMessage(error));
    }
  };

  return (
    <div className="flex-1 overflow-y-auto bg-[radial-gradient(circle_at_top_left,_rgba(255,138,101,0.2),_transparent_38%),linear-gradient(135deg,#fffdf5_0%,#f7f3e9_48%,#f1ebde_100%)]">
      <div className="mx-auto flex min-h-full w-full max-w-6xl flex-col gap-10 px-6 py-10 lg:grid lg:grid-cols-[1.1fr_0.9fr] lg:items-center lg:px-10">
        <section className="rounded-[36px] border border-white/70 bg-white/50 p-8 shadow-[0_24px_80px_rgba(74,69,62,0.08)] backdrop-blur-sm lg:p-10">
          <p className="mb-4 text-[11px] font-black uppercase tracking-[0.32em] text-[#FF8A65]">
            FoodPilot Account
          </p>
          <h1 className="max-w-xl font-serif-brand text-5xl font-bold leading-tight text-[#4A453E]">
            Keep your nutrition context synced to a real account.
          </h1>
          <p className="mt-6 max-w-xl text-base leading-8 text-[#4A453E]/70">
            Sign in to restore your profile and keep FoodPilot anchored to the same person on every request.
          </p>

          <div className="mt-10 grid gap-4 sm:grid-cols-3">
            <InsightCard
              eyebrow="Identity"
              title="Real session"
              body="The app now restores the current user from a signed token instead of a mock boolean."
            />
            <InsightCard
              eyebrow="Security"
              title="Safe by default"
              body="Passwords stay on the backend. The frontend only stores the bearer token and the cached user payload."
            />
            <InsightCard
              eyebrow="Flow"
              title="One account"
              body="Register once, sign in again later, and the app verifies the session on startup."
            />
          </div>
        </section>

        <section className="relative overflow-hidden rounded-[36px] border border-[#4A453E]/10 bg-white px-6 py-8 shadow-[0_24px_80px_rgba(74,69,62,0.12)] sm:px-8 lg:px-10">
          <div className="absolute inset-x-0 top-0 h-24 bg-[linear-gradient(90deg,rgba(255,138,101,0.16),rgba(129,199,132,0.12),transparent)]" />

          <div className="relative">
            <div className="mb-8 inline-flex rounded-full bg-[#F7F3E9] p-1">
              <button
                onClick={() => onModeChange('login')}
                className={`rounded-full px-5 py-2 text-sm font-bold transition-all ${
                  mode === 'login'
                    ? 'bg-white text-[#4A453E] shadow-sm'
                    : 'text-[#4A453E]/45 hover:text-[#4A453E]'
                }`}
                type="button"
              >
                Sign in
              </button>
              <button
                onClick={() => onModeChange('register')}
                className={`rounded-full px-5 py-2 text-sm font-bold transition-all ${
                  mode === 'register'
                    ? 'bg-white text-[#4A453E] shadow-sm'
                    : 'text-[#4A453E]/45 hover:text-[#4A453E]'
                }`}
                type="button"
              >
                Create account
              </button>
            </div>

            <div className="mb-8">
              <h2 className="text-3xl font-serif-brand font-bold text-[#4A453E]">
                {isRegister ? 'Create your account' : 'Welcome back'}
              </h2>
              <p className="mt-2 text-sm leading-7 text-[#4A453E]/55">
                {isRegister
                  ? 'Use email and password for the first working version of FoodPilot authentication.'
                  : 'Sign in with the same email and password you registered with.'}
              </p>
            </div>

            <form className="space-y-5" onSubmit={handleSubmit}>
              {isRegister && (
                <Field label="Display name">
                  <input
                    className={INPUT_CLASSNAME}
                    value={displayName}
                    onChange={(event) => setDisplayName(event.target.value)}
                    placeholder="How FoodPilot should address you"
                    autoComplete="name"
                    disabled={isSubmitting}
                  />
                </Field>
              )}

              <Field label="Email">
                <input
                  className={INPUT_CLASSNAME}
                  type="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  placeholder="you@example.com"
                  autoComplete="email"
                  disabled={isSubmitting}
                />
              </Field>

              <Field label="Password">
                <input
                  className={INPUT_CLASSNAME}
                  type="password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  placeholder={isRegister ? 'At least 8 characters' : 'Enter your password'}
                  autoComplete={isRegister ? 'new-password' : 'current-password'}
                  disabled={isSubmitting}
                />
              </Field>

              {errorMessage && (
                <div className="rounded-[20px] border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-600">
                  {errorMessage}
                </div>
              )}

              <button
                type="submit"
                disabled={isSubmitting}
                className={`flex w-full items-center justify-center rounded-[20px] px-6 py-4 text-sm font-bold transition-all ${
                  isSubmitting
                    ? 'cursor-not-allowed bg-[#4A453E]/12 text-[#4A453E]/35'
                    : 'bg-[#FF8A65] text-white shadow-lg shadow-[#FF8A65]/20 hover:translate-y-[-1px] hover:bg-[#ff7d56]'
                }`}
              >
                {isSubmitting
                  ? 'Working...'
                  : isRegister
                    ? 'Create account'
                    : 'Sign in'}
              </button>
            </form>

            <p className="mt-6 text-sm text-[#4A453E]/45">
              {isRegister ? 'Already have an account?' : 'Need an account?'}{' '}
              <button
                type="button"
                onClick={() => onModeChange(isRegister ? 'login' : 'register')}
                className="font-bold text-[#FF8A65]"
              >
                {isRegister ? 'Sign in' : 'Create one'}
              </button>
            </p>
          </div>
        </section>
      </div>
    </div>
  );
};

interface FieldProps {
  label: string;
  children: React.ReactNode;
}

const Field: React.FC<FieldProps> = ({ label, children }) => {
  return (
    <label className="block">
      <span className="mb-2 block px-1 text-[10px] font-black uppercase tracking-[0.22em] text-[#4A453E]/40">
        {label}
      </span>
      {children}
    </label>
  );
};

interface InsightCardProps {
  eyebrow: string;
  title: string;
  body: string;
}

const InsightCard: React.FC<InsightCardProps> = ({ eyebrow, title, body }) => {
  return (
    <article className="rounded-[28px] border border-[#4A453E]/8 bg-white/75 p-5">
      <p className="text-[10px] font-black uppercase tracking-[0.24em] text-[#4A453E]/32">{eyebrow}</p>
      <h3 className="mt-3 text-lg font-bold text-[#4A453E]">{title}</h3>
      <p className="mt-2 text-sm leading-7 text-[#4A453E]/55">{body}</p>
    </article>
  );
};

function getErrorMessage(error: unknown): string {
  if (error instanceof AuthApiError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return 'Authentication failed. Please try again.';
}
