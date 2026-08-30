import React, { useEffect, useState } from 'react'
import { Header } from './components/Header'
import { Hero } from './components/Hero'
// import { Features } from './components/Features'
import AnalyzerTabs from './components/AnalyzerTabs'
import { TechStack } from './components/TechStack'
import { CallToAction } from './components/CallToAction'
import { Footer } from './components/Footer'

export function App() {
  const [darkMode, setDarkMode] = useState(() => {
    try {
      const saved = localStorage.getItem('theme')
      if (saved) return saved === 'dark'
      return window.matchMedia('(prefers-color-scheme: dark)').matches
    } catch {
      return false
    }
  })
  const toggleDarkMode = () => setDarkMode((d) => !d)

  useEffect(() => {
    try {
      localStorage.setItem('theme', darkMode ? 'dark' : 'light')
    } catch {
      /* ignore */
    }
  }, [darkMode])

  return (
    <div className={`${darkMode ? 'dark' : ''} min-h-screen transition-colors duration-300`}>
      <div className="bg-[var(--color-bg)]">
        <Header darkMode={darkMode} toggleDarkMode={toggleDarkMode} />
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <Hero />
          {/* Features section removed */}
          <AnalyzerTabs />
          <TechStack />
          <CallToAction />
          <Footer />
        </div>
      </div>
    </div>
  )
}
