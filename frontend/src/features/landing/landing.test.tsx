import { act, fireEvent, screen, within } from "@testing-library/react"
import { afterEach, beforeEach, describe, expect, it } from "vitest"
import { renderWithTheme } from "@/test/render"
import { Gallery } from "./Gallery"
import { Guardrails } from "./Guardrails"
import { HowItWorks } from "./HowItWorks"
import { LandingFooter } from "./LandingFooter"
import { LINKS } from "./links"
import { ProofRow } from "./ProofRow"
import { RunReplay } from "./RunReplay"
import { setReplayElapsed } from "./replayClock"
import { GALLERY, HERO_RUN, recordedOn } from "./runs"

const realMatchMedia = window.matchMedia

function prefersReducedMotion(reduce: boolean) {
  window.matchMedia = (query: string) =>
    ({
      matches: reduce && query.includes("prefers-reduced-motion"),
      media: query,
      onchange: null,
      addEventListener: () => undefined,
      removeEventListener: () => undefined,
      addListener: () => undefined,
      removeListener: () => undefined,
      dispatchEvent: () => false,
    }) as MediaQueryList
}

afterEach(() => {
  window.matchMedia = realMatchMedia
  act(() => setReplayElapsed(0))
})

describe("recorded runs", () => {
  it("are real event streams in time order, with no ids", () => {
    for (const run of [HERO_RUN, ...GALLERY]) {
      const raw = JSON.stringify(run)
      expect(raw).not.toMatch(/trip_id|item_id|[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}/)
    }
    const offsets = HERO_RUN.events.map(([at]) => at)
    expect(offsets).toEqual([...offsets].sort((a, b) => a - b))
    expect(HERO_RUN.events.at(-1)?.[1]).toMatchObject({ agent: "travya", kind: "done" })
    expect(HERO_RUN.durationMs).toBe(offsets.at(-1))
    expect(recordedOn("2026-11-05T19:07:17Z")).toBe("5 Nov 2026")
  })
})

describe("RunReplay", () => {
  beforeEach(() => prefersReducedMotion(true))

  it("shows the finished run without motion, labelled as a real recording", () => {
    renderWithTheme(<RunReplay />)
    const figure = screen.getByRole("figure", { name: /Recorded planning run: Kyoto, 6 days/ })
    expect(figure).toHaveTextContent("real speed")
    expect(within(figure).getByRole("heading", { name: "Your 6-day itinerary is ready." }))
    expect(screen.getByRole("button", { name: "Play the replay" })).toBeInTheDocument()
    expect(screen.getByRole("img", { name: /14 planned stops/ })).toBeInTheDocument()
  })

  it("seeks through the recording, critic issues included", () => {
    renderWithTheme(<RunReplay />)
    fireEvent.change(screen.getByRole("slider", { name: "Position in the recorded run" }), {
      target: { value: "20500" },
    })
    expect(screen.getByText("Found 5 thing(s) to improve.")).toBeInTheDocument()
    expect(screen.getByText(/Nishiki Market shops generally do not open/)).toBeInTheDocument()
    expect(screen.getByRole("img", { name: /showing 40 places the scouts found/ })).toBeVisible()
  })

  it("plays and pauses", () => {
    prefersReducedMotion(false)
    renderWithTheme(<RunReplay />)
    const pause = screen.getByRole("button", { name: "Pause the replay" })
    fireEvent.click(pause)
    expect(screen.getByRole("button", { name: "Play the replay" })).toBeInTheDocument()
  })
})

describe("HowItWorks", () => {
  it("follows the replay: stations report their state", () => {
    renderWithTheme(<HowItWorks />)
    expect(screen.getAllByText(/\(waiting in the replay\)/)).toHaveLength(10)
    act(() => setReplayElapsed(HERO_RUN.durationMs))
    expect(screen.getByText("Your 6-day itinerary is ready.", { exact: false })).toBeInTheDocument()
    expect(screen.getAllByText(/\(done in the replay\)/)).toHaveLength(9)
    expect(screen.getByText(/\(working in the replay\)/).closest("p")).toHaveTextContent("You")
  })
})

describe("proof and credits", () => {
  it("links every number to the eval method", () => {
    renderWithTheme(<ProofRow />)
    expect(screen.getByText("plans pass every hard check")).toBeInTheDocument()
    expect(screen.getByRole("link", { name: "Method and reports" })).toHaveAttribute(
      "href",
      LINKS.evals,
    )
  })

  it("shows three real plans with sample prices and Nepali names from OSM", () => {
    renderWithTheme(<Gallery />)
    for (const name of ["Kathmandu", "Lisbon", "Kyoto"])
      expect(screen.getByRole("heading", { level: 3, name: new RegExp(name) })).toBeInTheDocument()
    expect(screen.getByText("काठमाडौँ")).toHaveAttribute("lang", "ne")
    expect(screen.getAllByText(/sample prices in/)).toHaveLength(3)
  })

  it("points engineers at the code", () => {
    renderWithTheme(<Guardrails />)
    expect(
      screen.getByRole("link", { name: "backend/app/agents/planning/checks.py" }),
    ).toHaveAttribute("href", LINKS.checks)
  })

  it("credits data sources, keeps the sponsor link quiet", () => {
    renderWithTheme(<LandingFooter />)
    expect(screen.getByRole("link", { name: /OpenStreetMap contributors/ })).toBeInTheDocument()
    expect(screen.getByRole("link", { name: /Wikivoyage, CC BY-SA/ })).toBeInTheDocument()
    expect(screen.getByText("Sponsor: not set up yet")).toBeInTheDocument()
    expect(screen.getByText(/Early UI by Bigya/)).toBeInTheDocument()
  })
})

describe("RealRunVideo", () => {
  it("is click to play, muted, captioned, and never preloads the whole file", async () => {
    prefersReducedMotion(false)
    const { RealRunVideo } = await import("./RealRunVideo")
    const { container } = renderWithTheme(<RealRunVideo />)
    const video = container.querySelector("video")
    expect(video).not.toBeNull()
    expect(video?.autoplay).toBe(false)
    expect(video?.muted).toBe(true)
    expect(video?.getAttribute("preload")).toBe("metadata")
    expect(video?.getAttribute("poster")).toBeTruthy()
    expect(container.querySelector('track[kind="captions"]')).not.toBeNull()
    expect(screen.getByRole("button", { name: "Play the 20-second video" })).toBeInTheDocument()
  })

  it("shows only the poster under reduced motion", async () => {
    prefersReducedMotion(true)
    const { RealRunVideo } = await import("./RealRunVideo")
    const { container } = renderWithTheme(<RealRunVideo />)
    expect(container.querySelector("video")).toBeNull()
    expect(screen.getByRole("img", { name: /trip page after planning Kathmandu/ })).toBeVisible()
  })
})
