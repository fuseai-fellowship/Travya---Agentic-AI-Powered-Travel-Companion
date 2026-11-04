import { screen } from "@testing-library/react"
import { describe, expect, it } from "vitest"
import { renderWithTheme } from "@/test/render"
import { Markdown } from "./Markdown"

describe("Markdown", () => {
  it("renders formatting and opens links safely", () => {
    renderWithTheme(
      <Markdown>{"**Bold** and [Wikivoyage](https://en.wikivoyage.org/wiki/Kathmandu)"}</Markdown>,
    )
    expect(screen.getByText("Bold").tagName).toBe("STRONG")
    const link = screen.getByRole("link", { name: "Wikivoyage" })
    expect(link).toHaveAttribute("target", "_blank")
    expect(link).toHaveAttribute("rel", expect.stringContaining("noopener"))
  })

  it("keeps script and event-handler payloads inert", () => {
    const payload = [
      "<script>window.__pwned = true</script>",
      '<img src="x" onerror="window.__pwned = true">',
      "[click](javascript:window.__pwned=true)",
      '<a href="#" onclick="window.__pwned = true">raw link</a>',
    ].join("\n\n")
    const { container } = renderWithTheme(<Markdown>{payload}</Markdown>)

    expect(container.querySelector("script")).toBeNull()
    expect(container.querySelector("[onerror]")).toBeNull()
    expect(container.querySelector("[onclick]")).toBeNull()
    for (const anchor of container.querySelectorAll("a")) {
      expect(anchor.getAttribute("href") ?? "").not.toMatch(/^javascript:/i)
    }
    expect((window as { __pwned?: boolean }).__pwned).toBeUndefined()
  })
})
