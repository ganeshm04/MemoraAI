# MemoraAI Frontend

Production-grade Next.js frontend for MemoraAI.

## Features

- **Modern UI**: Next.js 15 with Tailwind CSS
- **shadcn/ui**: Beautiful, accessible components
- **Framer Motion**: Smooth animations
- **Zustand**: State management
- **TypeScript**: Full type safety
- **Responsive**: Mobile-first design

## Quick Start

### Local Development

```bash
# Install dependencies
npm install

# Set environment variables
cp .env.example .env

# Run development server
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

### Docker

```bash
# Build and run
docker-compose up --build

# Run in background
docker-compose up -d
```

## Project Structure

```
frontend/
├── src/
│   ├── app/                    # Next.js app directory
│   │   ├── layout.tsx          # Root layout
│   │   ├── page.tsx            # Home page
│   │   └── globals.css         # Global styles
│   ├── components/
│   │   ├── ui/                 # shadcn/ui components
│   │   ├── chat/               # Chat interface
│   │   ├── retrieval/          # Retrieval panel
│   │   ├── memory/             # Memory display
│   │   └── sources/            # Source attribution
│   ├── hooks/                  # Custom hooks
│   ├── lib/                    # Utilities
│   └── types/                  # TypeScript types
├── public/
├── Dockerfile
├── package.json
├── tailwind.config.ts
└── README.md
```

## Components

### Chat Components
- `ChatPanel` - Main chat interface
- `MessageBubble` - Individual message display
- `ChatInput` - Message input field

### Retrieval Components
- `RetrievalPanel` - Retrieved chunks display
- `ChunkCard` - Individual chunk with scores

### Memory Components
- `MemoryPanel` - Memory management interface

### Source Components
- `SourceAttribution` - Source citation display

## Deployment

See deployment guides in the main README.