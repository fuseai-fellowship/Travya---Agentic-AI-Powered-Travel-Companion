/** Mirrors the API's upload rules (backend `DocumentService.upload`). */
export const ACCEPTED_TYPES = ["application/pdf", "image/png", "image/jpeg", "image/webp"]
export const MAX_UPLOAD_BYTES = 10 * 1024 * 1024

export function validateUpload(file: File): string | null {
  if (!ACCEPTED_TYPES.includes(file.type)) return "Only PDF, PNG, JPEG and WebP files are accepted."
  if (file.size > MAX_UPLOAD_BYTES) return "Files can be at most 10 MB."
  return null
}
