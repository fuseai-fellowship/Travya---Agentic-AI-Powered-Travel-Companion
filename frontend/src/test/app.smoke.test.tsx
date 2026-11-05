import { createMemoryHistory, RouterProvider } from "@tanstack/react-router"
import { render, screen, waitFor, within } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { HttpResponse, http } from "msw"
import { beforeAll, describe, expect, it, vi } from "vitest"
import { Providers } from "@/app/providers"
import { createQueryClient } from "@/app/queryClient"
import { createAppRouter } from "@/app/router"
import { setupApiClient } from "@/lib/api"
import * as fixtures from "./fixtures"
import { server } from "./server"

// Every page mounts against MSW: catches runtime errors (bad component usage, missing states)
// that type checks can't, without a browser.

const fakeUser = {
  uid: "user-1",
  isAnonymous: true,
  email: null,
  displayName: null,
  providerData: [],
  getIdToken: async () => "test-token",
}

vi.mock("firebase/auth", () => ({
  onIdTokenChanged: (_auth: unknown, callback: (user: unknown) => void) => {
    callback(fakeUser)
    return () => undefined
  },
  signOut: vi.fn(async () => undefined),
}))

vi.mock("@/lib/firebase", () => ({
  auth: {},
  currentUser: async () => fakeUser,
  onSessionExpired: () => () => undefined,
  firebaseTokens: { getToken: async () => "test-token", onUnauthorized: () => undefined },
}))

// MapLibre needs WebGL; the map's data flow is covered by its props.
vi.mock("@/features/map/TripMap", () => ({
  default: ({ stops }: { stops: unknown[] }) => (
    <div data-testid="trip-map">{stops.length} stops</div>
  ),
}))

const API = "http://localhost:8000/api/v1"

beforeAll(() => setupApiClient())

function mount(path: string) {
  const queryClient = createQueryClient()
  const router = createAppRouter(
    { queryClient, getUser: async () => fakeUser },
    createMemoryHistory({ initialEntries: [path] }),
  )
  return render(
    <Providers queryClient={queryClient}>
      <RouterProvider router={router} />
    </Providers>,
  )
}

function api(trips: unknown[] = [fixtures.trip]) {
  server.use(
    http.get(`${API}/trips`, () => HttpResponse.json(fixtures.page(trips))),
    http.get(`${API}/trips/:id`, () => HttpResponse.json(fixtures.trip)),
    http.get(`${API}/trips/:id/itinerary`, () => HttpResponse.json(fixtures.items)),
    http.get(`${API}/trips/:id/bookings`, () => HttpResponse.json(fixtures.bookings)),
    http.get(`${API}/trips/:id/map`, () => HttpResponse.json(fixtures.tripMap)),
    http.get(`${API}/trips/:id/weather`, () => HttpResponse.json([])),
    http.get(`${API}/trips/:id/photos`, () => HttpResponse.json([])),
    http.get(`${API}/documents`, () => HttpResponse.json([])),
    http.get(`${API}/notes`, () => HttpResponse.json(fixtures.page([fixtures.note]))),
    http.get(`${API}/conversations`, () =>
      HttpResponse.json(fixtures.page([fixtures.conversation])),
    ),
    http.get(`${API}/conversations/:id/messages`, () =>
      HttpResponse.json(
        fixtures.page([
          {
            id: "m1",
            role: "user",
            content: "What should I pack?",
            meta: {},
            created_at: "2026-11-05T09:00:00Z",
          },
          {
            id: "m2",
            role: "assistant",
            content: "Bring **layers**.",
            meta: { tools: ["weather_forecast"] },
            created_at: "2026-11-05T09:00:05Z",
          },
        ]),
      ),
    ),
    http.get(`${API}/me`, () => HttpResponse.json(fixtures.me)),
    http.get(`${API}/me/usage`, () => HttpResponse.json({ llm_runs_remaining_today: 42 })),
    http.get(`${API}/explore/places`, () => HttpResponse.json([])),
  )
}

