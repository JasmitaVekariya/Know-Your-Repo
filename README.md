```md
# GitHub Repo Intelligence Agent  
## Hackathon Phase-Wise Implementation Plan

---

## 0. Project Goal (Lock This First)

Build an AI agent that:
1. Ingests a **public GitHub repository**
2. Explains the repo **architecture + flow step-by-step**
3. Helps users **plan new features** by generating:
   - Architecture changes
   - Files to modify
   - A strict, reusable AI prompt
4. Uses **ephemeral vector storage** (per session)
5. Tracks **token usage + pricing per user**

This is a **developer tool**, not a chatbot.

---

## 1. Tech Stack (Finalized)

### Backend
- Python
- FastAPI
- LangChain
- Google Gemini (direct SDK)
- ChromaDB (local, ephemeral)
- MongoDB (users + usage)

### Frontend
- React
- Tailwind CSS
- Mermaid (diagram code only)

---

## 2. High-Level Architecture

Frontend (React)
→ FastAPI API Gateway
→ Repo Ingestion Pipeline
→ Repo Manifest Generator
→ ChromaDB (session-scoped)
→ LangChain + Gemini
→ Response Formatter (explanation / feature plan)

---

## 3. Phase 1 — Project Skeleton (DO THIS FIRST)

### Backend structure
```

backend/
├── app/
│   ├── main.py
│   ├── api/
│   │   ├── ingest.py
│   │   ├── chat.py
│   │   └── user.py
│   ├── core/
│   │   ├── config.py
│   │   ├── session.py
│   │   └── cleanup.py
│   ├── ingestion/
│   │   ├── github_loader.py
│   │   ├── filters.py
│   │   ├── chunker.py
│   │   └── manifest.py
│   ├── llm/
│   │   ├── gemini.py
│   │   └── prompts.py
│   ├── vector/
│   │   └── chroma.py
│   ├── db/
│   │   ├── mongo.py
│   │   └── models.py
│   └── utils/
│       └── token_counter.py

```

### Frontend structure
```

frontend/
├── src/
│   ├── pages/
│   ├── components/
│   ├── api/
│   └── utils/

```

---

## 4. Phase 2 — GitHub Repo Ingestion Pipeline (CRITICAL)

### 4.1 Repo Fetching
**AI CAN DO**
- Clone public repo using `gitpython`
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