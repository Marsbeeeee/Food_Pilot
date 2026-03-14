import React, { useEffect } from 'react';

interface ConfirmDialogProps {
  open: boolean;
  title: string;
  description: React.ReactNode;
  confirmLabel: string;
  cancelLabel?: string;
  icon?: string;
  isConfirming?: boolean;
  onClose: () => void;
  onConfirm: () => void;
}

export const ConfirmDialog: React.FC<ConfirmDialogProps> = ({
  open,
  title,
  description,
  confirmLabel,
  cancelLabel = 'Cancel',
  icon = 'warning',
  isConfirming = false,
  onClose,
  onConfirm,
}) => {
  useEffect(() => {
    if (!open) {
      return undefined;
    }

    const handleEscapeKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && !isConfirming) {
        onClose();
      }
    };

    document.addEventListener('keydown', handleEscapeKey);
    return () => document.removeEventListener('keydown', handleEscapeKey);
  }, [isConfirming, onClose, open]);

  if (!open) {
    return null;
  }

  return (
    <div
      className="fixed inset-0 z-[120] flex items-center justify-center bg-[#4A453E]/30 px-6"
      onClick={() => {
        if (!isConfirming) {
          onClose();
        }
      }}
    >
      <div
        className="w-full max-w-md rounded-[28px] border border-[#4A453E]/10 bg-[#FFFDF5] p-6 shadow-[0_28px_70px_rgba(74,69,62,0.18)]"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="mb-5 flex items-start gap-4">
          <div className="flex size-12 shrink-0 items-center justify-center rounded-[18px] border border-red-200 bg-red-50 text-red-500">
            <span className="material-symbols-outlined text-[22px]">{icon}</span>
          </div>
          <div className="min-w-0 flex-1">
            <h3 className="text-lg font-bold text-[#4A453E]">{title}</h3>
            <div className="mt-2 text-sm leading-7 text-[#4A453E]/55">
              {description}
            </div>
          </div>
        </div>

        <div className="flex justify-end gap-3">
          <button
            type="button"
            onClick={onClose}
            disabled={isConfirming}
            className="rounded-[14px] border border-[#4A453E]/10 bg-white px-4 py-2.5 text-sm font-semibold text-[#4A453E]/55 transition-colors hover:bg-[#F7F3E9] disabled:cursor-not-allowed disabled:opacity-70"
          >
            {cancelLabel}
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={isConfirming}
            className="rounded-[14px] bg-red-500 px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-red-500/15 transition-colors hover:bg-red-600 disabled:cursor-wait disabled:opacity-80"
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
};
