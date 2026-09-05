import type { ReactNode } from "react"
import { Header } from "../components/Header"

interface Section {
  heading: string
  body: ReactNode
}

export function LegalPage({ title, sections }: { title: string; sections: Section[] }) {
  return (
    <>
      <Header />
      <div className="min-h-screen w-full bg-surface px-4 py-12 pt-32">
        <div className="mx-auto max-w-2xl">
          <div className="mb-6 rounded border border-orange-300 bg-orange-50 px-4 py-3 text-body-sm text-orange-800">
            <strong>Draft placeholder.</strong> This page is a structural
            skeleton, not reviewed legal text. Replace this content with
            real Terms/Privacy copy (ideally reviewed by a lawyer or a
            proper policy generator) before any public launch.
          </div>

          <h1 className="mb-8 text-headline-lg text-on-surface">{title}</h1>

          <div className="flex flex-col gap-6 rounded bg-surface-container-lowest p-8 shadow-sm">
            {sections.map((section) => (
              <div key={section.heading}>
                <h2 className="mb-2 text-headline-sm text-on-surface">
                  {section.heading}
                </h2>
                <div className="text-body-md text-on-surface-variant">{section.body}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </>
  )
}
