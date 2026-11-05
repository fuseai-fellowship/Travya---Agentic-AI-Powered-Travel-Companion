# 0005. Use OpenStreetMap and other open data

- Status: accepted
- Date: 2026-11-04

## Context

The prototype depended on keyed commercial APIs (Google Maps and Places, Amadeus, a weather API).
Some keys were read from settings that did not exist, so results were always empty. Every reviewer
who wanted to run the project would have needed several accounts, and every key is one more secret to
keep out of the web bundle and the repository. Travya also needs to credit its sources clearly.

## Decision

Build on open data, called from the backend only (except map tiles):

| Need | Source |
|---|---|
| Geocoding | Nominatim |
| Destination autocomplete | Photon |
| Points of interest | Overpass API, with Wikipedia geosearch as a concurrent backup |
| Routing | FOSSGIS OSRM, or OpenRouteService when a key is set |
| Map tiles | OpenFreeMap vector tiles in MapLibre |
| Weather | Open-Meteo forecast and archive |
| Travel guides | Wikivoyage, with Wikipedia summaries as fallback |
| Photos | Wikimedia Commons, or Unsplash when a key is set |
| Flights and hotels | Deterministic sample offers ([ADR 0006](0006-simulated-bookings-human-in-the-loop.md)) |

Each call goes through the shared HTTP client with an identifying User-Agent, per-host rate limits,
retries and Redis caching (`backend/app/integrations/`). Attribution travels with the data:
`© OpenStreetMap contributors` on the map, source URLs and licences with guide text, photographer
credits with photos, and a `sources` list on every plan.

## Consequences

- The full product works without any key except Gemini's; with `OFFLINE_INTEGRATIONS=true` it needs
  none at all.
- No secrets reach the browser.
- Public instances have usage policies (for example one request per second on Nominatim) and are
  sometimes overloaded (Overpass). Caching, limits, time budgets and backups keep Travya within them
  and responsive, but throughput is capped and heavy use would need self-hosted or paid instances.
- Data quality varies by region: opening hours and addresses are often missing, and there are no
  ratings or reviews.
- Licence obligations (ODbL, CC BY-SA, CC BY) must be honoured in the UI, and the credit has to follow
  the source that actually answered.

## Alternatives considered

- **Google Maps Platform**: excellent data and ratings, but a billing account, keys in every
  environment and terms that restrict caching and mixing with other maps.
- **Mapbox or Foursquare**: good APIs, same key and quota issues, smaller free tiers for this mix of
  features.
- **Amadeus self-service test API for offers**: real-looking fares, but another account, token
  handling and test data that is no more real than samples.
