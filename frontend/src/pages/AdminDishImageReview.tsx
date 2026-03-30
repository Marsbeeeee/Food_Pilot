import React, { useEffect, useState } from 'react';

import {
  approveAdminDishImageCandidate,
  getAdminDishImageCandidate,
  listAdminDishImageCandidates,
  regenerateAdminDishImageCandidate,
  rejectAndRegenerateAdminDishImageCandidate,
  rejectAdminDishImageCandidate,
} from '../api/adminDishImages';
import {
  AdminDishImageCandidateDetail,
  AdminDishImageCandidateListItem,
  AdminDishImageStatus,
  AuthUser,
} from '../types/types';

interface AdminDishImageReviewPageProps {
  currentUser: AuthUser;
}

const STATUS_OPTIONS: Array<{ label: string; value: AdminDishImageStatus | '' }> = [
  { label: 'All', value: '' },
  { label: 'Pending', value: 'pending' },
  { label: 'Approved', value: 'approved' },
  { label: 'Rejected', value: 'rejected' },
];

export const AdminDishImageReviewPage: React.FC<AdminDishImageReviewPageProps> = ({
  currentUser,
}) => {
  const [items, setItems] = useState<AdminDishImageCandidateListItem[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [detail, setDetail] = useState<AdminDishImageCandidateDetail | null>(null);
  const [statusFilter, setStatusFilter] = useState<AdminDishImageStatus | ''>('pending');
  const [query, setQuery] = useState('');
  const [createdFrom, setCreatedFrom] = useState('');
  const [createdTo, setCreatedTo] = useState('');
  const [note, setNote] = useState('');
  const [listLoading, setListLoading] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState<
    'approve' | 'reject' | 'regenerate' | 'rejectRegenerate' | null
  >(null);
  const [listError, setListError] = useState<string | null>(null);
  const [detailError, setDetailError] = useState<string | null>(null);

  const loadCandidates = async (preferredId?: number | null) => {
    setListLoading(true);
    setListError(null);
    try {
      const nextItems = await listAdminDishImageCandidates({
        status: statusFilter || undefined,
        query: query.trim() || undefined,
        createdFrom: createdFrom || undefined,
        createdTo: createdTo || undefined,
        limit: 100,
      });
      setItems(nextItems);
      setSelectedId((current) => {
        const candidateId = preferredId ?? current;
        if (candidateId != null && nextItems.some((item) => item.id === candidateId)) {
          return candidateId;
        }
        return nextItems[0]?.id ?? null;
      });
    } catch (error) {
      setListError(getErrorMessage(error));
      setItems([]);
      setSelectedId(null);
    } finally {
      setListLoading(false);
    }
  };

  const loadDetail = async (dishImageId: number) => {
    setDetailLoading(true);
    setDetailError(null);
    try {
      const nextDetail = await getAdminDishImageCandidate(dishImageId);
      setDetail(nextDetail);
    } catch (error) {
      setDetail(null);
      setDetailError(getErrorMessage(error));
    } finally {
      setDetailLoading(false);
    }
  };

  useEffect(() => {
    void loadCandidates();
  }, [statusFilter, query, createdFrom, createdTo]);

  useEffect(() => {
    if (selectedId == null) {
      setDetail(null);
      return;
    }
    void loadDetail(selectedId);
  }, [selectedId]);

  const handleAction = async (action: 'approve' | 'reject' | 'regenerate' | 'rejectRegenerate') => {
    if (!detail || actionLoading) {
      return;
    }

    setActionLoading(action);
    setDetailError(null);
    try {
      const nextDetail = action === 'approve'
        ? await approveAdminDishImageCandidate(detail.id, note.trim() || undefined)
        : action === 'reject'
          ? await rejectAdminDishImageCandidate(detail.id, note.trim() || undefined)
          : action === 'regenerate'
            ? await regenerateAdminDishImageCandidate(detail.id, note.trim() || undefined)
            : await rejectAndRegenerateAdminDishImageCandidate(detail.id, note.trim() || undefined);
      setDetail(nextDetail);
      setNote('');
      await loadCandidates(nextDetail.id);
    } catch (error) {
      setDetailError(getErrorMessage(error));
    } finally {
      setActionLoading(null);
    }
  };

  if (!currentUser.isAdmin) {
    return (
      <div className="flex flex-1 items-center justify-center bg-[#FFFDF5] px-6 py-10">
        <div className="max-w-lg rounded-[32px] border border-[#4A453E]/10 bg-white px-8 py-10 text-center shadow-[0_24px_60px_rgba(74,69,62,0.08)]">
          <p className="text-[11px] font-black uppercase tracking-[0.28em] text-[#FF8A65]">
            Admin Only
          </p>
          <h1 className="mt-4 font-serif-brand text-3xl font-bold text-[#4A453E]">
            You do not have access to the dish image review console.
          </h1>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full min-h-0 flex-1 flex-col overflow-hidden bg-[radial-gradient(circle_at_top_left,_rgba(255,138,101,0.16),_transparent_30%),#FFFDF5] xl:flex-row">
      <aside className="custom-scrollbar w-full shrink-0 overflow-y-auto border-b border-[#4A453E]/8 bg-white/75 px-6 py-6 backdrop-blur-sm xl:w-[420px] xl:border-b-0 xl:border-r xl:px-7">
        <div className="mb-6">
          <p className="text-[10px] font-black uppercase tracking-[0.3em] text-[#FF8A65]">
            Internal Admin
          </p>
          <h1 className="mt-3 font-serif-brand text-3xl font-bold text-[#4A453E]">
            Dish Image Review
          </h1>
          <p className="mt-3 text-sm leading-7 text-[#4A453E]/60">
            Review AI-generated dish images before they become reusable official assets.
          </p>
        </div>

        <div className="space-y-4 rounded-[28px] border border-[#4A453E]/8 bg-[#FFFEFB] p-5 shadow-[0_18px_36px_rgba(74,69,62,0.06)]">
          <label className="block">
            <span className="mb-2 block text-[10px] font-black uppercase tracking-[0.2em] text-[#4A453E]/35">
              Dish Name
            </span>
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search standard dishes"
              className="w-full rounded-[18px] border border-[#4A453E]/10 bg-white px-4 py-3 text-sm font-semibold text-[#4A453E] outline-none transition-all focus:border-[#FF8A65]/45 focus:ring-4 focus:ring-[#FF8A65]/10"
            />
          </label>

          <div className="grid gap-4 sm:grid-cols-3 xl:grid-cols-1">
            <label className="block">
              <span className="mb-2 block text-[10px] font-black uppercase tracking-[0.2em] text-[#4A453E]/35">
                Status
              </span>
              <select
                value={statusFilter}
                onChange={(event) => setStatusFilter(event.target.value as AdminDishImageStatus | '')}
                className="w-full rounded-[18px] border border-[#4A453E]/10 bg-white px-4 py-3 text-sm font-semibold text-[#4A453E] outline-none transition-all focus:border-[#FF8A65]/45"
              >
                {STATUS_OPTIONS.map((option) => (
                  <option key={option.label} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>

            <label className="block">
              <span className="mb-2 block text-[10px] font-black uppercase tracking-[0.2em] text-[#4A453E]/35">
                Created From
              </span>
              <input
                type="date"
                value={createdFrom}
                onChange={(event) => setCreatedFrom(event.target.value)}
                className="w-full rounded-[18px] border border-[#4A453E]/10 bg-white px-4 py-3 text-sm font-semibold text-[#4A453E] outline-none transition-all focus:border-[#FF8A65]/45"
              />
            </label>

            <label className="block">
              <span className="mb-2 block text-[10px] font-black uppercase tracking-[0.2em] text-[#4A453E]/35">
                Created To
              </span>
              <input
                type="date"
                value={createdTo}
                onChange={(event) => setCreatedTo(event.target.value)}
                className="w-full rounded-[18px] border border-[#4A453E]/10 bg-white px-4 py-3 text-sm font-semibold text-[#4A453E] outline-none transition-all focus:border-[#FF8A65]/45"
              />
            </label>
          </div>
        </div>

        <div className="mt-6 flex items-center justify-between px-1">
          <p className="text-[10px] font-black uppercase tracking-[0.22em] text-[#4A453E]/35">
            Candidates
          </p>
          <button
            type="button"
            onClick={() => void loadCandidates(selectedId)}
            className="rounded-full bg-[#F7F3E9] px-3 py-1.5 text-[11px] font-bold text-[#4A453E]/65 transition-colors hover:bg-[#EFE7DA] hover:text-[#4A453E]"
          >
            Refresh
          </button>
        </div>

        <div className="mt-4 space-y-3">
          {listLoading && <PanelMessage text="Loading dish image candidates..." />}
          {!listLoading && listError && <PanelMessage text={listError} tone="error" />}
          {!listLoading && !listError && items.length === 0 && (
            <PanelMessage text="No dish image candidates match the current filters." />
          )}
          {!listLoading && !listError && items.map((item) => (
            <button
              key={item.id}
              type="button"
              onClick={() => setSelectedId(item.id)}
              className={`flex w-full items-start gap-4 rounded-[24px] border px-4 py-4 text-left transition-all ${
                selectedId === item.id
                  ? 'border-[#FF8A65]/40 bg-[#FFF3EA] shadow-[0_12px_24px_rgba(255,138,101,0.12)]'
                  : 'border-[#4A453E]/8 bg-white hover:border-[#FF8A65]/20 hover:bg-[#FFF9F3]'
              }`}
            >
              <img
                src={item.imageUrl}
                alt={item.standardDishName}
                className="h-20 w-20 shrink-0 rounded-[18px] border border-[#4A453E]/8 object-cover"
              />
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <StatusBadge status={item.status} />
                  {item.isCurrentOfficial && (
                    <span className="rounded-full bg-[#81C784]/12 px-2.5 py-1 text-[10px] font-black uppercase tracking-[0.18em] text-[#4D8C53]">
                      Official
                    </span>
                  )}
                </div>
                <h2 className="mt-3 truncate text-base font-bold text-[#4A453E]">
                  {item.standardDishName}
                </h2>
                <p className="mt-1 text-xs text-[#4A453E]/45">
                  Candidate #{item.id} · {formatTimestamp(item.createdAt)}
                </p>
              </div>
            </button>
          ))}
        </div>
      </aside>

      <main className="custom-scrollbar min-h-0 flex-1 overflow-y-auto px-6 py-6 md:px-8 xl:px-10">
        {detailLoading && <DetailState title="Loading review detail..." />}
        {!detailLoading && detailError && <DetailState title={detailError} tone="error" />}
        {!detailLoading && !detailError && !detail && (
          <DetailState title="Select a dish image candidate to review." />
        )}
        {!detailLoading && !detailError && detail && (
          <div className="mx-auto flex w-full max-w-6xl flex-col gap-6">
            <section className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
              <article className="overflow-hidden rounded-[32px] border border-[#4A453E]/8 bg-white shadow-[0_22px_50px_rgba(74,69,62,0.08)]">
                <div className="relative aspect-[4/3] bg-[#F7F3E9]">
                  <img
                    src={detail.imageUrl}
                    alt={detail.standardDishName}
                    className="h-full w-full object-cover"
                  />
                </div>
                <div className="border-t border-[#4A453E]/8 px-6 py-5">
                  <div className="flex flex-wrap items-center gap-2">
                    <StatusBadge status={detail.status} />
                    {detail.isCurrentOfficial && (
                      <span className="rounded-full bg-[#81C784]/12 px-3 py-1 text-[10px] font-black uppercase tracking-[0.18em] text-[#4D8C53]">
                        Current Official
                      </span>
                    )}
                  </div>
                  <h2 className="mt-4 font-serif-brand text-4xl font-bold text-[#4A453E]">
                    {detail.standardDishName}
                  </h2>
                  <div className="mt-4 grid gap-3 text-sm text-[#4A453E]/65 sm:grid-cols-2">
                    <MetaCard label="Candidate ID" value={`#${detail.id}`} />
                    <MetaCard label="Generated At" value={formatTimestamp(detail.createdAt)} />
                    <MetaCard label="Prompt Version" value={detail.promptVersion || 'Unknown'} />
                    <MetaCard label="Reviewed At" value={detail.reviewedAt ? formatTimestamp(detail.reviewedAt) : 'Not reviewed'} />
                  </div>
                </div>
              </article>

              <div className="space-y-6">
                <section className="rounded-[30px] border border-[#4A453E]/8 bg-white p-6 shadow-[0_18px_40px_rgba(74,69,62,0.06)]">
                  <p className="text-[10px] font-black uppercase tracking-[0.22em] text-[#4A453E]/35">
                    Official Asset
                  </p>
                  <div className="mt-4 overflow-hidden rounded-[24px] border border-[#4A453E]/8 bg-[#F7F3E9]">
                    {detail.officialImageUrl ? (
                      <img
                        src={detail.officialImageUrl}
                        alt={`${detail.standardDishName} official`}
                        className="h-48 w-full object-cover"
                      />
                    ) : (
                      <div className="flex h-48 items-center justify-center text-sm font-semibold text-[#4A453E]/45">
                        No official image yet
                      </div>
                    )}
                  </div>
                  <div className="mt-4 space-y-2 text-sm text-[#4A453E]/65">
                    <p>Status: {detail.officialImageStatus || 'none'}</p>
                    <p>Prompt version: {detail.officialImagePromptVersion || 'n/a'}</p>
                    <p>Last updated: {detail.officialImageUpdatedAt ? formatTimestamp(detail.officialImageUpdatedAt) : 'n/a'}</p>
                  </div>
                </section>

                <section className="rounded-[30px] border border-[#4A453E]/8 bg-white p-6 shadow-[0_18px_40px_rgba(74,69,62,0.06)]">
                  <div className="flex items-center justify-between">
                    <p className="text-[10px] font-black uppercase tracking-[0.22em] text-[#4A453E]/35">
                      Review Actions
                    </p>
                    <span className="rounded-full bg-[#F7F3E9] px-3 py-1 text-[11px] font-bold text-[#4A453E]/55">
                      {currentUser.displayName}
                    </span>
                  </div>
                  <textarea
                    value={note}
                    onChange={(event) => setNote(event.target.value)}
                    rows={4}
                    placeholder="Optional reviewer note"
                    className="mt-4 w-full rounded-[22px] border border-[#4A453E]/10 bg-[#FFFEFB] px-4 py-4 text-sm font-medium text-[#4A453E] outline-none transition-all focus:border-[#FF8A65]/45 focus:ring-4 focus:ring-[#FF8A65]/10"
                  />
                  <div className="mt-4 grid gap-3">
                    <ActionButton
                      label={actionLoading === 'approve' ? 'Approving...' : 'Approve Candidate'}
                      onClick={() => void handleAction('approve')}
                      disabled={!detail.canApprove || actionLoading !== null}
                      tone="approve"
                    />
                    <ActionButton
                      label={actionLoading === 'reject' ? 'Rejecting...' : 'Reject Candidate'}
                      onClick={() => void handleAction('reject')}
                      disabled={!detail.canReject || actionLoading !== null}
                      tone="reject"
                    />
                    {detail.canReject && detail.canRegenerate ? (
                      <ActionButton
                        label={actionLoading === 'rejectRegenerate' ? 'Rejecting and queueing...' : 'Reject & Regenerate'}
                        onClick={() => void handleAction('rejectRegenerate')}
                        disabled={actionLoading !== null}
                        tone="rejectRegenerate"
                      />
                    ) : (
                      <ActionButton
                        label={actionLoading === 'regenerate' ? 'Queueing regenerate...' : 'Regenerate'}
                        onClick={() => void handleAction('regenerate')}
                        disabled={!detail.canRegenerate || actionLoading !== null}
                        tone="regenerate"
                      />
                    )}
                  </div>
                </section>
              </div>
            </section>

            <section className="rounded-[30px] border border-[#4A453E]/8 bg-white p-6 shadow-[0_18px_40px_rgba(74,69,62,0.06)]">
              <p className="text-[10px] font-black uppercase tracking-[0.22em] text-[#4A453E]/35">
                Recent Operations
              </p>
              <div className="mt-5 space-y-4">
                {detail.recentOperations.length === 0 && (
                  <p className="text-sm text-[#4A453E]/55">No admin actions recorded yet.</p>
                )}
                {detail.recentOperations.map((operation) => (
                  <div
                    key={operation.id}
                    className="rounded-[22px] border border-[#4A453E]/8 bg-[#FFFEFB] px-5 py-4"
                  >
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="rounded-full bg-[#4A453E]/6 px-3 py-1 text-[10px] font-black uppercase tracking-[0.18em] text-[#4A453E]/70">
                        {operation.action}
                      </span>
                      <span className="text-sm font-bold text-[#4A453E]">{operation.actor.displayName}</span>
                      <span className="text-xs text-[#4A453E]/45">{operation.actor.email}</span>
                    </div>
                    <p className="mt-2 text-sm text-[#4A453E]/65">
                      Result: {operation.resultStatus} · {formatTimestamp(operation.createdAt)}
                    </p>
                    {operation.note && (
                      <p className="mt-2 text-sm leading-7 text-[#4A453E]/60">{operation.note}</p>
                    )}
                  </div>
                ))}
              </div>
            </section>
          </div>
        )}
      </main>
    </div>
  );
};

interface PanelMessageProps {
  text: string;
  tone?: 'default' | 'error';
}

const PanelMessage: React.FC<PanelMessageProps> = ({ text, tone = 'default' }) => (
  <div className={`rounded-[22px] border px-4 py-4 text-sm font-medium ${
    tone === 'error'
      ? 'border-red-200 bg-red-50 text-red-600'
      : 'border-[#4A453E]/8 bg-white text-[#4A453E]/55'
  }`}
  >
    {text}
  </div>
);

interface DetailStateProps {
  title: string;
  tone?: 'default' | 'error';
}

const DetailState: React.FC<DetailStateProps> = ({ title, tone = 'default' }) => (
  <div className={`mx-auto mt-12 max-w-2xl rounded-[32px] border px-8 py-12 text-center ${
    tone === 'error'
      ? 'border-red-200 bg-red-50 text-red-600'
      : 'border-[#4A453E]/8 bg-white text-[#4A453E]/60'
  }`}
  >
    <p className="text-lg font-bold">{title}</p>
  </div>
);

const StatusBadge: React.FC<{ status: AdminDishImageStatus }> = ({ status }) => {
  const className = status === 'pending'
    ? 'bg-[#FF8A65]/12 text-[#D7653F]'
    : status === 'approved'
      ? 'bg-[#81C784]/14 text-[#4D8C53]'
      : 'bg-[#E57373]/14 text-[#B84C4C]';
  return (
    <span className={`rounded-full px-3 py-1 text-[10px] font-black uppercase tracking-[0.18em] ${className}`}>
      {status}
    </span>
  );
};

const MetaCard: React.FC<{ label: string; value: string }> = ({ label, value }) => (
  <div className="rounded-[18px] border border-[#4A453E]/8 bg-[#FFFEFB] px-4 py-3">
    <p className="text-[10px] font-black uppercase tracking-[0.18em] text-[#4A453E]/35">{label}</p>
    <p className="mt-2 text-sm font-bold text-[#4A453E]">{value}</p>
  </div>
);

interface ActionButtonProps {
  label: string;
  onClick: () => void;
  disabled: boolean;
  tone: 'approve' | 'reject' | 'regenerate' | 'rejectRegenerate';
}

const ActionButton: React.FC<ActionButtonProps> = ({ label, onClick, disabled, tone }) => {
  const activeClassName = tone === 'approve'
    ? 'bg-[#81C784] text-white hover:bg-[#73b877]'
    : tone === 'reject'
      ? 'bg-[#E57373] text-white hover:bg-[#d86464]'
      : tone === 'rejectRegenerate'
        ? 'bg-[#FF8A65] text-white hover:bg-[#f07a54]'
        : 'bg-[#4A453E] text-white hover:bg-[#3d3934]';

  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={`rounded-[20px] px-5 py-3.5 text-sm font-bold transition-all ${
        disabled
          ? 'cursor-not-allowed bg-[#4A453E]/10 text-[#4A453E]/35'
          : activeClassName
      }`}
    >
      {label}
    </button>
  );
};

function formatTimestamp(value: string): string {
  const date = new Date(value.replace(' ', 'T'));
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString();
}

function getErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }
  return 'Unable to load dish image review data.';
}
