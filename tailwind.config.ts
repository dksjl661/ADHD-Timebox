import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['var(--font-inter)', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'sans-serif'],
      },
      colors: {
        // Soft UI Evolution - 改进的对比度，更好的可访问性
        calm: {
          50: '#F0F9FF',   // Softer background
          100: '#E0F2FE',
          200: '#BAE6FD',
          300: '#7DD3FC',
          400: '#38BDF8',  // Secondary
          500: '#0EA5E9',  // Primary (softer blue)
          600: '#0284C7',
          700: '#0369A1',
          800: '#075985',  // Text
          900: '#0C4A6E',
        },
        health: {
          50: '#F0FDF4',
          100: '#DCFCE7',
          200: '#BBF7D0',
          300: '#86EFAC',
          400: '#4ADE80',
          500: '#22C55E',  // Softer CTA Green
          600: '#16A34A',
          700: '#15803D',
          800: '#166534',
          900: '#14532D',
        },
        // Soft UI shadows and surfaces
        surface: {
          light: '#FFFFFF',
          soft: '#F8FAFC',
          elevated: '#FFFFFF',
        },
      },
      spacing: {
        // 改进的间距系统 - 基于 8px 网格
        '18': '4.5rem',   // 72px
        '22': '5.5rem',   // 88px
        '26': '6.5rem',   // 104px
        '30': '7.5rem',   // 120px
      },
      fontSize: {
        // 模块化字体大小比例 (12 14 16 18 24 32)
        '2xs': ['0.75rem', { lineHeight: '1.25rem' }],    // 12px
        'xs': ['0.875rem', { lineHeight: '1.5rem' }],      // 14px
        'sm': ['0.9375rem', { lineHeight: '1.625rem' }],   // 15px
        'base': ['1rem', { lineHeight: '1.75rem' }],       // 16px
        'lg': ['1.125rem', { lineHeight: '1.875rem' }],    // 18px
        'xl': ['1.5rem', { lineHeight: '2.25rem' }],       // 24px
        '2xl': ['2rem', { lineHeight: '2.5rem' }],         // 32px
        '3xl': ['2.5rem', { lineHeight: '3rem' }],         // 40px
        '4xl': ['3rem', { lineHeight: '3.5rem' }],         // 48px
      },
      boxShadow: {
        // Soft UI Evolution - 改进的阴影系统
        'soft': '0 2px 8px rgba(0, 0, 0, 0.04), 0 1px 2px rgba(0, 0, 0, 0.06)',
        'soft-md': '0 4px 12px rgba(0, 0, 0, 0.05), 0 2px 4px rgba(0, 0, 0, 0.06)',
        'soft-lg': '0 8px 24px rgba(0, 0, 0, 0.06), 0 4px 8px rgba(0, 0, 0, 0.08)',
        'soft-xl': '0 12px 32px rgba(0, 0, 0, 0.08), 0 6px 12px rgba(0, 0, 0, 0.1)',
        // 内阴影用于 Soft UI
        'inner-soft': 'inset 0 2px 4px rgba(0, 0, 0, 0.06)',
      },
      borderRadius: {
        'xl': '1rem',      // 16px
        '2xl': '1.25rem',  // 20px
        '3xl': '1.5rem',   // 24px
      },
      transitionDuration: {
        '150': '150ms',
        '200': '200ms',
        '300': '300ms',
      },
      transitionTimingFunction: {
        'ease-out': 'cubic-bezier(0, 0, 0.2, 1)',
        'ease-in-out': 'cubic-bezier(0.4, 0, 0.2, 1)',
      },
    },
  },
  plugins: [],
};
export default config;
