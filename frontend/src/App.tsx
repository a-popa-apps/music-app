import { Analytics } from "@vercel/analytics/react"
import { useEffect } from "react"
import { Route, Routes, useLocation } from "react-router-dom"
import { CookieConsentBanner } from "./components/CookieConsentBanner"
import { CustomCursor } from "./components/CustomCursor"
import { FAQ } from "./components/FAQ"
import { Features } from "./components/Features"
import { FeedbackWidget } from "./components/FeedbackWidget"
import { FinalCta } from "./components/FinalCta"
import { Footer } from "./components/Footer"
import { Header } from "./components/Header"
import { Hero } from "./components/Hero"
import { HowItWorks } from "./components/HowItWorks"
import { Pricing } from "./components/Pricing"
import { ScrollProgress } from "./components/ScrollProgress"
import { AdminPage } from "./pages/AdminPage"
import { AdminUserDetail } from "./pages/AdminUserDetail"
import { AuthActionPage } from "./pages/AuthActionPage"
import { AuthPage } from "./pages/AuthPage"
import { CookiePolicyPage } from "./pages/CookiePolicyPage"
import { HistoryPage } from "./pages/HistoryPage"
import { NotFound } from "./pages/NotFound"
import { PrivacyPage } from "./pages/PrivacyPage"
import { ProfileDetails } from "./pages/ProfileDetails"
import { TermsPage } from "./pages/TermsPage"
import { trackPageView } from "./utils/analytics"

// GA's config() call passes send_page_view: false (see analytics.ts), so
// this is what actually reports page views -- both the initial load and
// every client-side route change, which a plain page_view config call
// would otherwise miss entirely in a single-page app. No-ops until
// analytics consent has been granted.
function PageViewTracker() {
  const location = useLocation()
  useEffect(() => {
    trackPageView(location.pathname)
  }, [location.pathname])
  return null
}

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
        <FinalCta />
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
        <Route path="/cookie-policy" element={<CookiePolicyPage />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
      <PageViewTracker />
      <FeedbackWidget />
      <CookieConsentBanner />
      <Analytics />
      <ScrollProgress />
      <CustomCursor />
    </>
  )
}

export default App
