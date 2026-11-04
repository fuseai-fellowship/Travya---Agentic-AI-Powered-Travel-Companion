export const NOTE_COLORS = ["yellow", "pink", "blue", "green", "purple", "orange"] as const
export type NoteColor = (typeof NOTE_COLORS)[number]

/** Paper tones for light mode and muted ones for dark mode; ink stays ≥ 4.5:1 on both. */
export const NOTE_TONES: Record<NoteColor, { light: string; dark: string; edge: string }> = {
  yellow: { light: "#FFF4BF", dark: "#3D3714", edge: "#E6C84A" },
  pink: { light: "#FFDDE6", dark: "#40222B", edge: "#E58DA6" },
  blue: { light: "#DCEBFF", dark: "#1C2D42", edge: "#7FAEE6" },
  green: { light: "#DDF3E1", dark: "#1D3524", edge: "#78BF88" },
  purple: { light: "#EBE1FF", dark: "#2F2643", edge: "#A58BE0" },
  orange: { light: "#FFE4CC", dark: "#402A17", edge: "#EBA567" },
}

export function noteColor(value: string): NoteColor {
  return (NOTE_COLORS as readonly string[]).includes(value) ? (value as NoteColor) : "yellow"
}
