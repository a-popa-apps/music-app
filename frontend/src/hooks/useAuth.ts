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
      await sendEmailVerification(credential.user)
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
      if (auth.currentUser) await sendEmailVerification(auth.currentUser)
    },

    async resetPassword(email: string) {
      await sendPasswordResetEmail(auth, email)
    },

    async logOut() {
      await signOut(auth)
    },
  }
}
