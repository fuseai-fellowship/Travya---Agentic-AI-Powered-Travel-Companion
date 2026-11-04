import type { IconType } from "react-icons"
import {
  LuCloud,
  LuCloudDrizzle,
  LuCloudFog,
  LuCloudLightning,
  LuCloudRain,
  LuCloudSnow,
  LuCloudSun,
  LuSun,
} from "react-icons/lu"

/** WMO weather interpretation codes (Open-Meteo) to an icon. */
export function weatherIcon(code: number | null | undefined): IconType {
  if (code === null || code === undefined) return LuCloudSun
  if (code === 0) return LuSun
  if (code <= 2) return LuCloudSun
  if (code === 3) return LuCloud
  if (code === 45 || code === 48) return LuCloudFog
  if (code >= 51 && code <= 57) return LuCloudDrizzle
  if ((code >= 61 && code <= 67) || (code >= 80 && code <= 82)) return LuCloudRain
  if ((code >= 71 && code <= 77) || code === 85 || code === 86) return LuCloudSnow
  if (code >= 95) return LuCloudLightning
  return LuCloud
}

export function formatTemp(value: number | null | undefined): string {
  return value === null || value === undefined ? "–" : `${Math.round(value)}°`
}
