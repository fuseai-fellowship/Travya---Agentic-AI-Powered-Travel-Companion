import { HStack, Text } from "@chakra-ui/react"

export function LogoMark({ size = 28 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" aria-hidden="true" focusable="false">
      <rect width="64" height="64" rx="14" fill="#C4441F" />
      <path
        d="M15 21h30M30 21v23"
        fill="none"
        stroke="#FBF8F3"
        strokeWidth="7"
        strokeLinecap="round"
      />
      <path
        d="M30 44c0 6 5 7 10 4s9-3 10 0"
        fill="none"
        stroke="#FBF8F3"
        strokeWidth="3"
        strokeLinecap="round"
        strokeDasharray="1 5"
      />
      <circle cx="49" cy="21" r="5" fill="#F0E442" />
    </svg>
  )
}

export function Logo({ size = 28 }: { size?: number }) {
  return (
    <HStack gap="2" align="center">
      <LogoMark size={size} />
      <Text
        as="span"
        fontFamily="heading"
        fontWeight="600"
        fontSize={size > 32 ? "2xl" : "xl"}
        letterSpacing="-0.01em"
      >
        Travya
      </Text>
    </HStack>
  )
}
