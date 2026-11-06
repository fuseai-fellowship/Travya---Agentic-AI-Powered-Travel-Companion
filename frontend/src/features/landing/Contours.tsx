import { Box, type BoxProps } from "@chakra-ui/react"
import contours from "./media/contours-kathmandu.svg"

/**
 * The only decoration: 100 m contour lines of the Kathmandu Valley, traced from the Copernicus
 * GLO-90 elevation model (via Open-Meteo). The SVG is a mask, so the line colour follows the theme;
 * `fade` keeps the lines out from under text on the left.
 */
export function Contours({ fade = false, ...props }: BoxProps & { fade?: boolean }) {
  const lines = `url(${contours})`
  const mask = fade
    ? `${lines}, linear-gradient(to right, transparent 0%, transparent 30%, #000 62%)`
    : lines
  return (
    <Box
      aria-hidden="true"
      pointerEvents="none"
      bg="contour"
      css={{
        maskImage: mask,
        maskSize: fade ? "cover, 100% 100%" : "cover",
        maskPosition: "center",
        maskRepeat: "no-repeat",
        maskComposite: "intersect",
        WebkitMaskImage: mask,
        WebkitMaskSize: fade ? "cover, 100% 100%" : "cover",
        WebkitMaskPosition: "center",
        WebkitMaskRepeat: "no-repeat",
        WebkitMaskComposite: "source-in",
      }}
      {...props}
    />
  )
}
