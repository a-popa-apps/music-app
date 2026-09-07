import { useState } from "react"

const FAQS = [
  {
    question: "What is CratePrep?",
    answer:
      "CratePrep is a web tool for DJs that cleans up messy downloaded tracks in your browser: it strips junk from filenames, detects BPM and musical key, tags genre and energy, and hands you back a ready-to-gig playlist — no software to install.",
  },
  {
    question: "Which DJ software does CratePrep support?",
    answer:
      "Every track is tagged with the correct BPM, key, and genre before you download, so Rekordbox, Serato, and Traktor all recognize it right away when you add it to your library — no export file or software-specific step needed.",
  },
  {
    question: "What audio formats do you support?",
    answer:
      "MP3, WAV, AIFF, and FLAC — the formats DJs use the most.",
  },
  {
    question: "Does it run on my phone or tablet?",
    answer:
      "Yes, although we don't recommend it — dragging in a whole download folder and reviewing results is a much better experience on a laptop or desktop.",
  },
  {
    question: "Does CratePrep overwrite my original audio files?",
    answer:
      "Never. CratePrep creates a clean replica and exports your tracks with corrected metadata, leaving your original download folder completely untouched.",
  },
  {
    question: "Do my tracks get stored on your servers?",
    answer:
      "No. Files are processed in memory for the duration of a single request and streamed straight back to you as a ZIP — nothing is written to persistent storage.",
  },
  {
    question: "How accurate is the BPM and key detection?",
    answer:
      "CratePrep uses librosa and essentia, industry-standard open-source audio analysis libraries, tuned for modern dance music transients and bass frequencies.",
  },
]

export function FAQ() {
  const [openIndex, setOpenIndex] = useState<number | null>(null)

  return (
    <section id="faq" className="relative w-full overflow-hidden bg-black px-4 py-16 lg:px-12">
      <div className="relative z-10 mx-auto flex max-w-4xl flex-col gap-12">
        <div className="flex flex-col gap-1 text-center">
          <span className="font-mono text-meta-badge font-bold uppercase tracking-wider text-secondary-container">
            Clear Answers
          </span>
          <h2 className="text-headline-xl tracking-tight text-white">
            Frequently Asked Questions
          </h2>
        </div>

        <div className="flex flex-col gap-4">
          {FAQS.map((faq, i) => {
            const isOpen = openIndex === i
            return (
              <div
                key={faq.question}
                className="rounded border border-white/10 bg-white/10 p-6 backdrop-blur-md"
              >
                <button
                  onClick={() => setOpenIndex(isOpen ? null : i)}
                  aria-expanded={isOpen}
                  className="flex w-full items-center justify-between text-left text-headline-sm text-white"
                >
                  <span>{faq.question}</span>
                  <span
                    className={`material-symbols-outlined text-white/60 transition-transform ${
                      isOpen ? "rotate-180" : ""
                    }`}
                  >
                    expand_more
                  </span>
                </button>
                {isOpen && (
                  <div className="mt-2 text-body-md text-white/70">
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
