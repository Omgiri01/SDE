# Software Development Engineering (SDE) & Multi-Disciplinary Portfolio

[![Author](https://img.shields.io/badge/Author-Om%20Giri-blue.svg)](#author)
[![Stack](https://img.shields.io/badge/Stack-Physics--ML%20%7C%20MERN%20%7C%20Docker%20%7C%20AI-green)](#featured-projects)

Welcome to my Software Development Engineering (SDE) repository. This portfolio features production-grade full-stack web applications, Physics-Informed AI digital twins, containerized microservices, and modern web software applications built by **Om Giri**.

---

## 🛠️ Featured Projects

### 1. ⚙️ PhysiTwin: Multi-Physics PINN Digital Twin for Material Fracture & FEA Stress
*📁 Location: [`./PhysiTwin`](./PhysiTwin)*

An advanced engineering software platform combining solid mechanics (LEFM, EPFM, XFEM, Peridynamics), PyTorch Physics-Informed Neural Networks (PINNs), FastAPI microservices, and an interactive React/Three.js 3D stress visualization interface.
- **Key Features**: Navier-Cauchy momentum PDE loss functions, 100x accelerated stress field inference, Abaqus/CalculiX `.vtk` mesh parsing, live 3D stress contour shaders.
- **Tech Stack**: Python 3.10+, PyTorch, FastAPI, PyVista, React 18, Three.js, WebGL, Docker.

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

## 🐳 Docker Setup

Each project contains dedicated Docker configurations:

```bash
# To run PhysiTwin:
cd PhysiTwin
docker-compose up --build -d

# To run Enterprise ERP & CRM:
cd enterprise-erp-crm
docker-compose up --build -d

# To run AI Code Reviewer:
cd ai-code-reviewer
docker-compose up --build -d
```

---

## 👤 Author

**Om Giri**  
*Software Development Engineer | Multiscale Mechanics & AI Specialist*  
GitHub: [@Omgiri01](https://github.com/Omgiri01)
