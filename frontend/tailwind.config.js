/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                primary: {
                    50: '#f0f9ff',
                    100: '#e0f2fe',
                    200: '#bae6fd',
                    300: '#7dd3fc',
                    400: '#38bdf8',
                    500: '#1e3a8a',
                    600: '#2c5aa0',
                    700: '#1e40af',
                    800: '#1e3a8a',
                    900: '#172554',
                },
                secondary: {
                    50: '#faf5ff',
                    100: '#f3e8ff',
                    200: '#e9d5ff',
                    300: '#d8b4fe',
                    400: '#c084fc',
                    500: '#a855f7',
                    600: '#9333ea',
                    700: '#7e22ce',
                    800: '#6b21a8',
                    900: '#581c87',
                },
                accent: {
                    50: '#ecfdf5',
                    100: '#d1fae5',
                    200: '#a7f3d0',
                    300: '#6ee7b7',
                    400: '#34d399',
                    500: '#10b981',
                    600: '#059669',
                    700: '#047857',
                    800: '#065f46',
                    900: '#064e3b',
                },
            },
            fontFamily: {
                sans: ['Pretendard', 'Inter', '-apple-system', 'BlinkMacSystemFont', 'system-ui', 'sans-serif'],
            },
            boxShadow: {
                'glass': '0 8px 32px 0 rgba(31, 38, 135, 0.15)',
                'glass-lg': '0 20px 60px 0 rgba(31, 38, 135, 0.2)',
                'premium': '0 25px 60px rgba(30, 58, 138, 0.2), 0 0 0 1px rgba(44, 90, 160, 0.1)',
            },
            backgroundImage: {
                'gradient-primary': 'linear-gradient(135deg, #1e3a8a 0%, #2c5aa0 50%, #3b82f6 100%)',
                'gradient-premium': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                'gradient-mesh': 'radial-gradient(at 40% 20%, hsla(28,100%,74%,0.3) 0px, transparent 50%), radial-gradient(at 80% 0%, hsla(189,100%,56%,0.3) 0px, transparent 50%), radial-gradient(at 0% 50%, hsla(355,100%,93%,0.3) 0px, transparent 50%), radial-gradient(at 80% 50%, hsla(340,100%,76%,0.3) 0px, transparent 50%), radial-gradient(at 0% 100%, hsla(22,100%,77%,0.3) 0px, transparent 50%), radial-gradient(at 80% 100%, hsla(242,100%,70%,0.3) 0px, transparent 50%), radial-gradient(at 0% 0%, hsla(343,100%,76%,0.3) 0px, transparent 50%)',
            },
            backdropBlur: {
                xs: '2px',
            },
            animation: {
                'fade-in': 'fadeIn 0.3s ease-in-out',
                'slide-up': 'slideUp 0.3s ease-out',
                'slide-down': 'slideDown 0.3s ease-out',
                'blob': 'blob 7s infinite',
            },
            keyframes: {
                fadeIn: {
                    '0%': {
                        opacity: '0'
                    },
                    '100%': {
                        opacity: '1'
                    },
                },
                slideUp: {
                    '0%': {
                        transform: 'translateY(10px)',
                        opacity: '0'
                    },
                    '100%': {
                        transform: 'translateY(0)',
                        opacity: '1'
                    },
                },
                slideDown: {
                    '0%': {
                        transform: 'translateY(-10px)',
                        opacity: '0'
                    },
                    '100%': {
                        transform: 'translateY(0)',
                        opacity: '1'
                    },
                },
                blob: {
                    '0%': {
                        transform: 'translate(0px, 0px) scale(1)'
                    },
                    '33%': {
                        transform: 'translate(30px, -50px) scale(1.1)'
                    },
                    '66%': {
                        transform: 'translate(-20px, 20px) scale(0.9)'
                    },
                    '100%': {
                        transform: 'translate(0px, 0px) scale(1)'
                    },
                },
            },
        },
    },
    plugins: [],
}