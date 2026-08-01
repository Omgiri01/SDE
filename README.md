# Software Development Engineering (SDE) & Full-Stack MERN Portfolio

[![Author](https://img.shields.io/badge/Author-Om%20Giri-blue.svg)](#author)
[![Stack](https://img.shields.io/badge/Stack-MERN%20%7C%20Docker%20%7C%20AI%20%7C%20DevOps-green)](#projects)

Welcome to my Software Development Engineering (SDE) repository. This portfolio features production-grade full-stack web applications, AI integrations, containerized microservices, and CI/CD deployment setups built with the **MERN Stack** (MongoDB, Express.js, React.js, Node.js).

---

## 🛠️ Featured Projects

### 1. 🏢 Enterprise MERN ERP & CRM Platform
*📁 Location: [`./enterprise-erp-crm`](./enterprise-erp-crm)*

A production-ready multi-tenant Enterprise Resource Planning (ERP) and Customer Relationship Management (CRM) platform.
- **Key Features**: Automated invoice & quote management, customer CRM pipeline, payment tracking, PDF generation, role-based access control (RBAC).
- **Tech Stack**: React 18, Ant Design (AntD), Redux Toolkit, Node.js v20, Express.js, MongoDB Atlas, Docker, Nginx.

---

### 2. 🤖 AI-Powered Code Reviewer & PR Security Inspector
*📁 Location: [`./ai-code-reviewer`](./ai-code-reviewer)*

An AI-driven developer tool that analyzes code snippets and pull requests for security vulnerabilities, memory leaks, performance bottlenecks, and best-practice refactoring suggestions.
- **Key Features**: Live code editor, Google Gemini AI integration, real-time Markdown output, code diff highlights, containerized microservices.
- **Tech Stack**: React 19, Vite, PrismJS, Node.js, Express.js, `@google/generative-ai` SDK, Docker.

---

## 🐳 Running Projects with Docker

Each project contains a dedicated `docker-compose.yml` configuration:

```bash
# To run Enterprise ERP & CRM:
cd enterprise-erp-crm
docker-compose up --build -d

# To run AI Code Reviewer:
cd ../ai-code-reviewer
docker-compose up --build -d
```

---

## 👤 Author

**Om Giri**  
*Full-Stack Software Development Engineer*  
GitHub: [@Omgiri01](https://github.com/Omgiri01)
