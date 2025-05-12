/** @type {import('tailwindcss').Config} */
export default {
    content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
    theme: {
        extend: {
            colors: {
                border: "hsl(var(--border))",
                input: "hsl(var(--input))",
                ring: "hsl(var(--ring))",
                background: "hsl(var(--background))",
                foreground: "hsl(var(--foreground))",
                primary: {
                    DEFAULT: "hsl(var(--primary))",
                    foreground: "hsl(var(--primary-foreground))",
                },
                secondary: {
                    DEFAULT: "hsl(var(--secondary))",
                    foreground: "hsl(var(--secondary-foreground))",
                },
                destructive: {
                    DEFAULT: "hsl(var(--destructive))",
                    foreground: "hsl(var(--destructive-foreground))",
                },
                muted: {
                    DEFAULT: "hsl(var(--muted))",
                    foreground: "hsl(var(--muted-foreground))",
                },
                accent: {
                    DEFAULT: "hsl(var(--accent))",
                    foreground: "hsl(var(--accent-foreground))",
                },
                popover: {
                    DEFAULT: "hsl(var(--popover))",
                    foreground: "hsl(var(--popover-foreground))",
                },
                card: {
                    DEFAULT: "hsl(var(--card))",
                    foreground: "hsl(var(--card-foreground))",
                },
            },
            borderRadius: {
                lg: "var(--radius)",
                md: "calc(var(--radius) - 2px)",
                sm: "calc(var(--radius) - 4px)",
            },
            typography: {
                DEFAULT: {
                    css: {
                        maxWidth: 'none',
                        color: 'hsl(var(--foreground))',
                        a: {
                            color: 'hsl(var(--primary))',
                            '&:hover': {
                                color: 'hsl(var(--primary))',
                            },
                        },
                        code: {
                            color: 'hsl(var(--foreground))',
                            backgroundColor: 'hsl(var(--muted))',
                            padding: '0.2em 0.4em',
                            borderRadius: '0.25rem',
                            fontWeight: '400',
                        },
                        'pre code': {
                            backgroundColor: 'transparent',
                            padding: 0,
                        },
                        pre: {
                            backgroundColor: 'hsl(var(--muted))',
                            padding: '1em',
                            borderRadius: '0.5rem',
                            overflowX: 'auto',
                        },
                        blockquote: {
                            borderLeftColor: 'hsl(var(--border))',
                        },
                        h1: {
                            color: 'hsl(var(--foreground))',
                        },
                        h2: {
                            color: 'hsl(var(--foreground))',
                        },
                        h3: {
                            color: 'hsl(var(--foreground))',
                        },
                        h4: {
                            color: 'hsl(var(--foreground))',
                        },
                        hr: {
                            borderColor: 'hsl(var(--border))',
                        },
                        strong: {
                            color: 'hsl(var(--foreground))',
                        },
                        thead: {
                            color: 'hsl(var(--foreground))',
                            borderBottomColor: 'hsl(var(--border))',
                        },
                        tbody: {
                            tr: {
                                borderBottomColor: 'hsl(var(--border))',
                            },
                        },
                        table: {
                            fontSize: '0.875rem',
                        },
                        th: {
                            padding: '0.5rem',
                        },
                        td: {
                            padding: '0.5rem',
                        }
                    },
                },
            },
            animation: {
                "in": "in 0.3s ease-out",
                "out": "out 0.3s ease-in",
                "slide-in-from-right": "slide-in-from-right 0.3s ease-out",
                "slide-out-to-right": "slide-out-to-right 0.3s ease-in"
            },
            keyframes: {
                in: {
                    "0%": { opacity: 0 },
                    "100%": { opacity: 1 }
                },
                out: {
                    "0%": { opacity: 1 },
                    "100%": { opacity: 0 }
                },
                "slide-in-from-right": {
                    "0%": { transform: "translateX(100%)" },
                    "100%": { transform: "translateX(0)" }
                },
                "slide-out-to-right": {
                    "0%": { transform: "translateX(0)" },
                    "100%": { transform: "translateX(100%)" }
                }
            }
        },
    },
    plugins: [
        require('@tailwindcss/typography'),
    ],
}

