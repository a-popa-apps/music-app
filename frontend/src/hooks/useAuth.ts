import {
  createUserWithEmailAndPassword,
  getAdditionalUserInfo,
  GoogleAuthProvider,
  onAuthStateChanged,
  signInWithEmailAndPassword,
  signInWithPopup,
  signOut,
  type User,
} from "firebase/auth"
import { useEffect, useState } from "react"
import { auth } from "../firebase"
import { forgotPassword, sendVerificationEmail } from "../services/api"

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
      await sendVerificationEmail(await credential.user.getIdToken())
      return credential.user
    },

    async logIn(email: string, password: string) {
      const credential = await signInWithEmailAndPassword(auth, email, password)
      return credential.user
    },

    async signInWithGoogle() {
      const credential = await signInWithPopup(auth, new GoogleAuthProvider())
      const isNewUser = getAdditionalUserInfo(credential)?.isNewUser ?? false
      return { user: credential.user, isNewUser }
    },

    async resendVerification() {
      if (auth.currentUser) {
        await sendVerificationEmail(await auth.currentUser.getIdToken())
      }
    },

    async resetPassword(email: string) {
      await forgotPassword(email)
    },

    async logOut() {
      await signOut(auth)
    },
  }
}
