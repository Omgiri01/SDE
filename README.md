# Software Development Engineering (SDE) & Full-Stack AI Portfolio

[![Author](https://img.shields.io/badge/Author-Om%20Giri-blue.svg)](#author)
[![Stack](https://img.shields.io/badge/Stack-MERN%20%7C%20PyTorch%20%7C%20PINNs%20%7C%20Docker-green)](#featured-projects)

Welcome to my Software Development Engineering (SDE) repository. This portfolio features production-grade full-stack web applications, Physics-Informed AI integrations, multi-tenant SaaS systems, and containerized microservices built with modern web and machine learning stacks.

Created and maintained by **Om Giri**.

---

## 🛠️ Featured Projects

### 1. 🔬 PINN-FEA-DigitalTwin: Physics-Informed Neural Network for FEA & Stress Analysis
*📁 Location: [`./pinn-fea-digital-twin`](./pinn-fea-digital-twin)*

A multi-physics digital twin platform that predicts structural stress field distributions ($\sigma_{xx}, \sigma_{yy}, \tau_{xy}$) and Von Mises yield invariants ($\sigma_{vm}$) on finite element meshes using PyTorch PINNs.
- **Key Features**: Physics-Informed momentum equilibrium loss functions ($\nabla \cdot \boldsymbol{\sigma} + \mathbf{b} = 0$), VTK/Abaqus mesh processing, real-time 3D WebGL stress heatmap shaders, async WebSockets streaming.
- **Tech Stack**: Python, PyTorch (PINNs), PyVista, FastAPI, React 18, Three.js (`@react-three/fiber`), WebGL, Docker.

---

### 2. 🏢 Enterprise MERN ERP & CRM Platform
*📁 Location: [`./enterprise-erp-crm`](./enterprise-erp-crm)*

A production-ready multi-tenant Enterprise Resource Planning (ERP) and Customer Relationship Management (CRM) platform.
- **Key Features**: Automated invoice & quote management, customer CRM pipeline, payment tracking, PDF generation, role-based access control (RBAC).
- **Tech Stack**: React 18, Ant Design (AntD), Redux Toolkit, Node.js v20, Express.js, MongoDB Atlas, Docker, Nginx.

---

### 3. 🤖 AI-Powered Code Reviewer & PR Security Inspector
*📁 Location: [`./ai-code-reviewer`](./ai-code-reviewer)*

An AI-driven developer tool that analyzes code snippets and pull requests for security vulnerabilities, memory leaks, performance bottlenecks, and best-practice refactoring suggestions.
- **Key Features**: Live code editor, Google Gemini AI integration, real-time Markdown output, code diff highlights, containerized microservices.
- **Tech Stack**: React 19, Vite, PrismJS, Node.js, Express.js, `@google/generative-ai` SDK, Docker.

---

## 🐳 Running Projects with Docker

Each project contains a dedicated `docker-compose.yml` configuration:

```bash
# To run PINN FEA Digital Twin:
cd pinn-fea-digital-twin
docker-compose up --build -d

# To run Enterprise ERP & CRM:
cd ../enterprise-erp-crm
docker-compose up --build -d

# To run AI Code Reviewer:
cd ../ai-code-reviewer
docker-compose up --build -d
```

---

## 👤 Author

**Om Giri**  
*Full-Stack Software Development Engineer & Physics-ML Specialist*  
GitHub: [@Omgiri01](https://github.com/Omgiri01)
