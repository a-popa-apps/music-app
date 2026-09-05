import { useEffect, useState } from "react"
import { getProfile } from "../services/api"
import { useAuth } from "./useAuth"

export function useIsAdmin() {
  const { user } = useAuth()
  const [isAdmin, setIsAdmin] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!user) {
      setIsAdmin(false)
      setLoading(false)
      return
    }

    let cancelled = false
    async function load() {
      try {
        const token = await user!.getIdToken()
        const profile = await getProfile(token)
        if (!cancelled) setIsAdmin(profile.is_admin)
      } catch {
        if (!cancelled) setIsAdmin(false)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()

    return () => {
      cancelled = true
    }
  }, [user])

  return { isAdmin, loading }
}
