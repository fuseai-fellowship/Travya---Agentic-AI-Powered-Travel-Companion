import { HStack, Text } from "@chakra-ui/react"

/**
 * A road-sign plate in route blue: the T is a road with a stop at its end, drawn the way the map
 * draws a day (route line, numbered pin).
 */
export function LogoMark({ size = 28 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" aria-hidden="true" focusable="false">
      <rect width="64" height="64" rx="12" fill="#0072B2" />
      <path
        d="M14 19h30M29 19v20c0 7 4 10 11 10h4"
        fill="none"
        stroke="#FFFFFF"
        strokeWidth="7"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx="49" cy="49" r="7" fill="#D55E00" stroke="#FFFFFF" strokeWidth="3" />
    </svg>
  )
}

export function Logo({ size = 28 }: { size?: number }) {
  return (
    <HStack gap="2" align="center">
      <LogoMark size={size} />
      <Text
        as="span"
        fontWeight="800"
        fontSize={size > 32 ? "2xl" : "xl"}
        letterSpacing="-0.02em"
        lineHeight="1"
        pt="0.1em"
      >
        Travya
      </Text>
    </HStack>
  )
}
