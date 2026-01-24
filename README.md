# GitHub Repo Intelligence Agent

An AI-powered developer tool that ingests public GitHub repositories, analyzes their architecture, and helps plan new features with detailed implementation guidance.

## 🚀 Features

- **Repository Analysis**: Ingest and analyze public GitHub repositories
- **Architecture Explanation**: Step-by-step breakdown of repo structure and flow
- **Feature Planning**: Generate detailed plans for new features including:
  - Architecture changes
  - Files to modify
  - Implementation steps
  - Mermaid diagrams
- **Ephemeral Storage**: Session-based vector storage for security
- **Token Usage Tracking**: Monitor API costs per user
- **Clean UI**: React-based interface with Mermaid diagram support

## 🛠 Tech Stack

### Backend
- **Python** - Core language
- **FastAPI** - API framework
- **LangChain** - LLM orchestration
- **Google Gemini** - AI model
- **ChromaDB** - Vector storage
- **MongoDB** - User data and usage tracking

### Frontend
- **React** - UI framework
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **Mermaid** - Diagram generation

## 📋 Prerequisites

- Python 3.9+ (3.11 recommended)
- Node.js 16+
- Git
- Google Cloud account (for Gemini API)
- MongoDB instance

## 🚀 Installation

### Backend Setup

1. Navigate to backend directory:
   ```bash
   cd backend
   ```

2. Create virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create `.env` file:
   ```bash
   GEMINI_API_KEY=your_gemini_api_key
   MONGO_URI=your_mongodb_connection_string
   ```

5. Run the server:
   ```bash
   uvicorn app.main:app --reload
   ```

### Frontend Setup

1. Navigate to frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start development server:
   ```bash
   npm run dev
   ```

## 📖 Usage

1. **Access the application** at `http://localhost:5173` (frontend) and `http://localhost:8000` (backend API)

2. **Login or continue as guest**

3. **Enter a GitHub repository URL** (must be public)

4. **Choose mode**:
   - **Explain Repository**: Get architecture breakdown and flow explanation
   - **Plan Feature**: Describe a new feature and get implementation guidance

5. **View results** including Mermaid diagrams and detailed plans

## 🔧 API Endpoints

- `GET /health` - Health check
- `POST /api/ingest` - Ingest repository
- `POST /api/chat` - Chat with AI agent
- `GET /api/user/usage` - Get token usage

## 🏗 Project Structure

```
KYR/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   ├── core/
│   │   ├── ingestion/
│   │   ├── llm/
│   │   ├── vector/
│   │   ├── db/
│   │   └── utils/
│   ├── requirements.txt
│   └── SETUP.md
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   ├── components/
│   │   ├── api/
│   │   └── assets/
│   ├── package.json
│   └── vite.config.js
└── README.md
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🎯 Hackathon Implementation Plan

*Detailed phase-by-phase development plan for the hackathon*

### Phase 1 — Project Skeleton
- Set up backend and frontend project structures
- Initialize FastAPI and React applications

### Phase 2 — GitHub Repo Ingestion Pipeline
- Implement repository cloning with size limits
- Add file filtering and chunking strategies
- Create manifest generation

### Phase 3 — Vector Storage & LLM Integration
- Set up ChromaDB with session management
- Integrate Google Gemini API
- Implement cleanup tasks

### Phase 4 — Core Agent Capabilities
- Repository explanation mode
- Feature planning mode with structured outputs

### Phase 5 — Frontend & Demo
- Build minimal UI
- Add Mermaid diagram support
- Prepare demo scenarios

### Key Technical Decisions
- **Max repo size**: 500 files, 200KB per file
- **Session TTL**: 30 minutes
- **Chunk size**: 400-600 tokens
- **Models**: Google Gemini Pro

### Demo Readiness Checklist
- [ ] Small repo analysis (<100 files)
- [ ] Medium repo analysis (300-500 files)
- [ ] Feature planning demonstration
- [ ] Mermaid diagram generation
- [ ] Token usage tracking
- [ ] Error handling and recovery

---

*Built for hackathons with deterministic engineering first, AI second.*
- Handle branch = `main` fallback to `master`

**YOU MUST**
- Enforce timeout
- Enforce max repo size (hard stop)

---

### 4.2 Repo Filtering (NON-NEGOTIABLE)

Ignore directories:
```

