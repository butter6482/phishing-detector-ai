import React from 'react'
import { ShieldIcon } from 'lucide-react'
import securityIllustration from '../assets/security-illustration.svg'

export function Hero() {
  const scrollToAnalyzer = () => {
    const analyzerSection = document.getElementById('analyzer')
    if (analyzerSection) {
      analyzerSection.scrollIntoView({ behavior: 'smooth' })
    }
  }
  return (
    <section className="py-16 md:py-24">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-center">
        <div>
          <h1 className="text-4xl md:text-5xl font-heading font-bold mb-4 text-[var(--color-text)]">
            Detect phishing in seconds.
          </h1>
          <p className="text-xl mb-8 text-[var(--color-text)] opacity-80 max-w-md">
            Analyze email text or screenshots. Get a risk score, suspicious keywords, and an AI explanation.
          </p>
          <div className="flex flex-wrap gap-4">
            <button
              onClick={scrollToAnalyzer}
              className="px-6 py-3 bg-primary text-white rounded font-medium shadow-crisp hover:shadow-lg transform hover:-translate-y-0.5 transition-all duration-200"
            >
              Try Now
            </button>
            <a
              href="https://github.com/butter6482"
              target="_blank"
              rel="noopener noreferrer"
              className="px-6 py-3 border border-[var(--color-border)] rounded font-medium hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors dark:text-white"
            >
              View on GitHub
            </a>
          </div>
        </div>
        <div className="flex justify-center md:justify-end">
          <div className="bg-white dark:bg-gray-800 rounded shadow-crisp p-6 max-w-md backdrop-blur-sm bg-opacity-80 dark:bg-opacity-80 border border-[var(--color-border)]">
            <img
              src={securityIllustration}
              alt="Security illustration: shield, envelope and phishing hook"
              className="w-full h-auto rounded"
            />
          </div>
        </div>
      </div>
    </section>
  )
}
