import React from 'react'
import { GithubIcon, MailIcon } from 'lucide-react'

export function Footer() {
  return (
    <footer className="py-8 border-t border-[var(--color-border)]">
      <div className="flex flex-col md:flex-row justify-between items-center">
        <p className="text-[var(--color-text)] opacity-70 mb-4 md:mb-0">© Alejandro Butter · Puerto Rico</p>
        <div className="flex space-x-6">
          <a
            href="https://github.com/butter6482"
            target="_blank"
            rel="noopener noreferrer"
            className="text-[var(--color-text)] opacity-70 hover:opacity-100 transition-colors"
          >
            <GithubIcon className="h-5 w-5" />
            <span className="sr-only">GitHub</span>
          </a>
          <a
            href="mailto:alejandrobutter316@gmail.com"
            className="text-[var(--color-text)] opacity-70 hover:opacity-100 transition-colors"
          >
            <MailIcon className="h-5 w-5" />
            <span className="sr-only">Email</span>
          </a>
        </div>
      </div>
    </footer>
  )
}

