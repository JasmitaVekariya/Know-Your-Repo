# GitHub Repo Intelligence Agent

> An AI-powered developer tool that helps you understand and plan features for any public GitHub repository

## 📖 About

**Know Your Repo** is an intelligent repository analysis tool that leverages AI to help developers quickly understand codebases and plan new features. By ingesting and analyzing GitHub repositories, it provides:

- **Deep Code Understanding**: Automatically analyzes repository structure, architecture, and code flow
- **Interactive Q&A**: Chat with an AI agent that understands your repository's context
- **Feature Planning**: Get detailed implementation plans including architecture changes, files to modify, and step-by-step guidance
- **Visual Documentation**: Auto-generated Mermaid diagrams for architecture visualization

Perfect for developers who need to quickly onboard to new projects, plan features, or understand complex codebases.

## 🎯 Use Cases

- **Rapid Onboarding**: Quickly understand new codebases without spending hours reading documentation
- **Feature Development**: Get AI-powered suggestions on how to implement new features
- **Code Review**: Understand the architecture before reviewing pull requests
- **Documentation**: Generate architecture diagrams and explanations
- **Learning**: Study open-source projects more efficiently

## 🔍 How It Works

1. **Repository Ingestion**: Provide any public GitHub repository URL
2. **Intelligent Analysis**: The system clones, parses, and chunks the repository into meaningful segments
3. **Vector Storage**: Code is embedded and stored in ChromaDB for semantic search
4. **AI Processing**: Google Gemini analyzes the repository structure and content
5. **Interactive Chat**: Ask questions or request feature plans through a conversational interface
6. **Visual Output**: Get detailed explanations, implementation plans, and Mermaid diagrams

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

## 👨‍💻 Author

**Jasmita Vekariya**
- GitHub: [@JasmitaVekariya](https://github.com/JasmitaVekariya)

## 🌟 Repository Description

**AI-powered GitHub repository analyzer that helps developers understand codebases and plan features with intelligent insights and visualizations**

*This description can be used for the GitHub repository settings to help others discover and understand this project.*

---