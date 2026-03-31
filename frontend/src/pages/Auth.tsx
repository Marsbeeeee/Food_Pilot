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
  'w-full rounded-[20px] border border-[#4A453E]/10 bg-white/90 px-5 py-4 text-[15px] font-medium text-[#4A453E] outline-none transition-all placeholder:text-[#4A453E]/25 focus:border-[#FF8A65]/40 focus:ring-4 focus:ring-[#FF8A65]/10';

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
    <div className="flex-1 overflow-y-auto bg-[radial-gradient(circle_at_top_left,_rgba(255,138,101,0.12),_transparent_34%),linear-gradient(135deg,#fffdf7_0%,#f8f3ea_50%,#f3ede2_100%)]">
      <div className="mx-auto flex min-h-full w-full max-w-6xl flex-col gap-10 px-6 py-12 lg:grid lg:grid-cols-[1.1fr_0.9fr] lg:items-start lg:px-10 lg:py-14">
        <section className="relative overflow-hidden rounded-[36px] border border-[#4A453E]/12 bg-[linear-gradient(165deg,rgba(255,255,255,0.95),rgba(255,248,240,0.92))] p-9 shadow-[0_28px_84px_rgba(74,69,62,0.12)] lg:p-12">
          <div className="pointer-events-none absolute -left-16 -top-16 size-40 rounded-full bg-[#FF8A65]/6 blur-3xl" />

          <div className="relative">
            <p className="mb-4 text-xs font-semibold tracking-[0.06em] text-[#FF8A65]">
              继续使用 Food Pilot
            </p>
            <h1 className="max-w-xl text-[2rem] font-bold leading-[1.22] text-[#4A453E] md:text-[2.55rem]">
              登录后继续你的助手与记录。
            </h1>
            <p className="mt-5 max-w-xl text-[15px] leading-7 text-[#4A453E]/68 md:text-[16px]">
              同一账号可同步聊天上下文、饮食记录和个人档案，换设备后也能无缝继续。
            </p>

            <div className="mt-10 space-y-3">
              <BenefitItem
                icon="forum"
                title="助手上下文更稳定"
                body="同一账号持续累积聊天背景，回复更连贯。"
              />
              <BenefitItem
                icon="receipt_long"
                title="饮食记录自动跟随账号"
                body="保存过的分析可跨设备查看，不再只留在当前浏览器。"
              />
              <BenefitItem
                icon="person"
                title="个人偏好持续生效"
                body="目标、过敏项和饮食偏好会随登录状态延续。"
              />
            </div>
          </div>
        </section>

        <section className="relative overflow-hidden rounded-[36px] border border-[#4A453E]/10 bg-[linear-gradient(180deg,rgba(255,255,255,0.98),rgba(255,252,247,0.96))] px-7 py-8 shadow-[0_24px_80px_rgba(74,69,62,0.12)] sm:px-9 lg:px-10 lg:py-9">
          <div className="relative">
            <div className="mb-7 inline-flex rounded-[18px] border border-[#4A453E]/8 bg-[#F7F3E9] p-1">
              <button
                onClick={() => onModeChange('login')}
                className={`rounded-[14px] px-5 py-2 text-sm font-semibold transition-all ${
                  mode === 'login'
                    ? 'bg-white text-[#4A453E] shadow-[0_6px_14px_rgba(74,69,62,0.08)]'
                    : 'text-[#4A453E]/45 hover:text-[#4A453E]'
                }`}
                type="button"
              >
                登录
              </button>
              <button
                onClick={() => onModeChange('register')}
                className={`rounded-[14px] px-5 py-2 text-sm font-semibold transition-all ${
                  mode === 'register'
                    ? 'bg-white text-[#4A453E] shadow-[0_6px_14px_rgba(74,69,62,0.08)]'
                    : 'text-[#4A453E]/45 hover:text-[#4A453E]'
                }`}
                type="button"
              >
                注册
              </button>
            </div>

            <div className="mb-8">
              <h2 className="font-serif-brand text-[1.85rem] font-bold leading-[1.2] text-[#4A453E]">
                {isRegister ? '创建账号' : '欢迎回来'}
              </h2>
              <p className="mt-3 text-[15px] leading-7 text-[#4A453E]/55">
                {isRegister
                  ? '注册后可同步个人档案与饮食记录，并让助手持续识别你的身份。'
                  : '请使用你在 Food Pilot 中使用的邮箱与密码登录。'}
              </p>
            </div>

            <form className="space-y-5" onSubmit={handleSubmit}>
              {isRegister && (
                <Field label="显示名称">
                  <input
                    className={INPUT_CLASSNAME}
                    value={displayName}
                    onChange={(event) => setDisplayName(event.target.value)}
                    placeholder="助手应如何称呼你"
                    autoComplete="name"
                    disabled={isSubmitting}
                  />
                </Field>
              )}

              <Field label="邮箱">
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

              <Field label="密码">
                <input
                  className={INPUT_CLASSNAME}
                  type="password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  placeholder={isRegister ? '至少 8 个字符' : '请输入密码'}
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
                  ? '处理中...'
                  : isRegister
                    ? '注册'
                    : '登录'}
              </button>
            </form>

            <p className="mt-6 text-sm text-[#4A453E]/45">
              {isRegister ? '已有账号？' : '还没有账号？'}{' '}
              <button
                type="button"
                onClick={() => onModeChange(isRegister ? 'login' : 'register')}
                className="font-bold text-[#FF8A65]"
              >
                {isRegister ? '登录' : '去注册'}
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
      <span className="mb-2 block px-1 text-[12px] font-semibold tracking-[0.04em] text-[#4A453E]/46">
        {label}
      </span>
      {children}
    </label>
  );
};

interface BenefitItemProps {
  icon: string;
  title: string;
  body: string;
}

const BenefitItem: React.FC<BenefitItemProps> = ({ icon, title, body }) => {
  return (
    <article className="flex items-start gap-3 rounded-[18px] border border-[#4A453E]/12 bg-white px-4 py-3.5 shadow-[0_8px_22px_rgba(74,69,62,0.06)]">
      <span className="mt-0.5 flex size-7 items-center justify-center rounded-full bg-[#FF8A65]/10 text-[#FF8A65]">
        <span className="material-symbols-outlined text-[17px] leading-none">{icon}</span>
      </span>
      <div>
        <h3 className="text-[16px] font-semibold leading-6 text-[#4A453E]">{title}</h3>
        <p className="mt-0.5 text-[14px] leading-6 text-[#4A453E]/58">{body}</p>
      </div>
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

  return '认证失败，请稍后重试。';
}
