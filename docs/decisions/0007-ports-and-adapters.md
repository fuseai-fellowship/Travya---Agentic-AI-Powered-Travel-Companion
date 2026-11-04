# 0007. Put every external service behind a port with a fake

- Status: accepted
- Date: 2026-11-04

## Context

The prototype had two overlapping layers of API clients, and its tests either called real services or
mocked internals so deeply that they tested the mocks. Several test modules could not even be
collected. Travya needs nine external capabilities, most of them served by public instances with usage
policies, and CI, reviewers and the end-to-end suite must run without network access or keys.

## Decision

- `backend/app/integrations/ports.py` defines one `Protocol` per capability (`Geocoder`,
  `Autocomplete`, `PlacesSearch`, `Router`, `WeatherProvider`, `GuideProvider`, `PhotoProvider`,
  `OffersProvider`, `ObjectStorage`) and the Pydantic models they return.
- Each provider has an adapter in its own module; fallbacks are composed adapters (`FallbackPlaces`,
  `FallbackRouter`, `FallbackPhotos`).
- `fakes.py` implements every port deterministically and without network.
- `registry.py` builds an `Integrations` bundle from the settings at startup:
  `OFFLINE_INTEGRATIONS=true` selects the fakes. Services and agents receive the bundle and never
  import an adapter.
- Cross-cutting behaviour lives in one place: the shared HTTP client with retries and per-host limits
  (`http.py`), cache TTLs (`caching.py`).
- Tests: adapter tests mock HTTP with `respx`, API and agent tests run on the fakes, and live smoke
  tests against the real services run only with `RUN_LIVE=1`.

## Consequences

- The backend suite, CI and `make e2e` run offline and deterministically; a keyless demo works.
- Swapping or adding a provider touches one adapter and the registry.
- Fallbacks and caching are uniform and testable.
- Fakes can drift from real behaviour. Adapter tests pin the parsing of real response shapes, and the
  opt-in live tests catch upstream changes.
- The ports are an extra layer to read for newcomers.

## Alternatives considered

- **Mock HTTP everywhere**: no abstraction, but every service and agent test would need per-request
  fixtures, and demos would still need the network.
- **Recorded cassettes** (VCR-style): realistic, but brittle when queries change and awkward for
  parallel, cached requests.
- **Call the real services in tests**: slow, flaky, rate-limited, and impolite to public instances.
