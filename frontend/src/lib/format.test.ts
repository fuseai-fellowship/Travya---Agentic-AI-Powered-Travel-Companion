import { describe, expect, it } from "vitest"
import { validateUpload } from "@/features/documents/upload"
import {
  addDays,
  countdown,
  daysBetween,
  formatElapsed,
  formatTime,
  toNumber,
  tripLength,
} from "./format"

describe("dates", () => {
  it("counts calendar days without time zone drift", () => {
    expect(daysBetween("2026-03-28", "2026-03-30")).toBe(2) // spans a DST change in Europe
    expect(tripLength("2026-12-01", "2026-12-21")).toBe(21)
    expect(addDays("2026-12-31", 1)).toBe("2027-01-01")
  })

  it("describes when a trip happens", () => {
    const today = "2026-11-05"
    expect(countdown("2026-11-28", "2026-12-01", today)).toBe("in 23 days")
    expect(countdown("2026-11-06", "2026-11-08", today)).toBe("tomorrow")
    expect(countdown("2026-11-05", "2026-11-08", today)).toBe("starts today")
    expect(countdown("2026-11-01", "2026-11-08", today)).toBe("ongoing")
    expect(countdown("2026-10-01", "2026-10-04", today)).toBe("ended 32 days ago")
  })
})

describe("numbers", () => {
  it("parses API decimals", () => {
    expect(toNumber("1240.50")).toBe(1240.5)
    expect(toNumber(null)).toBeNull()
    expect(toNumber("abc")).toBeNull()
  })

  it("formats times and durations", () => {
    expect(formatTime("09:30:00")).toBe("09:30")
    expect(formatElapsed(2400)).toBe("2.4\u00a0s")
    expect(formatElapsed(75_000)).toBe("1\u00a0min 15\u00a0s")
  })
})

describe("validateUpload", () => {
  it("accepts the API's file types up to 10 MB", () => {
    expect(validateUpload(new File(["%PDF"], "ticket.pdf", { type: "application/pdf" }))).toBeNull()
    expect(validateUpload(new File(["x"], "notes.txt", { type: "text/plain" }))).toMatch(/Only PDF/)
    const big = new File([new Uint8Array(10 * 1024 * 1024 + 1)], "scan.png", { type: "image/png" })
    expect(validateUpload(big)).toMatch(/10 MB/)
  })
})
