import { Alert, CloseButton } from "@chakra-ui/react"
import { dismissDemoLimit, useDemoLimit } from "@/lib/demoLimit"

export function DemoLimitBanner() {
  const message = useDemoLimit()
  if (!message) return null
  return (
    <Alert.Root status="warning" borderRadius="0" borderBottomWidth="1px" role="status">
      <Alert.Indicator />
      <Alert.Content>
        <Alert.Title>Demo limit reached</Alert.Title>
        <Alert.Description>{message}</Alert.Description>
      </Alert.Content>
      <CloseButton size="sm" aria-label="Dismiss" onClick={dismissDemoLimit} />
    </Alert.Root>
  )
}
