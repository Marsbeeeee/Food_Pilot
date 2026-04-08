export const WORKSPACE_SCREENSHOT_OCR_MAX_BYTES = 5 * 1024 * 1024;
export const WORKSPACE_SCREENSHOT_OCR_SUPPORTED_TYPES = [
  'image/png',
  'image/jpeg',
  'image/webp',
];

export function validateWorkspaceScreenshotFile(file) {
  if (!file) {
    return '请先选择一张截图。';
  }

  const fileType = typeof file.type === 'string' ? file.type.trim().toLowerCase() : '';
  if (!WORKSPACE_SCREENSHOT_OCR_SUPPORTED_TYPES.includes(fileType)) {
    return '当前仅支持 PNG、JPEG 和 WebP 截图。';
  }

  const fileSize = typeof file.size === 'number' ? file.size : 0;
  if (fileSize <= 0) {
    return '截图内容为空，请重新选择图片。';
  }

  if (fileSize > WORKSPACE_SCREENSHOT_OCR_MAX_BYTES) {
    return '截图不能超过 5MB，请压缩后重试。';
  }

  return '';
}

export function resolveWorkspaceScreenshotConfirmationText(result) {
  const normalizedInput = normalizeWhitespace(result?.normalizedInput);
  if (normalizedInput) {
    return normalizedInput;
  }

  const primaryText = normalizeWhitespace(result?.primaryText);
  if (primaryText) {
    return primaryText;
  }

  const firstCandidate = Array.isArray(result?.candidateTitles) ? result.candidateTitles[0] : '';
  return normalizeWhitespace(firstCandidate);
}

function normalizeWhitespace(value) {
  return typeof value === 'string' ? value.trim().replace(/\s+/g, ' ') : '';
}
