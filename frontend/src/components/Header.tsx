import React from 'react'
import { ShieldIcon, SunIcon, MoonIcon } from 'lucide-react'

type Props = {
  darkMode: boolean
  toggleDarkMode: () => void
}

export function Header({ darkMode, toggleDarkMode }: Props) {
  const scrollToAnalyzer = () => {
    const analyzerSection = document.getElementById('analyzer')
    if (analyzerSection) {
      analyzerSection.scrollIntoView({ behavior: 'smooth' })
    }
  }

  return (
    <header className="sticky top-0 z-10 bg-[var(--color-bg)] border-b border-[var(--color-border)]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center">
            <ShieldIcon className="h-8 w-8 text-primary" />
            <span className="ml-2 text-lg font-heading font-semibold text-[var(--color-text)]">
              Phishing Detector
            </span>
          </div>
          <div className="hidden md:flex items-center space-x-8">
            <a
              href="https://github.com/butter6482/phishing-detector-ai"
              target="_blank"
              rel="noopener noreferrer"
              className="text-[var(--color-text)] hover:text-primary transition-colors"
            >
              GitHub
            </a>
            <button
              onClick={scrollToAnalyzer}
              className="px-4 py-2 bg-primary text-white rounded font-medium hover:shadow-md transition-shadow"
            >
              Try Now
            </button>
            <button
              onClick={toggleDarkMode}
              className="p-2 rounded bg-white dark:bg-gray-800 shadow-md hover:shadow-lg transition-shadow"
              aria-label="Toggle dark mode"
            >
              {darkMode ? (
                <SunIcon className="h-5 w-5 text-yellow-400" />
              ) : (
                <MoonIcon className="h-5 w-5 text-gray-700" />
              )}
            </button>
          </div>
          <div className="md:hidden flex items-center space-x-4">
            <button
              onClick={scrollToAnalyzer}
              className="px-3 py-1 bg-primary text-white rounded font-medium text-sm"
            >
              Try Now
            </button>
            <button
              onClick={toggleDarkMode}
              className="p-1.5 rounded bg-white dark:bg-gray-800 shadow-md"
              aria-label="Toggle dark mode"
            >
              {darkMode ? (
                <SunIcon className="h-4 w-4 text-yellow-400" />
              ) : (
                <MoonIcon className="h-4 w-4 text-gray-700" />
              )}
            </button>
          </div>
        </div>
      </div>
    </header>
  )
}

