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

export async function uploadAndProcess(files: File[]): Promise<Blob> {
  const formData = new FormData()
  files.forEach((file) => formData.append("files", file))

  const response = await fetch(`${BACKEND_URL}/process`, {
    method: "POST",
    body: formData,
  })

  if (!response.ok) {
    throw new Error(`Processing failed: ${response.status}`)
  }

  return response.blob()
}
