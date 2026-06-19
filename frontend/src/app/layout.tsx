import type { Metadata } from 'next';
import { Plus_Jakarta_Sans } from 'next/font/google';
import './globals.css';
import { Toaster } from 'react-hot-toast';

const sans = Plus_Jakarta_Sans({ subsets: ['latin'], variable: '--font-sans' });

export const metadata: Metadata = {
  title: 'MemoraAI — Adaptive RAG System with Deep Retrieval & Memory',
  description: 'Production-grade AI retrieval system featuring hybrid search (BM25 + Vector), Reciprocal Rank Fusion, cross-encoder reranking, layered memory, and explainable responses.',
  keywords: ['RAG', 'AI', 'hybrid retrieval', 'BM25', 'vector search', 'memory', 'reranking'],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className={`${sans.variable} font-sans antialiased`}>
        {children}
        <Toaster
          position="top-right"
          toastOptions={{
            className: 'glass-strong !rounded-xl !text-sm',
            style: {
              background: 'rgba(10, 11, 15, 0.9)',
              color: '#f8fafc',
              border: '1px solid rgba(255, 255, 255, 0.08)',
              backdropFilter: 'blur(16px)',
            },
          }}
        />
      </body>
    </html>
  );
}