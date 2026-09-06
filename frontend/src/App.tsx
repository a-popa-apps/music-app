import { Route, Routes } from "react-router-dom"
import bgSite from "./assets/bg-site.png"
import { FAQ } from "./components/FAQ"
import { Features } from "./components/Features"
import { FeedbackWidget } from "./components/FeedbackWidget"
import { Footer } from "./components/Footer"
import { Header } from "./components/Header"
import { Hero } from "./components/Hero"
import { HowItWorks } from "./components/HowItWorks"
import { Pricing } from "./components/Pricing"
import { AdminPage } from "./pages/AdminPage"
import { AdminUserDetail } from "./pages/AdminUserDetail"
import { AuthActionPage } from "./pages/AuthActionPage"
import { AuthPage } from "./pages/AuthPage"
import { HistoryPage } from "./pages/HistoryPage"
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
        {/* One continuous tiled background behind every section below the
            hero, applied once here rather than per-section, so the pattern
            is a single seamless canvas with no repeat-boundary at each
            section's edge. */}
        <div style={{ backgroundImage: `url(${bgSite})`, backgroundRepeat: "repeat" }}>
          <HowItWorks />
          <Features />
          <Pricing />
          <FAQ />
        </div>
      </main>
      <Footer />
    </>
  )
}

function App() {
  return (
    <>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/auth" element={<AuthPage />} />
        <Route path="/auth/action" element={<AuthActionPage />} />
        <Route path="/profile" element={<ProfileDetails />} />
        <Route path="/history" element={<HistoryPage />} />
        <Route path="/admin" element={<AdminPage />} />
        <Route path="/admin/users/:uid" element={<AdminUserDetail />} />
        <Route path="/terms" element={<TermsPage />} />
        <Route path="/privacy" element={<PrivacyPage />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
      <FeedbackWidget />
    </>
  )
}

export default App