node_modules, .git, dist, build, out, target,
venv, **pycache**, coverage, .next, .cache

```

Ignore file extensions:
```

.png .jpg .jpeg .svg .gif
.mp4 .mp3
.zip .tar .gz
.lock
.min.js .map

```

Hard limits:
- Max file size: 200 KB
- Max lines: 800

Files exceeding limits → summarize, do NOT embed raw.

---

### 4.3 Chunking Strategy

**Rule**
- Chunk per file
- Split by logical blocks (functions/classes)
- 400–600 tokens per chunk

Metadata to attach:
```

file_path
language
module_type (core / config / test / doc)
is_entry_candidate (true/false)

````

---

## 5. Phase 3 — Repo Manifest Generator (MANDATORY)

### Manifest JSON (example)
```json
{
  "repo_name": "",
  "tech_stack": [],
  "entry_points": [],
  "core_modules": [],
  "config_files": [],
  "test_presence": true,
  "architecture_summary": ""
}
````

**AI CAN DO**

* Infer tech stack
* Detect entry points using heuristics
* Summarize architecture

**YOU MUST**

* Define entry-point heuristics explicitly
* Ensure manifest is generated BEFORE embeddings

---

## 6. Phase 4 — ChromaDB (Ephemeral Storage)

### Strategy

* One `session_id` per user connection
* All embeddings tagged with:

```
session_id
repo_url
timestamp
```

### Cleanup

* TTL = 30 minutes
* Background cleanup task every 10 minutes

**Do NOT rely on “disconnect events”**

---

## 7. Phase 5 — LLM Integration (Gemini)

### What YOU must do

* Create Google Cloud project
* Enable Gemini API
* Generate API key
* Store in `.env`

```
GEMINI_API_KEY=xxxx
```

### What AI can do

* Wrap Gemini with LangChain
* Build prompt templates
* Handle retries + context limits

---

## 8. Phase 6 — Core Agent Capabilities

### 8.1 Repo Explanation Mode

Input:

```
"Explain this repository"
```

Flow:

1. Load manifest
2. Identify entry point(s)
3. Explain:

   * Purpose
   * High-level flow
   * Key modules
4. Generate Mermaid diagram code (if asked)

Output structure:

* Overview
* Architecture
* Flow
* Code quality observations (no fake scores)

---

### 8.2 Feature Planning Mode (MOST IMPORTANT)

Input:

```
"I want to add X feature"
```

Output MUST be structured:

```
## Feature Objective
## Architectural Impact
## Files to Modify
## Step-by-Step Changes
## Mermaid Diagram (if applicable)
## Copy-Paste Prompt for AI Tools
## Validation Checklist
```

**Prompt must be deterministic and boring.**
No hallucinated files. No assumptions.

---

## 9. Phase 7 — Token Usage + Pricing

### MongoDB Models

**User**

```
user_id
email
created_at
```

**Usage**

```
user_id
session_id
prompt_tokens
completion_tokens
model
price_snapshot
timestamp
```

**Rules**

* Store price at request time
* Do not recalculate later

---

## 10. Phase 8 — Frontend (Minimal but Clean)

Pages:

* Login / Guest
* Repo URL input
* Chat interface
* Token usage indicator
* Mermaid diagram viewer

**AI can scaffold UI**
**YOU must**
Final polish, UX decisions, demo flow

---

## 11. Phase 9 — Demo Readiness Checklist

* Small repo demo (<100 files)
* Medium repo demo (300–500 files)
* Feature planning demo
* Mermaid diagram demo
* Token usage visible
* No crashes on refresh

---

## 12. What YOU Must Do (Cannot Delegate)

* Create Gemini API key
* Decide repo size limits
* Handle secrets securely
* Decide demo narrative
* Control scope (do NOT overbuild)

---

## 13. Hackathon Pitch Line

> “This is an AI software architect that reverse-engineers real GitHub repositories and safely guides feature development.”

---

## 14. Final Warning

If preprocessing and manifest are weak,
**the LLM will hallucinate** and your project will fail.

Deterministic engineering first.
LLM second.

```

---

If you want next:
- I can convert this into **Cursor task prompts**
- Or design the **exact FastAPI endpoint contracts**
- Or write the **Gemini prompt templates** directly
```