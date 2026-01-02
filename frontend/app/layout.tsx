import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'AI Platform',
  description: 'MCP 기반 기업용 AI 플랫폼',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko" className="dark">
      <body className="min-h-screen bg-dark-900 text-dark-100 antialiased">
        {children}
      </body>
    </html>
  );
}
