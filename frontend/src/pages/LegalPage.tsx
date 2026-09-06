import type { ReactNode } from "react"
import { Header } from "../components/Header"

interface Section {
  heading: string
  body: ReactNode
}

export function LegalPage({ title, sections }: { title: string; sections: Section[] }) {
  return (
    <>
      <Header dark />
      <div className="min-h-screen w-full bg-black px-4 py-12 pt-32">
        <div className="mx-auto max-w-2xl">
          <div className="mb-6 rounded border border-orange-400/30 bg-orange-500/10 px-4 py-3 text-body-sm text-orange-300">
            <strong>Draft placeholder.</strong> This page is a structural
            skeleton, not reviewed legal text. Replace this content with
            real legal copy (ideally reviewed by a lawyer or a proper
            policy generator) before any public launch.
          </div>

          <h1 className="mb-8 text-headline-lg text-white">{title}</h1>

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
    </>
  )
}
