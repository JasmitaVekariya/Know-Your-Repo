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