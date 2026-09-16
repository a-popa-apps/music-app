import { useEffect, useState } from "react"
import { Navigate, useNavigate, useSearchParams } from "react-router-dom"
import { AuthForm } from "../components/AuthForm"
import { Header } from "../components/Header"
import { useAuth } from "../hooks/useAuth"
import { getInvitePreview, type InvitePreview } from "../services/api"

export function AuthPage() {
  const { user, isVerified } = useAuth()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const inviteToken = searchParams.get("invite") ?? undefined
  const [invite, setInvite] = useState<InvitePreview | null>(null)

  useEffect(() => {
    if (!inviteToken) return
    getInvitePreview(inviteToken).then(setInvite)
  }, [inviteToken])

  if (user && isVerified) {
    return <Navigate to="/" replace />
  }

  const inviteBanner =
    invite?.valid && invite.inviter_label
      ? `${invite.inviter_label} invited you to CratePrep${invite.name ? `, ${invite.name}` : ""}!`
      : undefined

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
            <AuthForm
              onSuccess={() => navigate("/")}
              initialEmail={invite?.valid ? invite.email : undefined}
              inviteToken={invite?.valid ? inviteToken : undefined}
              inviteBanner={inviteBanner}
            />
          </div>
        </div>
      </div>
    </>
  )
}
