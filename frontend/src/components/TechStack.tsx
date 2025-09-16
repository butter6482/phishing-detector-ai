import React from 'react'

export function TechStack() {
  const technologies = [
    'Python',
    'FastAPI',
    'scikit-learn',
    'Pandas',
    'OCR',
    'React',
    'Vite',
    'TailwindCSS',
    'TypeScript',
    'Docker',
    'GitHub Actions',
    'Vercel/Render',
  ]
  return (
    <section className="py-16">
      <h2 className="text-3xl font-heading font-bold text-center mb-12 text-[var(--color-text)]">
        Tech Behind the Detector
      </h2>
      <div className="max-w-4xl mx-auto">
        <div className="flex flex-wrap justify-center gap-3">
          {technologies.map((tech) => (
            <span
              key={tech}
              className="px-4 py-2 bg-white dark:bg-gray-800 text-[var(--color-text)] rounded-full shadow-sm border border-[var(--color-border)] text-sm font-medium"
            >
              {tech}
            </span>
          ))}
        </div>
      </div>
    </section>
  )
}

