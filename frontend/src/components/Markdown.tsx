import { Box, type BoxProps } from "@chakra-ui/react"
import ReactMarkdown, { type Components } from "react-markdown"
import rehypeSanitize from "rehype-sanitize"

const components: Components = {
  a: ({ node: _node, ...props }) => (
    <a {...props} target="_blank" rel="noopener noreferrer nofollow" />
  ),
  img: ({ node: _node, alt, ...props }) => <img {...props} alt={alt ?? ""} loading="lazy" />,
}

/** Markdown from users and the model. Raw HTML is never rendered and the output is sanitised. */
export function Markdown({ children, ...props }: { children: string } & BoxProps) {
  return (
    <Box
      fontSize="sm"
      lineHeight="1.6"
      css={{
        "& p + p, & ul, & ol, & pre, & blockquote": { marginTop: "0.5em" },
        "& ul, & ol": { paddingInlineStart: "1.25em" },
        "& ul": { listStyleType: "disc" },
        "& ol": { listStyleType: "decimal" },
        "& a": { color: "brand.fg", textDecoration: "underline" },
        "& code": {
          fontFamily: "mono",
          fontSize: "0.9em",
          bg: "bg.muted",
          px: "1",
          borderRadius: "sm",
        },
        "& pre": { bg: "bg.muted", p: "3", borderRadius: "md", overflowX: "auto" },
        "& h1, & h2, & h3": { fontFamily: "heading", fontWeight: "600", marginTop: "0.75em" },
        "& img": { maxWidth: "100%", borderRadius: "md" },
        "& blockquote": {
          borderInlineStartWidth: "3px",
          paddingInlineStart: "3",
          color: "fg.muted",
        },
      }}
      {...props}
    >
      <ReactMarkdown rehypePlugins={[rehypeSanitize]} components={components}>
        {children}
      </ReactMarkdown>
    </Box>
  )
}
