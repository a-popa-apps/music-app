import { applyActionCode, confirmPasswordReset, verifyPasswordResetCode } from "firebase/auth"
import { useEffect, useState } from "react"
import { useNavigate, useSearchParams } from "react-router-dom"
import { Header } from "../components/Header"
import { auth } from "../firebase"
import { checkPwnedPassword } from "../utils/checkPwnedPassword"

const REDIRECT_DELAY_SECONDS = 4

type Status =
  | "checking"
  | "verified"
  | "reset-form"
  | "reset-success"
  | "error"

export function AuthActionPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const [status, setStatus] = useState<Status>("checking")
  const [secondsLeft, setSecondsLeft] = useState(REDIRECT_DELAY_SECONDS)
  const [resetEmail, setResetEmail] = useState<string | null>(null)

  const [newPassword, setNewPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [resetError, setResetError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const mode = searchParams.get("mode")
  const oobCode = searchParams.get("oobCode")

  useEffect(() => {
    if (!oobCode) {
      setStatus("error")
      return
    }

    let cancelled = false
    async function run() {
      try {
        if (mode === "verifyEmail") {
          await applyActionCode(auth, oobCode!)
          // Refresh the local user object if this browser happens to be
          // signed in as the account being verified -- harmless no-op
          // otherwise.
          await auth.currentUser?.reload().catch(() => {})
          if (!cancelled) setStatus("verified")
        } else if (mode === "resetPassword") {
          const email = await verifyPasswordResetCode(auth, oobCode!)
          if (!cancelled) {
            setResetEmail(email)
            setStatus("reset-form")
          }
        } else {
          if (!cancelled) setStatus("error")
        }
      } catch {
        if (!cancelled) setStatus("error")
      }
    }
    run()

    return () => {
      cancelled = true
    }
  }, [mode, oobCode])

  useEffect(() => {
    if (status !== "verified" && status !== "reset-success") return

    if (secondsLeft <= 0) {
      navigate(status === "reset-success" ? "/auth" : "/")
      return
    }
    const timer = setTimeout(() => setSecondsLeft((s) => s - 1), 1000)
    return () => clearTimeout(timer)
  }, [status, secondsLeft, navigate])

  async function handleResetSubmit(e: React.FormEvent) {
    e.preventDefault()
    setResetError(null)

    if (newPassword !== confirmPassword) {
      setResetError("Passwords don't match.")
      return
    }
    if (newPassword.length < 6) {
      setResetError("Password should be at least 6 characters.")
      return
    }

    setSubmitting(true)
    try {
      const breachCount = await checkPwnedPassword(newPassword)
      if (breachCount) {
        setResetError(
          "This password has appeared in known data breaches. Please choose a different one."
        )
        return
      }
      await confirmPasswordReset(auth, oobCode!, newPassword)
      setStatus("reset-success")
    } catch {
      setResetError("Couldn't reset your password. The link may have expired -- try again.")
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <>
      <Header dark />
      <div className="flex min-h-screen w-full items-center justify-center bg-black px-4 py-12 pt-32">
        <div className="w-full max-w-md rounded border border-white/10 bg-white/10 p-8 text-center backdrop-blur-md">
          {status === "checking" && (
            <>
              <span className="material-symbols-outlined animate-spin text-[40px] text-secondary-container">
                progress_activity
              </span>
              <h1 className="mt-4 text-headline-lg text-white">One moment...</h1>
            </>
          )}

          {status === "verified" && (
            <>
              <span className="material-symbols-outlined text-[48px] text-green-400">
                check_circle
              </span>
              <h1 className="mt-4 text-headline-lg text-white">Email verified!</h1>
              <p className="mt-2 text-body-md text-white/70">
                Taking you to CratePrep in {secondsLeft}s...
              </p>
              <button
                onClick={() => navigate("/")}
                className="mt-6 rounded-full bg-secondary-container px-6 py-3 text-headline-sm font-semibold text-on-primary transition-opacity hover:opacity-90"
              >
                Go now
              </button>
            </>
          )}

          {status === "reset-form" && (
            <div className="text-left">
              <h1 className="text-center text-headline-lg text-white">
                Set a new password
              </h1>
              {resetEmail && (
                <p className="mt-2 text-center text-body-sm text-white/60">
                  for {resetEmail}
                </p>
              )}
              <form onSubmit={handleResetSubmit} className="mt-6 flex flex-col gap-4">
                <label className="flex flex-col gap-1">
                  <span className="text-body-sm font-semibold text-white">
                    New password
                  </span>
                  <input
                    type="password"
                    required
                    minLength={6}
                    autoFocus
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    className="rounded border border-white/20 bg-white/5 px-4 py-3 text-body-md text-white outline-none focus:border-secondary-container"
                  />
                </label>
                <label className="flex flex-col gap-1">
                  <span className="text-body-sm font-semibold text-white">
                    Confirm password
                  </span>
                  <input
                    type="password"
                    required
                    minLength={6}
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className="rounded border border-white/20 bg-white/5 px-4 py-3 text-body-md text-white outline-none focus:border-secondary-container"
                  />
                </label>
                {resetError && <p className="text-body-sm text-red-400">{resetError}</p>}
                <button
                  type="submit"
                  disabled={submitting}
                  className="rounded-full bg-secondary-container px-6 py-3 text-headline-sm font-semibold text-on-primary transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
                >
                  {submitting ? "Saving..." : "Save new password"}
                </button>
              </form>
            </div>
          )}

          {status === "reset-success" && (
            <>
              <span className="material-symbols-outlined text-[48px] text-green-400">
                check_circle
              </span>
              <h1 className="mt-4 text-headline-lg text-white">Password updated!</h1>
              <p className="mt-2 text-body-md text-white/70">
                Taking you to sign in in {secondsLeft}s...
              </p>
              <button
                onClick={() => navigate("/auth")}
                className="mt-6 rounded-full bg-secondary-container px-6 py-3 text-headline-sm font-semibold text-on-primary transition-opacity hover:opacity-90"
              >
                Go now
              </button>
            </>
          )}

          {status === "error" && (
            <>
              <span className="material-symbols-outlined text-[48px] text-red-400">error</span>
              <h1 className="mt-4 text-headline-lg text-white">
                This link is invalid or has expired
              </h1>
              <p className="mt-2 text-body-md text-white/70">
                Log in and request a new one from there.
              </p>
              <button
                onClick={() => navigate("/auth")}
                className="mt-6 rounded-full bg-secondary-container px-6 py-3 text-headline-sm font-semibold text-on-primary transition-opacity hover:opacity-90"
              >
                Back to sign in
              </button>
            </>
          )}
        </div>
      </div>
    </>
  )
}
