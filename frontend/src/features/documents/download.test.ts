import { afterEach, describe, expect, it, vi } from "vitest"
import { downloadDocument } from "./download"

const sdk = vi.hoisted(() => ({ documentsDownloadDocument: vi.fn() }))
vi.mock("@/client/sdk.gen", () => sdk)

afterEach(() => vi.restoreAllMocks())

describe("downloadDocument", () => {
  it("follows a signed URL with a link click instead of a popup that would be blocked", async () => {
    sdk.documentsDownloadDocument.mockResolvedValue({
      data: { url: "https://storage.test/e-ticket.pdf?sig=1" },
    })
    const open = vi.spyOn(window, "open").mockReturnValue(null)
    const clicked: HTMLAnchorElement[] = []
    vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(function (
      this: HTMLAnchorElement,
    ) {
      clicked.push(this)
    })
    await downloadDocument("doc-1", "e-ticket.pdf")
    expect(open).not.toHaveBeenCalled()
    expect(clicked).toHaveLength(1)
    expect(clicked[0]?.href).toBe("https://storage.test/e-ticket.pdf?sig=1")
    expect(clicked[0]?.download).toBe("e-ticket.pdf")
    expect(document.querySelector("a[download]")).toBeNull() // cleaned up
  })
})
