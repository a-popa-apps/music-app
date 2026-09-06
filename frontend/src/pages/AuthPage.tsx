import { useState } from "react"
import { Navigate, useNavigate } from "react-router-dom"
import { Header } from "../components/Header"
import { useAuth } from "../hooks/useAuth"
import { checkPwnedPassword } from "../utils/checkPwnedPassword"

type Mode = "login" | "signup"
type View = "form" | "check-inbox"

function firebaseErrorMessage(error: unknown): string {
  const code = (error as { code?: string })?.code ?? ""
  if (code.includes("email-already-in-use")) return "That email is already registered."
  if (code.includes("invalid-credential") || code.includes("wrong-password"))
    return "Incorrect email or password."
  if (code.includes("user-not-found")) return "No account found with that email."
  if (code.includes("weak-password")) return "Password should be at least 6 characters."
  if (code.includes("invalid-email")) return "That doesn't look like a valid email."
  if (code.includes("unauthorized-domain"))
    return "This domain isn't authorized for sign-in yet. (Add it in Firebase Console → Authentication → Settings → Authorized domains.)"
  if (code.includes("operation-not-allowed"))
    return "This sign-in method isn't enabled yet. (Check Firebase Console → Authentication → Sign-in method.)"
  if (code.includes("network-request-failed"))
    return "Network error. Check your connection and try again."
  console.error("Unhandled auth error:", error)
  return code ? `Something went wrong (${code}). Please try again.` : "Something went wrong. Please try again."
}

export function AuthPage() {
  const { user, isVerified, signUp, logIn, signInWithGoogle, resendVerification } = useAuth()
  const navigate = useNavigate()

  const [mode, setMode] = useState<Mode>("login")
  const [view, setView] = useState<View>("form")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [acceptedTerms, setAcceptedTerms] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      if (mode === "signup") {
        const breachCount = await checkPwnedPassword(password)
        if (breachCount) {
          setError(
            "This password has appeared in known data breaches. Please choose a different one."
          )
          return
        }
        await signUp(email, password)
        setView("check-inbox")
      } else {
        const user = await logIn(email, password)
        if (user.emailVerified) {
          navigate("/")
        } else {
          setView("check-inbox")
        }
      }
    } catch (err) {
      setError(firebaseErrorMessage(err))
    } finally {
      setSubmitting(false)
    }
  }

  async function handleGoogle() {
    setError(null)
    try {
      await signInWithGoogle()
      navigate("/")
    } catch {
      setError("Google sign-in failed. Please try again.")
    }
  }

  async function handleResend() {
    setError(null)
    try {
      await resendVerification()
    } catch {
      setError("Couldn't resend the email. Try logging in again.")
    }
  }

  if (user && isVerified) {
    return <Navigate to="/" replace />
  }

  return (
    <>
      <Header dark />
      <div className="flex min-h-screen w-full items-center justify-center bg-black px-4 py-12 pt-32">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <span className="font-mono text-headline-lg font-bold tracking-tight text-white">
            crateprep.
          </span>
        </div>

        <div className="rounded border border-white/10 bg-white/10 p-8 backdrop-blur-md">
          {view === "check-inbox" ? (
            <div className="flex flex-col items-center text-center">
              <div className="mb-4 text-5xl">📬</div>
              <h1 className="mb-2 text-headline-lg text-white">Check your inbox</h1>
              <p className="mb-6 text-body-md text-white/70">
                We sent a confirmation link to <strong>{email}</strong>. Click it to
                activate your account, then come back to log in.
              </p>
              <p className="mb-6 text-body-sm text-white/60">
                Don't see it? Check your spam or junk folder — it can take a minute to
                arrive.
              </p>
              <button
                onClick={handleResend}
                className="mb-4 w-full rounded-full border border-white/20 px-6 py-3 text-body-md font-semibold text-white transition-colors hover:bg-white/10"
              >
                Resend verification email
              </button>
              <button
                onClick={() => {
                  setView("form")
                  setMode("signup")
                }}
                className="text-body-sm text-white/60 underline hover:text-white"
              >
                Use a different email
              </button>
              {error && <p className="mt-4 text-body-sm text-red-400">{error}</p>}
            </div>
          ) : (
            <>
              <div className="mb-6 flex rounded-full bg-white/5 p-1">
                <button
                  onClick={() => setMode("login")}
                  className={`flex-1 rounded-full py-2 text-body-md font-semibold transition-colors ${
                    mode === "login"
                      ? "bg-white/15 text-white"
                      : "text-white/60"
                  }`}
                >
                  Log in
                </button>
                <button
                  onClick={() => setMode("signup")}
                  className={`flex-1 rounded-full py-2 text-body-md font-semibold transition-colors ${
                    mode === "signup"
                      ? "bg-white/15 text-white"
                      : "text-white/60"
                  }`}
                >
                  Sign up
                </button>
              </div>

              <form onSubmit={handleSubmit} className="flex flex-col gap-4">
                <label className="flex flex-col gap-1">
                  <span className="text-body-sm font-semibold text-white">Email</span>
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="rounded border border-white/20 bg-white/5 px-4 py-3 text-body-md text-white outline-none focus:border-secondary-container"
                  />
                </label>

                <label className="flex flex-col gap-1">
                  <span className="text-body-sm font-semibold text-white">
                    Password
                  </span>
                  <input
                    type="password"
                    required
                    minLength={6}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="rounded border border-white/20 bg-white/5 px-4 py-3 text-body-md text-white outline-none focus:border-secondary-container"
                  />
                </label>

                {mode === "signup" && (
                  <label className="flex items-start gap-2 text-body-sm text-white/70">
                    <input
                      type="checkbox"
                      required
                      checked={acceptedTerms}
                      onChange={(e) => setAcceptedTerms(e.target.checked)}
                      className="mt-0.5"
                    />
                    <span>
                      I accept the{" "}
                      <a href="/terms" className="underline">
                        Terms and Conditions
                      </a>{" "}
                      and{" "}
                      <a href="/privacy" className="underline">
                        Privacy Policy
                      </a>
                      .
                    </span>
                  </label>
                )}

                {error && <p className="text-body-sm text-red-400">{error}</p>}

                <button
                  type="submit"
                  disabled={submitting || (mode === "signup" && !acceptedTerms)}
                  className="rounded-full bg-secondary-container px-6 py-3 text-headline-sm font-semibold text-on-primary transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
                >
                  {mode === "signup" ? "Create account" : "Log in"}
                </button>
              </form>

              <div className="my-6 flex items-center gap-4">
                <div className="h-px flex-1 bg-white/10" />
                <span className="text-body-sm text-white/60">OR</span>
                <div className="h-px flex-1 bg-white/10" />
              </div>

              <button
                onClick={handleGoogle}
                className="w-full rounded-full border border-white/20 bg-white/5 px-6 py-3 text-body-md font-semibold text-white transition-colors hover:bg-white/10"
              >
                Continue with Google
              </button>
            </>
          )}
        </div>
      </div>
      </div>
    </>
  )
}
