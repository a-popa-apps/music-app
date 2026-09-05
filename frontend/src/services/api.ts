export const BACKEND_URL =
  import.meta.env.VITE_BACKEND_URL ?? "http://localhost:8000"

export async function checkBackendHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${BACKEND_URL}/health`)
    if (!res.ok) return false
    const data = await res.json()
    return data.status === "ok"
  } catch {
    return false
  }
}

export interface ProfileSettings {
  name: string
  country: string
  artist_name: string
  role: string | null
  primary_genres: string[]
  filename_template: string | null
  discogs_deep_search: boolean
  plan: "free" | "pro"
  is_admin: boolean
}

export async function getProfile(idToken: string): Promise<ProfileSettings> {
  const res = await fetch(`${BACKEND_URL}/profile`, {
    headers: { Authorization: `Bearer ${idToken}` },
  })
  if (!res.ok) throw new Error(`Failed to load profile: ${res.status}`)
  return res.json()
}

export async function saveProfile(
  idToken: string,
  settings: Partial<Omit<ProfileSettings, "plan">>
): Promise<ProfileSettings> {
  const res = await fetch(`${BACKEND_URL}/profile`, {
    method: "PUT",
    headers: {
      Authorization: `Bearer ${idToken}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(settings),
  })
  if (!res.ok) throw new Error(`Failed to save profile: ${res.status}`)
  return res.json()
}

export async function deleteAccount(idToken: string): Promise<void> {
  const res = await fetch(`${BACKEND_URL}/profile`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${idToken}` },
  })
  if (!res.ok) throw new Error(`Failed to delete account: ${res.status}`)
}

export interface AdminUser {
  uid: string
  email: string | null
  disabled: boolean
  created_at: number
  name: string
  artist_name: string
  plan: "free" | "pro"
  is_admin: boolean
}

export interface AdminStats {
  total_users: number
  by_plan: Record<string, number>
  admin_count: number
  recent_signups: AdminUser[]
}

export interface DiscountCode {
  code: string
  percent_off: number
  active: boolean
  max_uses: number
  used_count: number
  created_by: string
  created_at: string
}

function adminHeaders(idToken: string) {
  return { Authorization: `Bearer ${idToken}`, "Content-Type": "application/json" }
}

export async function getAdminUsers(idToken: string): Promise<AdminUser[]> {
  const res = await fetch(`${BACKEND_URL}/admin/users`, { headers: adminHeaders(idToken) })
  if (!res.ok) throw new Error(`Failed to load users: ${res.status}`)
  return res.json()
}

export async function setUserPlan(
  idToken: string,
  uid: string,
  plan: "free" | "pro"
): Promise<ProfileSettings> {
  const res = await fetch(`${BACKEND_URL}/admin/users/${uid}/plan`, {
    method: "PUT",
    headers: adminHeaders(idToken),
    body: JSON.stringify({ plan }),
  })
  if (!res.ok) throw new Error(`Failed to update plan: ${res.status}`)
  return res.json()
}

export async function setUserAdmin(
  idToken: string,
  uid: string,
  isAdmin: boolean
): Promise<ProfileSettings> {
  const res = await fetch(`${BACKEND_URL}/admin/users/${uid}/admin`, {
    method: "PUT",
    headers: adminHeaders(idToken),
    body: JSON.stringify({ is_admin: isAdmin }),
  })
  if (!res.ok) throw new Error(`Failed to update admin status: ${res.status}`)
  return res.json()
}

export async function deleteUserAsAdmin(idToken: string, uid: string): Promise<void> {
  const res = await fetch(`${BACKEND_URL}/admin/users/${uid}`, {
    method: "DELETE",
    headers: adminHeaders(idToken),
  })
  if (!res.ok) throw new Error(`Failed to delete user: ${res.status}`)
}

export async function getAdminStats(idToken: string): Promise<AdminStats> {
  const res = await fetch(`${BACKEND_URL}/admin/stats`, { headers: adminHeaders(idToken) })
  if (!res.ok) throw new Error(`Failed to load stats: ${res.status}`)
  return res.json()
}

export async function getDiscountCodes(idToken: string): Promise<DiscountCode[]> {
  const res = await fetch(`${BACKEND_URL}/admin/discount-codes`, {
    headers: adminHeaders(idToken),
  })
  if (!res.ok) throw new Error(`Failed to load discount codes: ${res.status}`)
  return res.json()
}

export async function createDiscountCode(
  idToken: string,
  percentOff: number,
  maxUses: number
): Promise<DiscountCode> {
  const res = await fetch(`${BACKEND_URL}/admin/discount-codes`, {
    method: "POST",
    headers: adminHeaders(idToken),
    body: JSON.stringify({ percent_off: percentOff, max_uses: maxUses }),
  })
  if (!res.ok) throw new Error(`Failed to create discount code: ${res.status}`)
  return res.json()
}

export async function setDiscountCodeActive(
  idToken: string,
  code: string,
  active: boolean
): Promise<DiscountCode> {
  const res = await fetch(`${BACKEND_URL}/admin/discount-codes/${code}`, {
    method: "PATCH",
    headers: adminHeaders(idToken),
    body: JSON.stringify({ active }),
  })
  if (!res.ok) throw new Error(`Failed to update discount code: ${res.status}`)
  return res.json()
}

export async function uploadAndProcess(files: File[], idToken?: string): Promise<Blob> {
  const formData = new FormData()
  files.forEach((file) => formData.append("files", file))

  const response = await fetch(`${BACKEND_URL}/process`, {
    method: "POST",
    headers: idToken ? { Authorization: `Bearer ${idToken}` } : undefined,
    body: formData,
  })

  if (!response.ok) {
    throw new Error(`Processing failed: ${response.status}`)
  }

  return response.blob()
}
