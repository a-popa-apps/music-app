import {
  createUserWithEmailAndPassword,
  GoogleAuthProvider,
  onAuthStateChanged,
  sendEmailVerification,
  sendPasswordResetEmail,
  signInWithEmailAndPassword,
  signInWithPopup,
  signOut,
  type User,
} from "firebase/auth"
import { useEffect, useState } from "react"
import { auth } from "../firebase"

// Firebase's default verification/reset links land on a generic
// Firebase-hosted page with no way back to the app. Pointing them at our
// own /auth/action route instead lets us show a branded confirmation (or
// a proper "set new password" form) and redirect back here.
const authActionSettings = {
  url: `${window.location.origin}/auth/action`,
}

export function useAuth() {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    return onAuthStateChanged(auth, (u) => {
      setUser(u)
      setLoading(false)
    })
  }, [])

  return {
    user,
    loading,
    isVerified: user?.emailVerified ?? false,

    async signUp(email: string, password: string) {
      const credential = await createUserWithEmailAndPassword(auth, email, password)
      await sendEmailVerification(credential.user, authActionSettings)
      return credential.user
    },

    async logIn(email: string, password: string) {
      const credential = await signInWithEmailAndPassword(auth, email, password)
      return credential.user
    },

    async signInWithGoogle() {
      const credential = await signInWithPopup(auth, new GoogleAuthProvider())
      return credential.user
    },

    async resendVerification() {
      if (auth.currentUser) {
        await sendEmailVerification(auth.currentUser, authActionSettings)
      }
    },

    async resetPassword(email: string) {
      await sendPasswordResetEmail(auth, email, authActionSettings)
    },

    async logOut() {
      await signOut(auth)
    },
  }
}
