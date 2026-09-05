import { Route, Routes } from "react-router-dom"
import { FAQ } from "./components/FAQ"
import { Features } from "./components/Features"
import { Footer } from "./components/Footer"
import { Header } from "./components/Header"
import { Hero } from "./components/Hero"
import { HowItWorks } from "./components/HowItWorks"
import { Pricing } from "./components/Pricing"
import { UploadDemo } from "./components/UploadDemo"
import { AuthPage } from "./pages/AuthPage"
import { ProfileDetails } from "./pages/ProfileDetails"

function Landing() {
  return (
    <>
      <Header />
      <main className="w-full pt-16">
        <Hero />
        <HowItWorks />
        <UploadDemo />
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
    </Routes>
  )
}

export default App
