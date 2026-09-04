import { FAQ } from "./components/FAQ"
import { Features } from "./components/Features"
import { Footer } from "./components/Footer"
import { Header } from "./components/Header"
import { Hero } from "./components/Hero"
import { HowItWorks } from "./components/HowItWorks"
import { Pricing } from "./components/Pricing"
import { UploadDemo } from "./components/UploadDemo"

function App() {
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

export default App
