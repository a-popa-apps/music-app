import type { ReactNode } from "react"
import { Footer } from "../components/Footer"
import { Header } from "../components/Header"
import { useDocumentHead } from "../hooks/useDocumentHead"

interface Section {
  heading: string
  body: ReactNode
}

export function LegalPage({
  title,
  path,
  lastUpdated,
  sections,
}: {
  title: string
  path: string
  lastUpdated: string
  sections: Section[]
}) {
  useDocumentHead(title, `${title} for CratePrep, the browser-based BPM, key, and genre detection tool for DJs.`, path)

  return (
    <>
      <Header dark />
      <div className="min-h-screen w-full bg-black px-4 py-12 pt-32">
        <div className="mx-auto max-w-2xl">
          <h1 className="mb-1 text-headline-lg text-white">{title}</h1>
          <p className="mb-8 text-body-sm text-white/50">Last updated: {lastUpdated}</p>

          <div className="flex flex-col gap-6 rounded border border-white/10 bg-white/10 p-8 backdrop-blur-md">
            {sections.map((section) => (
              <div key={section.heading}>
                <h2 className="mb-2 text-headline-sm text-white">
                  {section.heading}
                </h2>
                <div className="text-body-md text-white/70">{section.body}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
      <Footer />
    </>
  )
}
