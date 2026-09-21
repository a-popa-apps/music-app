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

export async function sendVerificationEmail(idToken: string): Promise<void> {
  const res = await fetch(`${BACKEND_URL}/auth/send-verification-email`, {
    method: "POST",
    headers: { Authorization: `Bearer ${idToken}` },
  })
  if (!res.ok) throw new Error(`Failed to send verification email: ${res.status}`)
}

export async function forgotPassword(email: string): Promise<void> {
  const res = await fetch(`${BACKEND_URL}/auth/forgot-password`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  })
  if (!res.ok) throw new Error(`Failed to request password reset: ${res.status}`)
}

// Best-effort -- called right after a user completes email verification.
// Never throws: a failure here shouldn't block or alarm someone who just
// successfully verified their email.
export async function sendWelcomeEmail(email: string): Promise<void> {
  try {
    await fetch(`${BACKEND_URL}/auth/welcome-email`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email }),
    })
  } catch {
    // ignore
  }
}

// Best-effort -- called right after a password reset succeeds. Never
// throws: this is a courtesy security notice, not something that should
// block or alarm someone who just successfully reset their password.
export async function notifyPasswordChanged(email: string): Promise<void> {
  try {
    await fetch(`${BACKEND_URL}/auth/password-changed-notice`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email }),
    })
  } catch {
    // ignore
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
  enhanced_detection: boolean
  ai_filename_cleanup: boolean
  auto_sort_by_energy: boolean
  plan: "free" | "pro"
  is_admin: boolean
  stripe_customer_id: string | null
  stripe_subscription_id: string | null
  subscription_status: string | null
  tracks_processed_this_period: number
  usage_period_start: string | null
}

export async function getProfile(idToken: string): Promise<ProfileSettings> {
  const res = await fetch(`${BACKEND_URL}/profile`, {
    headers: { Authorization: `Bearer ${idToken}` },
  })
  if (!res.ok) throw new Error(`Failed to load profile: ${res.status}`)
  return res.json()
}

export interface HistoryEntry {
  history_id: string
  filename: string
  original_filename: string
  bpm: number | null
  key: string | null
  camelot: string | null
  genre: string | null
  duration_seconds: number | null
  failed: boolean
  processed_at: string
}

export async function getHistory(idToken: string): Promise<HistoryEntry[]> {
  const res = await fetch(`${BACKEND_URL}/history`, {
    headers: { Authorization: `Bearer ${idToken}` },
  })
  if (!res.ok) throw new Error(`Failed to load history: ${res.status}`)
  return res.json()
}

