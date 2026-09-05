async function sha1Hex(text: string): Promise<string> {
  const data = new TextEncoder().encode(text)
  const digest = await crypto.subtle.digest("SHA-1", data)
  return Array.from(new Uint8Array(digest))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("")
    .toUpperCase()
}

/**
 * Checks a password against the Have I Been Pwned Pwned Passwords API using
 * k-anonymity: only the first 5 characters of the SHA-1 hash are sent, never
 * the password itself. Returns the number of times it's appeared in known
 * breaches (0 if it hasn't), or null if the check couldn't be completed
 * (e.g. offline) -- callers should treat null as "unknown, don't block".
 */
export async function checkPwnedPassword(password: string): Promise<number | null> {
  try {
    const hash = await sha1Hex(password)
    const prefix = hash.slice(0, 5)
    const suffix = hash.slice(5)

    const response = await fetch(`https://api.pwnedpasswords.com/range/${prefix}`)
    if (!response.ok) return null

    const text = await response.text()
    for (const line of text.split("\n")) {
      const [lineSuffix, count] = line.trim().split(":")
      if (lineSuffix === suffix) return parseInt(count, 10)
    }
    return 0
  } catch {
    return null
  }
}
