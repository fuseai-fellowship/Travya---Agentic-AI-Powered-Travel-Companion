import { AspectRatio, Box, Button, Link as ChakraLink, Image, Text } from "@chakra-ui/react"
import { useRef, useState } from "react"
import { LuPause, LuPlay } from "react-icons/lu"
import { usePrefersReducedMotion } from "@/lib/hooks"
import mp4 from "./media/real-run.mp4"
import captions from "./media/real-run.vtt?url"
import webm from "./media/real-run.webm"
import poster from "./media/real-run-poster.webp"
import { linkStyle, Section } from "./Section"

const WIDTH = 1600
const HEIGHT = 1000

/**
 * A real production run screen-recorded on this interface, cut to 20 s (trimmed and sped up only).
 * Muted, captioned, click to play or pause; nothing autoplays. Reduced motion gets the poster.
 */
export function RealRunVideo() {
  const reducedMotion = usePrefersReducedMotion()
  const video = useRef<HTMLVideoElement>(null)
  const [playing, setPlaying] = useState(false)

  const toggle = () => {
    const element = video.current
    if (!element) return
    if (element.paused) void element.play()
    else element.pause()
  }

  return (
    <Section
      id="video"
      title="Watch a real run"
      lead="Twenty seconds of a production run on this interface: Kathmandu planned, a simulated stay confirmed, a weather question answered. Waits are sped up, nothing is staged."
    >
      <Box
        position="relative"
        borderWidth="1px"
        borderRadius="card"
        overflow="hidden"
        bg="bg.muted"
      >
        <AspectRatio ratio={WIDTH / HEIGHT}>
          {reducedMotion ? (
            <Image
              src={poster}
              width={WIDTH}
              height={HEIGHT}
              loading="lazy"
              alt="Travya's trip page after planning Kathmandu: the day list beside a map with numbered stops"
            />
          ) : (
            <video
              ref={video}
              poster={poster}
              width={WIDTH}
              height={HEIGHT}
              muted
              loop
              playsInline
              preload="metadata"
              onPlay={() => setPlaying(true)}
              onPause={() => setPlaying(false)}
              onClick={toggle}
              aria-label="Screen recording of a real planning run"
            >
              <source src={webm} type='video/webm; codecs="av01.0.08M.08"' />
              <source src={mp4} type="video/mp4" />
              <track kind="captions" src={captions} srcLang="en" label="English" default />
            </video>
          )}
        </AspectRatio>
        {!reducedMotion && (
          <Button
            position="absolute"
            left="3"
            bottom="3"
            size="sm"
            colorPalette="brand"
            variant={playing ? "surface" : "solid"}
            onClick={toggle}
            aria-label={playing ? "Pause the video" : "Play the 20-second video"}
          >
            {playing ? <LuPause /> : <LuPlay />}
            {playing ? "Pause" : "Play, 20 s"}
          </Button>
        )}
      </Box>
      <Text fontSize="sm" color="fg.muted" mt="3">
        No sound; captions describe each step.{" "}
        <ChakraLink href={mp4} target="_blank" rel="noopener noreferrer" {...linkStyle}>
          Open the video file
        </ChakraLink>
        .
      </Text>
    </Section>
  )
}
