import { documentsDownloadDocument } from "@/client/sdk.gen"

/**
 * `GET /documents/{id}/download` answers with a signed URL (`DownloadLink`, cloud storage) or the
 * file bytes themselves (local storage). Handle both.
 */
export async function downloadDocument(documentId: string, filename: string): Promise<void> {
  const { data } = await documentsDownloadDocument({
    path: { document_id: documentId },
    parseAs: "auto",
    throwOnError: true,
  })
  const payload = data as unknown
  if (payload instanceof Blob) {
    const url = URL.createObjectURL(payload)
    const link = document.createElement("a")
    link.href = url
    link.download = filename
    document.body.append(link)
    link.click()
    link.remove()
    window.setTimeout(() => URL.revokeObjectURL(url), 30_000)
    return
  }
  const link = payload as { url?: unknown }
  if (typeof link?.url === "string") {
    // After an await the click no longer counts as a user gesture, so a popup would be blocked.
    // The signed URL answers with Content-Disposition: attachment, so following it in place
    // downloads the file without leaving the page.
    const anchor = document.createElement("a")
    anchor.href = link.url
    anchor.download = filename
    anchor.rel = "noopener"
    document.body.append(anchor)
    anchor.click()
    anchor.remove()
    return
  }
  throw new Error("The download link was missing.")
}
