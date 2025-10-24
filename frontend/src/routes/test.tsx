import { createFileRoute } from "@tanstack/react-router"

export const Route = createFileRoute("/test")({
  component: TestComponent,
})

function TestComponent() {
  return (
    <div style={{ padding: "20px", fontFamily: "Arial, sans-serif" }}>
      <h1>Test Page</h1>
      <p>If you can see this, the router is working!</p>
      <a href="/">Go to Home</a>
    </div>
  )
}
