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
