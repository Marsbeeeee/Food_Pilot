import React from 'react';

import { ChatScreenshotOcrResult } from '../types/types';

interface WorkspaceScreenshotOcrDialogProps {
  open: boolean;
  isParsing: boolean;
  previewUrl: string | null;
  parseResult: ChatScreenshotOcrResult | null;
  errorMessage: string;
  editableText: string;
  onChangeText: (value: string) => void;
  onClose: () => void;
  onRetry: () => void;
  onChooseFile: () => void;
  onConfirm: () => void;
}

export const WorkspaceScreenshotOcrDialog: React.FC<WorkspaceScreenshotOcrDialogProps> = ({
  open,
  isParsing,
  previewUrl,
  parseResult,
  errorMessage,
  editableText,
  onChangeText,
  onClose,
  onRetry,
  onChooseFile,
  onConfirm,
}) => {
  if (!open) {
    return null;
  }

  const isEmptyState = !isParsing && !previewUrl && !parseResult && !errorMessage && !editableText.trim();
  const failedMessage = errorMessage || (
    parseResult?.status === 'failed'
      ? parseResult.failureReason || '这张截图暂时没识别出稳定的商品主体。'
      : ''
  );
  const canConfirm = !isParsing && Boolean(editableText.trim()) && !failedMessage;

  return (
    <div
      className="fixed inset-0 z-[110] flex items-center justify-center bg-black/35 px-4 py-6"
      onClick={onClose}
    >
      <div
        className="flex max-h-[92vh] w-full max-w-4xl flex-col overflow-hidden rounded-[30px] border border-[#4A453E]/10 bg-[#FFFDF5] shadow-[0_30px_80px_rgba(74,69,62,0.2)]"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="border-b border-[#4A453E]/8 px-6 py-5 sm:px-7">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-[11px] font-bold uppercase tracking-[0.24em] text-[#C95B3A]">
                本地上传
              </p>
              <h3 className="mt-2 text-xl font-bold text-[#4A453E]">上传图片后识别商品信息</h3>
              <p className="mt-2 max-w-2xl text-sm leading-6 text-[#4A453E]/55">
                图片只用于本次识别，不默认长期保存原图。请先从本地选择图片，确认提取结果无误后，再进入点单决策。
              </p>
            </div>
            <button
              type="button"
              onClick={onClose}
              className="inline-flex size-10 items-center justify-center rounded-full border border-[#4A453E]/10 bg-white text-[#4A453E]/55 transition-colors hover:bg-[#F7F3E9]"
            >
              <span className="material-symbols-outlined text-[20px]">close</span>
            </button>
          </div>
        </div>

        <div className="custom-scrollbar grid min-h-0 flex-1 gap-0 overflow-y-auto lg:grid-cols-[1.05fr_1fr]">
          <div className="border-b border-[#4A453E]/8 bg-[#F7F3E9]/45 p-5 lg:border-b-0 lg:border-r">
            <div className="overflow-hidden rounded-[24px] border border-[#4A453E]/8 bg-white">
              {previewUrl ? (
                <img
                  src={previewUrl}
                  alt="截图预览"
                  className="max-h-[56vh] w-full object-contain"
                />
              ) : (
                <div className="flex min-h-[220px] items-center justify-center text-sm text-[#4A453E]/40">
                  暂无截图预览
                </div>
              )}
            </div>
          </div>

          <div className="flex min-h-0 flex-col p-5 sm:p-6">
            {isParsing ? (
              <div className="flex flex-1 flex-col items-center justify-center text-center">
                <div className="flex gap-2">
                  <span className="size-2.5 animate-bounce rounded-full bg-[#FF8A65] [animation-delay:-0.3s]"></span>
                  <span className="size-2.5 animate-bounce rounded-full bg-[#FF8A65] [animation-delay:-0.15s]"></span>
                  <span className="size-2.5 animate-bounce rounded-full bg-[#FF8A65]"></span>
                </div>
                <p className="mt-5 text-base font-semibold text-[#4A453E]">正在识别截图里的商品主体</p>
                <p className="mt-2 text-sm leading-6 text-[#4A453E]/50">
                  我会尽量忽略平台壳子、促销文案和页面噪声，只保留适合继续点单决策的文本。
                </p>
              </div>
            ) : isEmptyState ? (
              <div className="flex flex-1 flex-col items-center justify-center text-center">
                <div className="flex size-16 items-center justify-center rounded-[22px] border border-[#FF8A65]/20 bg-[#FFF1EB] text-[#FF8A65]">
                  <span className="material-symbols-outlined text-[30px]">upload_file</span>
                </div>
                <p className="mt-5 text-base font-semibold text-[#4A453E]">先从本地上传一张图片</p>
                <p className="mt-2 max-w-md text-sm leading-6 text-[#4A453E]/55">
                  支持 PNG、JPEG 和 WebP，大小不超过 5MB。选择本地图片后会先展示识别结果，你确认无误后再继续进入点单决策。
                </p>
                <button
                  type="button"
                  onClick={onChooseFile}
                  className="mt-6 inline-flex items-center gap-2 rounded-[16px] bg-[#FF8A65] px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-[#F77C55]"
                >
                  <span className="material-symbols-outlined text-[18px]">add_photo_alternate</span>
                  选择本地图片
                </button>
              </div>
            ) : failedMessage ? (
              <div className="flex flex-1 flex-col justify-center">
                <div className="rounded-[24px] border border-[#E5C1A5] bg-[#FFF7F1] p-5">
                  <p className="text-sm font-bold text-[#B85B31]">这张截图暂时不能直接进入决策</p>
                  <p className="mt-3 text-sm leading-6 text-[#7A5543]">{failedMessage}</p>
                  {parseResult?.warnings?.length ? (
                    <div className="mt-4 space-y-2">
                      {parseResult.warnings.map((warning) => (
                        <p key={warning} className="text-xs leading-5 text-[#7A5543]/80">
                          {warning}
                        </p>
                      ))}
                    </div>
                  ) : null}
                </div>
              </div>
            ) : (
              <div className="flex min-h-0 flex-1 flex-col">
                <div className="flex flex-wrap gap-2">
                  <span className="rounded-full border border-[#4A453E]/10 bg-white px-3 py-1 text-[11px] font-semibold text-[#4A453E]/65">
                    文件：{parseResult?.fileName}
                  </span>
                  <span className="rounded-full border border-[#FF8A65]/20 bg-[#FFF1EB] px-3 py-1 text-[11px] font-semibold text-[#C95B3A]">
                    置信度：{mapConfidenceLabel(parseResult?.confidenceLevel)}
                  </span>
                  {parseResult?.brandCandidate ? (
                    <span className="rounded-full border border-[#4A453E]/10 bg-white px-3 py-1 text-[11px] font-semibold text-[#4A453E]/65">
                      品牌：{parseResult.brandCandidate}
                    </span>
                  ) : null}
                  {parseResult?.specCandidate ? (
                    <span className="rounded-full border border-[#4A453E]/10 bg-white px-3 py-1 text-[11px] font-semibold text-[#4A453E]/65">
                      规格：{parseResult.specCandidate}
                    </span>
                  ) : null}
                </div>

                <label className="mt-5 block text-sm font-bold text-[#4A453E]">
                  可编辑确认文本
                  <textarea
                    value={editableText}
                    onChange={(event) => onChangeText(event.target.value)}
                    className="custom-scrollbar mt-3 min-h-[150px] w-full resize-y rounded-[22px] border border-[#4A453E]/10 bg-white px-4 py-4 text-sm leading-6 text-[#4A453E] outline-none transition-all focus:border-[#FF8A65]/30 focus:ring-2 focus:ring-[#FF8A65]/10"
                    placeholder="确认或修正识别结果后，再继续点单决策"
                  />
                </label>

                {parseResult?.candidateTitles?.length ? (
                  <div className="mt-4">
                    <p className="text-xs font-bold uppercase tracking-[0.2em] text-[#4A453E]/35">候选商品</p>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {parseResult.candidateTitles.map((candidate) => (
                        <button
                          key={candidate}
                          type="button"
                          onClick={() => onChangeText(candidate)}
                          className="rounded-full border border-[#4A453E]/10 bg-white px-3 py-1.5 text-xs font-semibold text-[#4A453E]/70 transition-colors hover:bg-[#F7F3E9]"
                        >
                          {candidate}
                        </button>
                      ))}
                    </div>
                  </div>
                ) : null}

                {parseResult?.recognizedText ? (
                  <div className="mt-4 rounded-[22px] border border-[#4A453E]/8 bg-white px-4 py-4">
                    <p className="text-xs font-bold uppercase tracking-[0.2em] text-[#4A453E]/35">识别到的主体文本</p>
                    <p className="mt-2 text-sm leading-6 text-[#4A453E]/65">{parseResult.recognizedText}</p>
                  </div>
                ) : null}

                {parseResult?.warnings?.length ? (
                  <div className="mt-4 space-y-2">
                    {parseResult.warnings.map((warning) => (
                      <p key={warning} className="text-xs leading-5 text-[#4A453E]/55">
                        {warning}
                      </p>
                    ))}
                  </div>
                ) : null}
              </div>
            )}
          </div>
        </div>

        <div className="flex items-center justify-end gap-3 border-t border-[#4A453E]/8 bg-white px-5 py-4 sm:px-6">
          <button
            type="button"
            onClick={onRetry}
            className="ml-auto rounded-[16px] border border-[#4A453E]/10 bg-white px-4 py-2.5 text-sm font-semibold text-[#4A453E]/70 transition-colors hover:bg-[#F7F3E9]"
          >
            重新上传
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={!canConfirm}
            className={`${canConfirm ? '' : 'hidden '}rounded-[16px] px-4 py-2.5 text-sm font-semibold text-white transition-colors ${
              canConfirm
                ? 'bg-[#FF8A65] hover:bg-[#F77C55]'
                : 'cursor-not-allowed bg-[#4A453E]/18'
            }`}
          >
            确认并继续决策
          </button>
        </div>
      </div>
    </div>
  );
};

function mapConfidenceLabel(value?: string | null): string {
  if (value === 'high') {
    return '高';
  }
  if (value === 'medium') {
    return '中';
  }
  if (value === 'low') {
    return '低';
  }
  return '待确认';
}
