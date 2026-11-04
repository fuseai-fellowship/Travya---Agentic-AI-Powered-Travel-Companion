# 0006. Simulate bookings and require the user to confirm them

- Status: accepted
- Date: 2026-11-04

## Context

Booking is the step where an agent's mistake costs real money. In the prototype every planning run
"booked" a mock flight automatically, with no confirmation. Real booking would need merchant
agreements, payment handling and PCI scope, none of which a portfolio demo should have. The OWASP Top
10 for LLM Applications lists excessive agency as a top risk.

## Decision

- The offers scout collects quotes only. `SampleOffers` (`backend/app/integrations/offers/sample.py`)
  returns deterministic sample flights and hotels for the destination and dates, each marked
  `is_sample` and carrying a note that Travya does not sell travel.
- A planning run stores up to eight quotes as `bookings` with status `quoted` and `is_simulated = true`.
- Only the user changes a booking's state, through
  `POST /trips/{trip_id}/bookings/{booking_id}/confirm` or `/cancel`. Confirming sets a `SIM-` code,
  cancels the other open quotes of the same kind and marks the trip `booked`. Anything other than a
  quote cannot be confirmed (`409`).
- Re-planning replaces open quotes but keeps confirmed and cancelled bookings.
- No agent has a tool that writes bookings; the assistant is told that it cannot book.

## Consequences

- No payment data and no real purchases.
- The human-in-the-loop step is enforced by the API, not by a prompt.
- Plans, screenshots and tests are stable because sample prices are deterministic.
- Prices are illustrative only, which the UI must say plainly.
- A real booking provider can later be added as another `OffersProvider`, with the same confirmation
  step in front of it.

## Alternatives considered

- **Agent books directly**: the failure mode the prototype had.
- **Amadeus self-service test API**: realistic-looking data, but still not bookable, and it adds an
  account and token handling.
- **Affiliate deep links**: real prices, but they leave the app and add tracking.
- **Stripe test mode**: demonstrates payments, but adds a payment flow that serves no purpose here.
