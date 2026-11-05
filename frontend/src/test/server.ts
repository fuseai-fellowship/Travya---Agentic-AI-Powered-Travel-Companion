import { setupServer } from "msw/node"

export const API = "http://api.test"

/** Tests add their own handlers with `server.use(...)`; unmatched requests fail the test. */
export const server = setupServer()
