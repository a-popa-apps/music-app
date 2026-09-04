import { useState } from "react"

const FAQS = [
  {
    question: "Does Quickie overwrite my original audio files?",
    answer:
      "Never. Quickie creates a clean replica and exports your tracks with corrected metadata, leaving your original download folder completely untouched.",
  },
  {
    question: "Which DJ software does Quickie support?",
    answer:
      "Quickie generates Rekordbox-compatible playlists and formatted folder hierarchies ready for direct Pioneer CDJ USB stick mounting. Serato and Traktor export are on the roadmap.",
  },
  {
    question: "Do my tracks get stored on your servers?",
    answer:
      "No. Files are processed in memory for the duration of a single request and streamed straight back to you as a ZIP — nothing is written to persistent storage.",
  },
  {
    question: "How accurate is the BPM and key detection?",
    answer:
      "Quickie uses librosa and essentia, industry-standard open-source audio analysis libraries, tuned for modern dance music transients and bass frequencies.",
  },
]

export function FAQ() {
  const [openIndex, setOpenIndex] = useState<number | null>(null)

  return (
    <section
      id="faq"
      className="w-full bg-surface-container-low px-4 py-16 lg:px-12"
    >
      <div className="mx-auto flex max-w-4xl flex-col gap-12">
        <div className="flex flex-col gap-1 text-center">
          <span className="font-mono text-meta-badge font-bold uppercase tracking-wider text-secondary-container">
            Clear Answers
          </span>
          <h2 className="text-headline-xl tracking-tight text-on-surface">
            Frequently Asked Questions
          </h2>
        </div>

        <div className="flex flex-col gap-4">
          {FAQS.map((faq, i) => {
            const isOpen = openIndex === i
            return (
              <div
                key={faq.question}
                className="rounded bg-surface-container-lowest p-6 shadow-sm"
              >
                <button
                  onClick={() => setOpenIndex(isOpen ? null : i)}
                  className="flex w-full items-center justify-between text-left text-headline-sm text-on-surface"
                >
                  <span>{faq.question}</span>
                  <span
                    className={`material-symbols-outlined text-on-surface-variant transition-transform ${
                      isOpen ? "rotate-180" : ""
                    }`}
                  >
                    expand_more
                  </span>
                </button>
                {isOpen && (
                  <div className="mt-2 text-body-md text-on-surface-variant">
                    {faq.answer}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>
    </section>
  )
}
