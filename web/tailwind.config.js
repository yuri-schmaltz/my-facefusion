/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                surface: {
                    DEFAULT: '#09090b', // zinc-950
                    hover: '#18181b',   // zinc-900
                    active: '#27272a',  // zinc-800
                    border: '#27272a',  // zinc-800
                },
                primary: {
                    DEFAULT: '#10b981', // emerald-500
                    foreground: '#ecfdf5', // emerald-50
                    hover: '#059669',   // emerald-600
                    glow: 'rgba(16, 185, 129, 0.5)',
                },
                secondary: {
                    DEFAULT: '#8b5cf6', // violet-500
                    foreground: '#f5f3ff', // violet-50
                    hover: '#7c3aed',   // violet-600
                },
                accent: {
                    DEFAULT: '#f59e0b', // amber-500
                }
            },
            animation: {
                'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
                'glow': 'glow 2s ease-in-out infinite alternate',
            },
            keyframes: {
                glow: {
                    '0%': { boxShadow: '0 0 5px rgba(16, 185, 129, 0.2)' },
                    '100%': { boxShadow: '0 0 20px rgba(16, 185, 129, 0.6)' },
                }
            }
        },
    },
    plugins: [],
}