export async function clearHistory(idToken: string): Promise<void> {
  const res = await fetch(`${BACKEND_URL}/history`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${idToken}` },
  })
  if (!res.ok) throw new Error(`Failed to clear history: ${res.status}`)
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

export async function createCheckoutSession(
  idToken: string,
  billingCycle: "monthly" | "annual"
): Promise<string> {
  const res = await fetch(`${BACKEND_URL}/billing/checkout`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${idToken}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ billing_cycle: billingCycle }),
  })
  if (!res.ok) throw new Error(`Failed to start checkout: ${res.status}`)
  const data = await res.json()
  return data.url
}

export async function createBillingPortalSession(idToken: string): Promise<string> {
  const res = await fetch(`${BACKEND_URL}/billing/portal`, {
    method: "POST",
    headers: { Authorization: `Bearer ${idToken}` },
  })
  if (!res.ok) throw new Error(`Failed to open billing portal: ${res.status}`)
  const data = await res.json()
  return data.url
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
  ai_calls_today: number
  ai_daily_limit: number
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

export async function resetUserUsage(idToken: string, uid: string): Promise<ProfileSettings> {
  const res = await fetch(`${BACKEND_URL}/admin/users/${uid}/reset-usage`, {
    method: "POST",
    headers: adminHeaders(idToken),
  })
  if (!res.ok) throw new Error(`Failed to reset usage: ${res.status}`)
  return res.json()
}

export async function getUserProfileAsAdmin(
  idToken: string,
  uid: string
): Promise<ProfileSettings> {
  const res = await fetch(`${BACKEND_URL}/admin/users/${uid}/profile`, {
    headers: adminHeaders(idToken),
  })
  if (!res.ok) throw new Error(`Failed to load profile: ${res.status}`)
  return res.json()
}

export async function getUserHistoryAsAdmin(
  idToken: string,
  uid: string
): Promise<HistoryEntry[]> {
  const res = await fetch(`${BACKEND_URL}/admin/users/${uid}/history`, {
    headers: adminHeaders(idToken),
  })
  if (!res.ok) throw new Error(`Failed to load history: ${res.status}`)
  return res.json()
}

export async function saveUserProfileAsAdmin(
  idToken: string,
  uid: string,
  settings: Partial<Omit<ProfileSettings, "plan" | "is_admin">>
): Promise<ProfileSettings> {
  const res = await fetch(`${BACKEND_URL}/admin/users/${uid}/profile`, {
    method: "PUT",
    headers: adminHeaders(idToken),
    body: JSON.stringify(settings),
  })
  if (!res.ok) throw new Error(`Failed to save profile: ${res.status}`)
  return res.json()
}

export async function getAdminStats(idToken: string): Promise<AdminStats> {
  const res = await fetch(`${BACKEND_URL}/admin/stats`, { headers: adminHeaders(idToken) })
  if (!res.ok) throw new Error(`Failed to load stats: ${res.status}`)
  return res.json()
}

export interface BillingStats {
  mrr_cents: number
  active_subscribers: number
  trialing_subscribers: number
  canceling_subscribers: number
  canceled_last_30_days: number
  revenue_last_30_days_cents: number
}

export async function getBillingStats(idToken: string): Promise<BillingStats> {
  const res = await fetch(`${BACKEND_URL}/admin/billing-stats`, { headers: adminHeaders(idToken) })
  if (!res.ok) throw new Error(`Failed to load billing stats: ${res.status}`)
  return res.json()
}

export interface Transaction {
  id: string
  amount_cents: number
  currency: string
  customer_email: string | null
  status: string
  created: number
  stripe_url: string
}

export async function getRecentTransactions(idToken: string): Promise<Transaction[]> {
  const res = await fetch(`${BACKEND_URL}/admin/recent-transactions`, {
    headers: adminHeaders(idToken),
  })
  if (!res.ok) throw new Error(`Failed to load recent transactions: ${res.status}`)
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

export interface Invite {
  invite_id: string
  email: string
  name: string | null
  source: "admin" | "user"
  invited_by: string
  invited_by_email: string
  inviter_label: string
  admin_note: string | null
  token: string
  status: "pending" | "accepted" | "revoked" | "expired" | "existing_user"
  sent_at: string
  accepted_at: string | null
  accepted_uid: string | null
}

export interface InvitePreview {
  valid: boolean
  email?: string
  name?: string | null
  inviter_label?: string
}

async function _parseInviteError(response: Response, fallback: string): Promise<never> {
  let message = fallback
  try {
    const body = await response.json()
    if (typeof body?.detail === "string") message = body.detail
  } catch {
    // non-JSON error body, fall back to the generic message
  }
  throw new ApiError(response.status, message)
}

export async function getAdminInvites(idToken: string): Promise<Invite[]> {
  const res = await fetch(`${BACKEND_URL}/admin/invites`, { headers: adminHeaders(idToken) })
  if (!res.ok) throw new Error(`Failed to load invites: ${res.status}`)
  return res.json()
}

export async function createAdminInvite(
  idToken: string,
  email: string,
  name: string | undefined,
  adminNote: string | undefined
): Promise<Invite> {
  const res = await fetch(`${BACKEND_URL}/admin/invites`, {
    method: "POST",
    headers: adminHeaders(idToken),
    body: JSON.stringify({ email, name: name || null, admin_note: adminNote || null }),
  })
  if (!res.ok) return _parseInviteError(res, `Failed to create invite: ${res.status}`)
  return res.json()
}

export async function revokeInvite(idToken: string, inviteId: string): Promise<Invite> {
  const res = await fetch(`${BACKEND_URL}/admin/invites/${inviteId}`, {
    method: "PATCH",
    headers: adminHeaders(idToken),
    body: JSON.stringify({ status: "revoked" }),
  })
  if (!res.ok) return _parseInviteError(res, `Failed to revoke invite: ${res.status}`)
  return res.json()
}

export async function getMyInvites(idToken: string): Promise<Invite[]> {
  const res = await fetch(`${BACKEND_URL}/invites/mine`, {
    headers: { Authorization: `Bearer ${idToken}` },
  })
  if (!res.ok) throw new Error(`Failed to load invites: ${res.status}`)
  return res.json()
}

export async function sendInvite(idToken: string, email: string, name: string | undefined): Promise<Invite> {
  const res = await fetch(`${BACKEND_URL}/invites`, {
    method: "POST",
    headers: { Authorization: `Bearer ${idToken}`, "Content-Type": "application/json" },
    body: JSON.stringify({ email, name: name || null }),
  })
  if (!res.ok) return _parseInviteError(res, `Failed to send invite: ${res.status}`)
  return res.json()
}

export async function getInvitePreview(token: string): Promise<InvitePreview> {
  const res = await fetch(`${BACKEND_URL}/invites/${token}`)
  if (!res.ok) return { valid: false }
  return res.json()
}

// Best-effort -- called right after a new account finishes signing up with
// an invite token present. Never throws: a failure here shouldn't block or
// alarm someone who just successfully signed up.
export async function redeemInvite(idToken: string, token: string): Promise<void> {
  try {
    await fetch(`${BACKEND_URL}/invites/${token}/redeem`, {
      method: "POST",
      headers: { Authorization: `Bearer ${idToken}` },
    })
  } catch {
    // ignore
  }
}

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

// XMLHttpRequest, not fetch -- fetch has no way to observe request-body
// upload progress. For a large batch of lossless files, the upload itself
// (client -> Render) can take a lot longer than the actual analysis, and
// onUploadProgress is what lets the UI show "uploading" instead of a
// misleading "processing" the whole time.
export function uploadAndProcess(
  files: File[],
  idToken?: string,
  onUploadProgress?: (fraction: number) => void
): Promise<Blob> {
  const formData = new FormData()
  files.forEach((file) => formData.append("files", file))

  // event.total (from the upload progress event) isn't a stable
  // denominator for a multi-file FormData body -- confirmed in practice,
  // some browsers report it against a partial/streaming estimate early on
  // and correct it upward mid-upload, which makes the percentage jump up
  // and then drop back down. The sum of the actual File sizes is fixed
  // and known upfront, so dividing event.loaded (monotonically
  // non-decreasing per spec) by that instead gives a smooth 0->100% climb
  // regardless of what the browser reports as the total. Clamped to 1
  // since the real wire size is slightly larger (multipart headers/
  // boundaries), so loaded can end up a bit above this estimate.
  const totalBytes = files.reduce((sum, file) => sum + file.size, 0)

  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest()
    xhr.open("POST", `${BACKEND_URL}/process`)
    if (idToken) xhr.setRequestHeader("Authorization", `Bearer ${idToken}`)
    xhr.responseType = "blob"

    xhr.upload.onprogress = (event) => {
      if (totalBytes > 0) onUploadProgress?.(Math.min(1, event.loaded / totalBytes))
    }
    // Body fully sent to the network -- the browser side of "uploading" is
    // done even if the server hasn't started responding yet, so this is
    // the more reliable "upload done" signal vs. waiting on the response.
    xhr.upload.onloadend = () => onUploadProgress?.(1)

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(xhr.response as Blob)
        return
      }
      const errorBlob = xhr.response as Blob
      const reader = new FileReader()
      const fail = (message: string) => reject(new ApiError(xhr.status, message))
      reader.onload = () => {
        let message = `Processing failed: ${xhr.status}`
        try {
          const body = JSON.parse(reader.result as string)
          if (typeof body?.detail === "string") message = body.detail
        } catch {
          // non-JSON error body, fall back to the generic message
        }
        fail(message)
      }
      reader.onerror = () => fail(`Processing failed: ${xhr.status}`)
      reader.readAsText(errorBlob)
    }
    xhr.onerror = () => reject(new ApiError(0, "Network error -- the upload didn't reach the server."))

    xhr.send(formData)
  })
}

export interface TrackCorrection {
  artist: string | null
  title: string | null
  genre: string | null
  bpm: number | null
  camelot: string | null
  tonality: string | null
  energy: number | null
  duration_seconds: number | null
}

// Re-tags an already-processed batch with corrected values -- doesn't
// spend any more of the caller's monthly quota, matching the backend's
// own no-quota-check-here design (this fixes what gets written, it
// doesn't process a new batch).
export async function retagFiles(
  files: File[],
  corrections: TrackCorrection[],
  idToken?: string
): Promise<Blob> {
  const formData = new FormData()
  files.forEach((file) => formData.append("files", file))
  formData.append("corrections", JSON.stringify(corrections))

  const response = await fetch(`${BACKEND_URL}/process/retag`, {
    method: "POST",
    headers: idToken ? { Authorization: `Bearer ${idToken}` } : undefined,
    body: formData,
  })

  if (!response.ok) {
    let message = `Re-tagging failed: ${response.status}`
    try {
      const body = await response.json()
      if (typeof body?.detail === "string") message = body.detail
    } catch {
      // non-JSON error body, fall back to the generic message
    }
    throw new ApiError(response.status, message)
  }

  return response.blob()
}

export interface FeedbackSubmission {
  feedback_id: string
  category: "support" | "feedback"
  subject: string | null
  message: string
  email: string | null
  uid: string | null
  submitted_at: string
  read: boolean
}

export async function submitFeedback(
  category: "support" | "feedback",
  message: string,
  options?: {
    email?: string
    subject?: string
    idToken?: string
    website?: string
    formRenderedAt?: number
  }
): Promise<FeedbackSubmission> {
  const res = await fetch(`${BACKEND_URL}/feedback`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(options?.idToken ? { Authorization: `Bearer ${options.idToken}` } : {}),
    },
    body: JSON.stringify({
      category,
      message,
      email: options?.email,
      subject: options?.subject,
      website: options?.website,
      form_rendered_at: options?.formRenderedAt,
    }),
  })
  if (!res.ok) {
    let msg = `Failed to submit: ${res.status}`
    try {
      const body = await res.json()
      if (typeof body?.detail === "string") msg = body.detail
    } catch {
      // non-JSON error body, fall back to the generic message
    }
    throw new Error(msg)
  }
  return res.json()
}

export async function getFeedback(idToken: string): Promise<FeedbackSubmission[]> {
  const res = await fetch(`${BACKEND_URL}/admin/feedback`, { headers: adminHeaders(idToken) })
  if (!res.ok) throw new Error(`Failed to load feedback: ${res.status}`)
  return res.json()
}

export async function setFeedbackRead(
  idToken: string,
  feedbackId: string,
  read: boolean
): Promise<FeedbackSubmission> {
  const res = await fetch(`${BACKEND_URL}/admin/feedback/${feedbackId}`, {
    method: "PATCH",
    headers: adminHeaders(idToken),
    body: JSON.stringify({ read }),
  })
  if (!res.ok) throw new Error(`Failed to update feedback: ${res.status}`)
  return res.json()
}

export async function summarizeFeedback(idToken: string): Promise<{ summary: string | null }> {
  const res = await fetch(`${BACKEND_URL}/admin/feedback/summarize`, {
    method: "POST",
    headers: adminHeaders(idToken),
  })
  if (!res.ok) throw new Error(`Failed to summarize feedback: ${res.status}`)
  return res.json()
}

export async function deleteFeedback(idToken: string, feedbackId: string): Promise<void> {
  const res = await fetch(`${BACKEND_URL}/admin/feedback/${feedbackId}`, {
    method: "DELETE",
    headers: adminHeaders(idToken),
  })
  if (!res.ok) throw new Error(`Failed to delete feedback: ${res.status}`)
}

export async function deleteFeedbackBatch(idToken: string, feedbackIds: string[]): Promise<void> {
  const res = await fetch(`${BACKEND_URL}/admin/feedback/bulk-delete`, {
    method: "POST",
    headers: adminHeaders(idToken),
    body: JSON.stringify({ feedback_ids: feedbackIds }),
  })
  if (!res.ok) throw new Error(`Failed to delete feedback: ${res.status}`)
}
