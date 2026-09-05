import { Route, Routes } from "react-router-dom"
import { FAQ } from "./components/FAQ"
import { Features } from "./components/Features"
import { Footer } from "./components/Footer"
import { Header } from "./components/Header"
import { Hero } from "./components/Hero"
import { HowItWorks } from "./components/HowItWorks"
import { Pricing } from "./components/Pricing"
import { AdminPage } from "./pages/AdminPage"
import { AdminUserDetail } from "./pages/AdminUserDetail"
import { AuthPage } from "./pages/AuthPage"
import { NotFound } from "./pages/NotFound"
import { PrivacyPage } from "./pages/PrivacyPage"
import { ProfileDetails } from "./pages/ProfileDetails"
import { TermsPage } from "./pages/TermsPage"

function Landing() {
  return (
    <>
      <Header />
      <main className="w-full pt-16">
        <Hero />
        <HowItWorks />
        <Features />
        <Pricing />
        <FAQ />
      </main>
      <Footer />
    </>
  )
}

function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/auth" element={<AuthPage />} />
      <Route path="/profile" element={<ProfileDetails />} />
      <Route path="/admin" element={<AdminPage />} />
      <Route path="/admin/users/:uid" element={<AdminUserDetail />} />
      <Route path="/terms" element={<TermsPage />} />
      <Route path="/privacy" element={<PrivacyPage />} />
      <Route path="*" element={<NotFound />} />
    </Routes>
  )
}

export default App
