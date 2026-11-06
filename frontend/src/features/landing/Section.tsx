import { Box, Container, Heading, Stack, Text } from "@chakra-ui/react"
import type { ReactNode } from "react"

/** A landing section: left-aligned heading, one lead line, content. No entrance animation. */
export function Section({
  id,
  title,
  lead,
  children,
  bordered = true,
}: {
  id: string
  title: string
  lead?: ReactNode
  children: ReactNode
  bordered?: boolean
}) {
  return (
    <Box as="section" aria-labelledby={`${id}-title`} id={id} scrollMarginTop="16">
      <Container
        maxW="7xl"
        px={{ base: "4", md: "8" }}
        py={{ base: "12", md: "16" }}
        borderTopWidth={bordered ? "1px" : "0"}
      >
        <Stack gap="2" mb={{ base: "6", md: "8" }} maxW="3xl">
          <Heading
            as="h2"
            id={`${id}-title`}
            fontSize={{ base: "2xl", md: "3xl" }}
            fontWeight="800"
            letterSpacing="-0.02em"
            lineHeight="1.1"
          >
            {title}
          </Heading>
          {lead && (
            <Text color="fg.muted" fontSize={{ base: "md", md: "lg" }}>
              {lead}
            </Text>
          )}
        </Stack>
        {children}
      </Container>
    </Box>
  )
}

/** Inline link styling shared by the landing sections. */
export const linkStyle = {
  color: "brand.fg",
  textDecoration: "underline",
  textUnderlineOffset: "3px",
  textDecorationThickness: "1px",
  _hover: { textDecorationThickness: "2px" },
} as const
