# AI-Powered Code Reviewer & PR Security Inspector

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Stack](https://img.shields.io/badge/Stack-React%20%7C%20Node.js%20%7C%20Express%20%7C%20Gemini%20AI-green)](#tech-stack)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue)](docker-compose.yml)

An AI-driven code review application that inspects code snippets and pull requests for security vulnerabilities, syntax errors, performance bottlenecks, and best practice refactoring suggestions.

Developed by **Om Giri**.

---

## 🌟 Features

- 🔍 **Automated Code Analysis**: Pastes code snippets and instantly generates deep AI code reviews powered by Google Gemini AI.
- 🎨 **Rich Syntax Highlighting**: Live code editor with real-time syntax highlighting (`prismjs` / `highlight.js`).
- ⚡ **Markdown Output Rendering**: Clean Markdown-rendered AI feedback with code diff blocks and bulleted security suggestions.
- 🐳 **Dockerized Deployment**: Includes container setups for client and API backend with environment variable isolation.
- 🚀 **Production Ready**: Configured for continuous integration via GitHub Actions and Vercel/Render deployment.

---

## 🛠️ Tech Stack

- **Frontend**: React 19, Vite, Axios, React Simple Code Editor, React Markdown, PrismJS, Rehype Highlight
- **Backend**: Node.js, Express.js, `@google/generative-ai` SDK, CORS, Dotenv
- **DevOps**: Docker, Docker Compose, GitHub Actions CI/CD

---

## 🚀 Quick Start

### 1. Clone & Set Up Environment

```bash
git clone https://github.com/omgiri01/ai-code-reviewer.git
cd ai-code-reviewer
```

### 2. Backend Configuration

```bash
cd BackEnd
npm install
# Create a .env file:
# GEMINI_KEY=your_google_gemini_api_key
npm start
```

### 3. Frontend Configuration

```bash
cd ../Frontend
npm install
npm run dev
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).  
Created with ❤️ by **Om Giri**.
