import React from 'react'

export function CallToAction() {
  const scrollToAnalyzer = () => {
    const analyzerSection = document.getElementById('analyzer')
    if (analyzerSection) {
      analyzerSection.scrollIntoView({ behavior: 'smooth' })
    }
  }
  return (
    <section className="py-16 text-center">
      <div className="max-w-3xl mx-auto px-4">
        <h2 className="text-3xl font-heading font-bold mb-6 text-[var(--color-text)]">
          Stay safe from phishing today.
        </h2>
        <button
          onClick={scrollToAnalyzer}
          className="px-8 py-3 text-lg font-medium text-white bg-primary rounded shadow-crisp hover:shadow-lg transform hover:-translate-y-0.5 transition-all duration-200"
        >
          Try for Free
        </button>
      </div>
    </section>
  )
}

