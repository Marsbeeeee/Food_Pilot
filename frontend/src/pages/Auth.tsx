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
    <div className="flex-1 overflow-y-auto bg-[radial-gradient(circle_at_top_left,_rgba(255,138,101,0.2),_transparent_38%),linear-gradient(135deg,#fffdf5_0%,#f7f3e9_48%,#f1ebde_100%)]">
      <div className="mx-auto flex min-h-full w-full max-w-6xl flex-col gap-12 px-6 py-12 lg:grid lg:grid-cols-[1.1fr_0.9fr] lg:items-center lg:px-10 lg:py-16">
        <section className="rounded-[36px] border border-white/70 bg-white/50 p-9 shadow-[0_24px_80px_rgba(74,69,62,0.08)] backdrop-blur-sm lg:p-12">
          <p className="mb-4 text-[10px] font-bold uppercase tracking-[0.24em] text-[#FF8A65]">
            Food Pilot 账号
          </p>
          <h1 className="max-w-xl font-serif-brand text-[2.8rem] font-bold leading-[1.18] text-[#4A453E] md:text-5xl">
            让助手、饮食记录和个人档案保持同步。
          </h1>
          <p className="mt-6 max-w-xl text-[15px] leading-8 text-[#4A453E]/70 md:text-[17px]">
            登录后可恢复你的聊天、饮食记录和个人档案，让助手按正确上下文继续为你服务。
          </p>

          <div className="mt-12 grid gap-5 sm:grid-cols-3">
            <InsightCard
              eyebrow="助手"
              title="回复更连贯"
              body="登录后，助手每次都能读取同一份账号与档案上下文，回复更稳定。"
            />
            <InsightCard
              eyebrow="饮食记录"
              title="已保存记录随账号同步"
              body="你保存到饮食记录的分析会随账号加载，不再只留在当前设备。"
            />
            <InsightCard
              eyebrow="个人档案"
              title="个性化设置可延续"
              body="目标、过敏项和饮食偏好会随会话恢复，无需每次重新填写。"
            />
          </div>
        </section>

        <section className="relative overflow-hidden rounded-[36px] border border-[#4A453E]/10 bg-white px-7 py-9 shadow-[0_24px_80px_rgba(74,69,62,0.12)] sm:px-9 lg:px-10 lg:py-11">
          <div className="absolute inset-x-0 top-0 h-24 bg-[linear-gradient(90deg,rgba(255,138,101,0.16),rgba(129,199,132,0.12),transparent)]" />

          <div className="relative">
            <div className="mb-10 inline-flex rounded-full bg-[#F7F3E9] p-1">
              <button
                onClick={() => onModeChange('login')}
                className={`rounded-full px-5 py-2 text-sm font-bold transition-all ${
                  mode === 'login'
                    ? 'bg-white text-[#4A453E] shadow-sm'
                    : 'text-[#4A453E]/45 hover:text-[#4A453E]'
                }`}
                type="button"
              >
                登录
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
                注册
              </button>
            </div>

            <div className="mb-10">
              <h2 className="font-serif-brand text-[2rem] font-bold leading-[1.22] text-[#4A453E]">
                {isRegister ? '创建账号' : '欢迎回来'}
              </h2>
              <p className="mt-3 text-[15px] leading-8 text-[#4A453E]/55">
                {isRegister
                  ? '注册账号后可保存个人档案、绑定你的饮食记录，并让助手持续识别你的身份。'
                  : '请使用你在聊天、饮食记录和个人档案中使用的同一邮箱与密码登录。'}
              </p>
            </div>

            <form className="space-y-6" onSubmit={handleSubmit}>
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
      <span className="mb-2 block px-1 text-[10px] font-bold uppercase tracking-[0.16em] text-[#4A453E]/40">
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
    <article className="rounded-[28px] border border-[#4A453E]/8 bg-white/75 p-6">
      <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-[#4A453E]/32">{eyebrow}</p>
      <h3 className="mt-3 font-serif-brand text-[22px] font-bold leading-[1.28] text-[#4A453E] break-words">{title}</h3>
      <p className="mt-3 text-[15px] leading-7 text-[#4A453E]/55">{body}</p>
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
