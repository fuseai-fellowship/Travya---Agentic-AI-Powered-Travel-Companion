/**
 * After a Pages deploy, an open tab still asks for the old hashed chunks, which now resolve to
 * index.html, so lazy routes and the map fail to load. Vite reports that as `vite:preloadError`:
 * reload once to pick up the new build (a session flag stops a reload loop).
 */
export const RELOAD_FLAG = "travya:reloaded-for-new-build"

export function recoverFromStaleChunks(
  target: Window = window,
  storage: Storage = window.sessionStorage,
  reload: () => void = () => window.location.reload(),
) {
  target.addEventListener("vite:preloadError", (event) => {
    if (storage.getItem(RELOAD_FLAG)) return
    storage.setItem(RELOAD_FLAG, "1")
    event.preventDefault()
    reload()
  })
  // The new build loaded fine: a later deploy may reload again.
  target.setTimeout(() => storage.removeItem(RELOAD_FLAG), 10_000)
}
