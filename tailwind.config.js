/** @type {import('tailwindcss').Config} */
const defaultTheme = require('tailwindcss/defaultTheme')

module.exports = {
  content: [
    "./src/api/templates/**/*.html",
    "./src/api/static/js/**/*.js"
  ],
  theme: {
    extend: {
      colors: {
        // The new dark mode palette (Charcoal & Slate)
        gray: {
          900: '#1a1b1e', // Main background
          850: '#1f2023', // Slightly lighter for depth
          800: '#25262b', // Card/Panel background
          750: '#2a2b31', // Card hover
          700: '#2c2e33', // Lighter borders/dividers
          600: '#373a40',
          500: '#5c5f66',
          400: '#909296', // Secondary text
          300: '#ced4da',
          200: '#e0e0e0', // Primary text color
          100: '#f1f3f5',
        },
        // Antique Gold Accent Palette
        gold: {
          300: '#e6c97a',
          400: '#d9b85c',
          500: '#C5A065', // Muted gold (borders, text)
          600: '#d4af37', // Metallic gold (active states, badges)
          700: '#b8942e',
          800: '#8a6f22',
          900: '#3E2F17', // Deep gold background context
        },
        // Status colors
        success: {
          400: '#5aac7d',
          500: '#4a9c6d',
          600: '#3d8a5d',
        },
        danger: {
          400: '#c46464',
          500: '#a85454',
          600: '#8a4545',
        }
      },
      fontFamily: {
        // Elegant Serif for Headers
        serif: ['Playfair Display', ...defaultTheme.fontFamily.serif],
        // Clean Sans for UI/Data
        sans: ['Inter', ...defaultTheme.fontFamily.sans],
      },
      boxShadow: {
        'soft': '0 4px 20px -2px rgba(0, 0, 0, 0.3)',
        'soft-lg': '0 8px 30px -4px rgba(0, 0, 0, 0.4)',
        'glow': '0 0 0 2px #C5A065',
        'glow-sm': '0 0 0 1px #C5A065',
        'card': '0 2px 8px rgba(0, 0, 0, 0.15)',
        'card-hover': '0 12px 40px rgba(0, 0, 0, 0.4)',
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-card': 'linear-gradient(to bottom, transparent, rgba(26, 27, 30, 0.95))',
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'slide-down': 'slideDown 0.3s ease-out',
        'spin-slow': 'spin 1.5s linear infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        slideDown: {
          '0%': { transform: 'translateY(-10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
      transitionDuration: {
        '400': '400ms',
      },
      backdropBlur: {
        'xs': '2px',
      },
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms')({
      strategy: 'class',
    }),
  ],
}
