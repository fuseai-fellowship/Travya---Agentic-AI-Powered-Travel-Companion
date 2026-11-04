/** Formatting helpers. Dates from the API are ISO `YYYY-MM-DD` calendar days (no time zone). */

const DAY_MS = 86_400_000

/** Parses a calendar day as local midnight so it never shifts across time zones. */
export function parseDay(day: string): Date {
  const [y, m, d] = day.split("-").map(Number)
  return new Date(y ?? 1970, (m ?? 1) - 1, d ?? 1)
}

export function toDayString(date: Date): string {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, "0")
  const d = String(date.getDate()).padStart(2, "0")
  return `${y}-${m}-${d}`
}

export function addDays(day: string, days: number): string {
  const date = parseDay(day)
  date.setDate(date.getDate() + days)
  return toDayString(date)
}

/** Whole calendar days from `from` to `to` (can be negative). */
export function daysBetween(from: string, to: string): number {
  return Math.round((parseDay(to).getTime() - parseDay(from).getTime()) / DAY_MS)
}

export function tripLength(start: string, end: string): number {
  return daysBetween(start, end) + 1
}

export function formatDay(day: string, options: Intl.DateTimeFormatOptions = {}): string {
  return parseDay(day).toLocaleDateString(undefined, {
    weekday: "short",
    day: "numeric",
    month: "short",
    ...options,
  })
}

export function formatDateRange(start: string, end: string): string {
  const a = parseDay(start)
  const b = parseDay(end)
  const sameYear = a.getFullYear() === b.getFullYear()
  const first = a.toLocaleDateString(undefined, {
    day: "numeric",
    month: "short",
    ...(sameYear ? {} : { year: "numeric" }),
  })
  const last = b.toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" })
  return start === end ? last : `${first} – ${last}`
}

/** "in 23 days", "tomorrow", "today", "ongoing", "ended 3 days ago". */
export function countdown(
  start: string,
  end: string,
  today: string = toDayString(new Date()),
): string {
  const untilStart = daysBetween(today, start)
  if (untilStart > 1) return `in ${untilStart} days`
  if (untilStart === 1) return "tomorrow"
  if (untilStart === 0) return "starts today"
  const sinceEnd = daysBetween(end, today)
  if (sinceEnd <= 0) return "ongoing"
  return sinceEnd === 1 ? "ended yesterday" : `ended ${sinceEnd} days ago`
}

export function formatMoney(
  amount: number,
  currency: string,
  options: { compact?: boolean } = {},
): string {
  try {
    return new Intl.NumberFormat(undefined, {
      style: "currency",
      currency,
      maximumFractionDigits: options.compact || Math.abs(amount) >= 1000 ? 0 : 2,
      minimumFractionDigits: 0,
    }).format(amount)
  } catch {
    return `${amount.toFixed(0)} ${currency}`
  }
}

/** Decimal strings from the API ("1240.00") to numbers; null for missing or malformed values. */
export function toNumber(value: string | number | null | undefined): number | null {
  if (value === null || value === undefined || value === "") return null
  const parsed = typeof value === "number" ? value : Number(value)
  return Number.isFinite(parsed) ? parsed : null
}

/** "09:30:00" → "09:30". */
export function formatTime(value: string | null | undefined): string | null {
  return value ? value.slice(0, 5) : null
}

export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export function formatElapsed(ms: number): string {
  const seconds = ms / 1000
  if (seconds < 10) return `${seconds.toFixed(1)} s`
  if (seconds < 60) return `${Math.round(seconds)} s`
  return `${Math.floor(seconds / 60)} min ${Math.round(seconds % 60)} s`
}

const RELATIVE = new Intl.RelativeTimeFormat(undefined, { numeric: "auto" })

export function formatRelative(iso: string, now: number = Date.now()): string {
  const diff = (new Date(iso).getTime() - now) / 1000
  const abs = Math.abs(diff)
  if (abs < 60) return "just now"
  if (abs < 3600) return RELATIVE.format(Math.round(diff / 60), "minute")
  if (abs < 86_400) return RELATIVE.format(Math.round(diff / 3600), "hour")
  if (abs < 86_400 * 7) return RELATIVE.format(Math.round(diff / 86_400), "day")
  return new Date(iso).toLocaleDateString(undefined, { day: "numeric", month: "short" })
}

export function plural(count: number, one: string, many = `${one}s`): string {
  return `${count} ${count === 1 ? one : many}`
}
