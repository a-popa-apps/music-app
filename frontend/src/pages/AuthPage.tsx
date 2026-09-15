import { Navigate, useNavigate } from "react-router-dom"
import { AuthForm } from "../components/AuthForm"
import { Header } from "../components/Header"
import { useAuth } from "../hooks/useAuth"

export function AuthPage() {
  const { user, isVerified } = useAuth()
  const navigate = useNavigate()

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
            <AuthForm onSuccess={() => navigate("/")} />
          </div>
        </div>
      </div>
    </>
  )
}
