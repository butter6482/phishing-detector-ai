/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['DM Sans', 'system-ui', 'sans-serif'],
        heading: ['Poppins', 'system-ui', 'sans-serif'],
      },
      colors: {
        primary: '#E16F45',
        accent: '#09D2A3',
        background: '#FAFAFA',
        textColor: '#180353',
        border: '#E5E7EB',
      },
      borderRadius: {
        DEFAULT: '8px',
      },
      boxShadow: {
        'crisp': '0 8px 24px rgba(0,0,0,0.12)',
      }
    },
  },
  plugins: [],
}

