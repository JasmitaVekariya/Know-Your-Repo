# GitHub Repo Intelligence Agent - Frontend

This is the React-based frontend for the GitHub Repo Intelligence Agent, an AI-powered developer tool that analyzes GitHub repositories and helps plan new features.

## Tech Stack

- **React 19** - UI library
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Utility-first styling
- **React Router** - Client-side routing
- **Axios** - HTTP client for API communication
- **React Markdown** - Rendering markdown content
- **Mermaid** - Diagram rendering via markdown
- **Lucide React** - Icon library

## Setup

1. Install dependencies:
   ```bash
   npm install
   ```

2. Start development server:
   ```bash
   npm run dev
   ```

3. The application will be available at `http://localhost:5173`

## Available Scripts

- `npm run dev` - Start development server with hot reload
- `npm run build` - Build for production
- `npm run preview` - Preview production build locally
- `npm run lint` - Run ESLint for code quality checks

## Features

- User authentication (login/register) with guest mode
- Repository URL input and validation
- Mode selection (Explain Repository / Plan Feature)
- Real-time chat interface with AI agent
- Markdown rendering with code syntax highlighting
- Mermaid diagram support for architecture visualization
- Token usage tracking dashboard
- Responsive design with Tailwind CSS

## Project Structure

```
src/
├── pages/          # Main application pages
├── components/     # Reusable UI components
├── layouts/        # Layout components
├── context/        # React context providers
├── api/            # API integration layer
└── assets/         # Static assets
```

## Backend Integration

The frontend connects to the FastAPI backend at `http://localhost:8000`. Ensure the backend server is running before using the application.