describe("app smoke", () => {
  it("renders the landing page with the demo call to action", async () => {
    api()
    mount("/")
    expect(
      await screen.findByRole("heading", { level: 1, name: /team of AI agents/i }),
    ).toBeInTheDocument()
    expect(screen.getByRole("link", { name: /open your trips/i })).toHaveAttribute("href", "/trips")
    expect(screen.getByText(/Tilak Parajuli and Bigya/)).toBeInTheDocument()
  })

  it("shows sample trips when there are none", async () => {
    api([])
    mount("/trips")
    expect(await screen.findByText("Plan your first trip")).toBeInTheDocument()
    for (const name of ["Kathmandu", "Lisbon", "Kyoto"]) {
      expect(screen.getByRole("link", { name })).toHaveAttribute(
        "href",
        expect.stringContaining("sample="),
      )
    }
  })

  it("doesn't call an emptied later page 'your first trip'", async () => {
    api()
    server.use(
      http.get(`${API}/trips`, () =>
        HttpResponse.json({ items: [], total: 20, limit: 20, offset: 20 }),
      ),
    )
    mount("/trips?page=2")
    expect(await screen.findByText("Nothing on this page")).toBeInTheDocument()
    expect(screen.queryByText("Plan your first trip")).not.toBeInTheDocument()
    expect(screen.getByRole("button", { name: "Back to the first page" })).toBeInTheDocument()
  })

  it("starts a blank trip from the profile's home city and currency", async () => {
    api()
    server.use(
      http.get(`${API}/me`, () =>
        HttpResponse.json({ ...fixtures.me, home_city: "Pokhara", currency: "EUR" }),
      ),
    )
    mount("/trips/new")
    const origin = await screen.findByRole("textbox", { name: /Travelling from/ })
    await waitFor(() => expect(origin).toHaveValue("Pokhara"))
    expect(screen.getByRole("combobox", { name: "Currency" })).toHaveValue("EUR")
  })

  it("asks before a demo account signs out", async () => {
    api()
    mount("/trips")
    const user = userEvent.setup()
    const [menu] = await screen.findAllByRole("button", { name: /Account menu for/ })
    await user.click(menu as HTMLElement)
    await user.click(await screen.findByRole("menuitem", { name: "Sign out" }))
    const dialog = await screen.findByRole("alertdialog", { name: "Sign out of the demo?" })
    expect(dialog).toHaveTextContent("add an email or Google sign-in in Settings")
  })

  it("lists trips", async () => {
    api()
    mount("/trips")
    expect(await screen.findByRole("link", { name: "Kathmandu" })).toHaveAttribute(
      "href",
      `/trips/${fixtures.TRIP_ID}`,
    )
  })

  it("prefills the new-trip form from a sample", async () => {
    api()
    mount("/trips/new?sample=lisbon")
    expect(await screen.findByRole("heading", { name: "Plan Lisbon" })).toBeInTheDocument()
    expect(screen.getByRole("combobox", { name: "Destination" })).toHaveValue("Lisbon")
    expect(screen.getByRole("button", { name: /plan my trip/i })).toBeEnabled()
  })

  it("renders the trip page with itinerary, budget and map", async () => {
    api()
    mount(`/trips/${fixtures.TRIP_ID}`)
    expect(await screen.findByRole("heading", { level: 1, name: "Kathmandu" })).toBeInTheDocument()
    expect(
      await screen.findByText("Kathmandu Durbar Square", { selector: "p" }),
    ).toBeInTheDocument()
    expect(screen.getByRole("meter", { name: "Budget used" })).toBeInTheDocument()
    expect(await screen.findByTestId("trip-map")).toHaveTextContent("1 stops")
    expect(screen.getByText("Walk clockwise around stupas")).toBeInTheDocument()
  })

  it("shows the simulated booking notice", async () => {
    api()
    mount(`/trips/${fixtures.TRIP_ID}?tab=bookings`)
    expect(await screen.findByText(/Bookings are simulated/)).toBeInTheDocument()
    expect(await screen.findByRole("button", { name: "Confirm booking" })).toBeInTheDocument()
  })

  it("renders a conversation with tool chips", async () => {
    api()
    mount("/assistant?c=conv-1")
    const log = await screen.findByRole("log", { name: "Conversation" })
    expect(await within(log).findByText("layers")).toBeInTheDocument()
    expect(within(log).getByText("Checked the weather")).toBeInTheDocument()
  })

  it("renders the notes board and settings", async () => {
    api()
    const { unmount } = mount("/notes")
    expect(await screen.findByRole("button", { name: "Pack a headlamp" })).toBeInTheDocument()
    unmount()
    mount("/settings")
    expect(await screen.findByText(/42 agent runs/)).toBeInTheDocument()
    expect(screen.getByText("You're using a demo account")).toBeInTheDocument()
  })
})
