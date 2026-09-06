import { useProfile } from "./useProfile"

export function useIsAdmin() {
  const { profile, loading } = useProfile()
  return { isAdmin: profile?.is_admin ?? false, loading }
}
