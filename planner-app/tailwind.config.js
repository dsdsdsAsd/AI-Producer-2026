/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                background: "#0f0f11", // The specific dark background user likes
                surface: "#1a1a1d",
                primary: "#3b82f6", // Blue for actions
                accent: "#10b981", // Green for success
                text: "#ffffff",
                textMuted: "#a1a1aa",
            },
            fontFamily: {
                sans: ['Inter', 'sans-serif'],
            },
        },
    },
    plugins: [],
}
