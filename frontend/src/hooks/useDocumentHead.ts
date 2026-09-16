import { useEffect } from "react"

const DEFAULT_TITLE = "CratePrep — Clean Filenames, BPM & Key Detection for DJs"
const DEFAULT_DESCRIPTION =
  "Drop your messy downloaded tracks and get back clean filenames plus verified BPM, key, and genre tags — ready for Rekordbox, Serato, or any DJ software."

function setMetaContent(selector: string, content: string) {
  const el = document.querySelector(selector)
  if (el) el.setAttribute("content", content)
}

function setCanonical(path: string) {
  let link = document.querySelector<HTMLLinkElement>('link[rel="canonical"]')
  if (!link) {
    link = document.createElement("link")
    link.rel = "canonical"
    document.head.appendChild(link)
  }
  link.href = `https://crateprep.app${path}`
}

function setRobots(noindex: boolean) {
  let meta = document.querySelector<HTMLMetaElement>('meta[name="robots"]')
  if (noindex) {
    if (!meta) {
      meta = document.createElement("meta")
      meta.name = "robots"
      document.head.appendChild(meta)
    }
    meta.setAttribute("content", "noindex")
  } else if (meta) {
    meta.remove()
  }
}

/** Per-route <title>/description/canonical -- index.html only ships one
 * static set (what a non-JS crawler/link-unfurler ever sees for the
 * homepage), so every other route needs this to avoid every page in the
 * app reporting the same title/description to search engines. Resets to
 * the site-wide default on unmount so navigating away (e.g. via the
 * back button into a route that doesn't call this) doesn't leak a stale
 * title/description from whatever page was open last.
 *
 * noindex is for routes that shouldn't be indexed but (unlike /auth,
 * /profile, /history, /admin -- already blocked in robots.txt) aren't
 * disallowed there, namely the 404 page: the SPA rewrite in vercel.json
 * sends every unmatched path to this same page with a 200 status, so
 * without this it reads as an indexable "soft 404" to a crawler. */
export function useDocumentHead(title: string, description: string, path: string, noindex = false) {
  useEffect(() => {
    const fullTitle = `${title} | CratePrep`
    document.title = fullTitle
    setMetaContent('meta[name="description"]', description)
    setMetaContent('meta[property="og:title"]', fullTitle)
    setMetaContent('meta[property="og:description"]', description)
    setMetaContent('meta[property="og:url"]', `https://crateprep.app${path}`)
    setMetaContent('meta[name="twitter:title"]', fullTitle)
    setMetaContent('meta[name="twitter:description"]', description)
    setCanonical(path)
    setRobots(noindex)

    return () => {
      document.title = DEFAULT_TITLE
      setMetaContent('meta[name="description"]', DEFAULT_DESCRIPTION)
      setMetaContent('meta[property="og:title"]', DEFAULT_TITLE)
      setMetaContent('meta[property="og:description"]', DEFAULT_DESCRIPTION)
      setMetaContent('meta[property="og:url"]', "https://crateprep.app/")
      setMetaContent('meta[name="twitter:title"]', DEFAULT_TITLE)
      setMetaContent('meta[name="twitter:description"]', DEFAULT_DESCRIPTION)
      setCanonical("/")
      setRobots(false)
    }
  }, [title, description, path, noindex])
}
