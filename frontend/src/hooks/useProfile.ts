import { useEffect, useState } from "react"
import { getProfile, type ProfileSettings } from "../services/api"
import { useAuth } from "./useAuth"

export function useProfile() {
  const { user } = useAuth()
  const [profile, setProfile] = useState<ProfileSettings | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!user) {
      setProfile(null)
      setLoading(false)
      return
    }

    let cancelled = false
    async function load() {
      try {
        const token = await user!.getIdToken()
        const p = await getProfile(token)
        if (!cancelled) setProfile(p)
      } catch {
        if (!cancelled) setProfile(null)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()

    return () => {
      cancelled = true
    }
  }, [user])

  return { profile, loading }
}
