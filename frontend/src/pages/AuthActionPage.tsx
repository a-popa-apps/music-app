import { applyActionCode } from "firebase/auth"
import { useEffect, useState } from "react"
import { useNavigate, useSearchParams } from "react-router-dom"
import { Header } from "../components/Header"
import { auth } from "../firebase"

const REDIRECT_DELAY_SECONDS = 4

type Status = "verifying" | "verified" | "error"

export function AuthActionPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const [status, setStatus] = useState<Status>("verifying")
  const [secondsLeft, setSecondsLeft] = useState(REDIRECT_DELAY_SECONDS)

  const mode = searchParams.get("mode")
  const oobCode = searchParams.get("oobCode")

  useEffect(() => {
    if (mode !== "verifyEmail" || !oobCode) {
      setStatus("error")
      return
    }

    let cancelled = false
    async function verify() {
      try {
        await applyActionCode(auth, oobCode!)
        // Refresh the local user object if this browser happens to be signed
        // in as the account being verified -- harmless no-op otherwise.
        await auth.currentUser?.reload().catch(() => {})
        if (!cancelled) setStatus("verified")
      } catch {
        if (!cancelled) setStatus("error")
      }
    }
    verify()

    return () => {
      cancelled = true
    }
  }, [mode, oobCode])

  useEffect(() => {
    if (status !== "verified") return

    if (secondsLeft <= 0) {
      navigate("/")
      return
    }
    const timer = setTimeout(() => setSecondsLeft((s) => s - 1), 1000)
    return () => clearTimeout(timer)
  }, [status, secondsLeft, navigate])

  return (
    <>
      <Header />
      <div className="flex min-h-screen w-full items-center justify-center bg-surface px-4 py-12 pt-32">
        <div className="w-full max-w-md rounded bg-surface-container-lowest p-8 text-center shadow-md">
          {status === "verifying" && (
            <>
              <span className="material-symbols-outlined animate-spin text-[40px] text-secondary-container">
                progress_activity
              </span>
              <h1 className="mt-4 text-headline-lg text-on-surface">Verifying your email...</h1>
            </>
          )}

          {status === "verified" && (
            <>
              <span className="material-symbols-outlined text-[48px] text-green-600">
                check_circle
              </span>
              <h1 className="mt-4 text-headline-lg text-on-surface">Email verified!</h1>
              <p className="mt-2 text-body-md text-on-surface-variant">
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

          {status === "error" && (
            <>
              <span className="material-symbols-outlined text-[48px] text-red-600">error</span>
              <h1 className="mt-4 text-headline-lg text-on-surface">
                This link is invalid or has expired
              </h1>
              <p className="mt-2 text-body-md text-on-surface-variant">
                Log in and request a new verification email from there.
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
