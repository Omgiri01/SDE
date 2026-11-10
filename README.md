# Software Development Engineering (SDE) & Multi-Disciplinary Portfolio

[![Author](https://img.shields.io/badge/Author-Om%20Giri-blue.svg)](https://github.com/Omgiri01)
[![GitHub](https://img.shields.io/badge/GitHub-Profile-black?logo=github)](https://github.com/Omgiri01)
[![Stack](https://img.shields.io/badge/Focus-Distributed%20Systems%20%7C%20Physics--AI%20%7C%20Full--Stack%20%7C%20Robotics-brightgreen)](#core-competencies)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Welcome to the Software Development Engineering (SDE) portfolio repository of **Om Giri**. This repository showcases production-grade full-stack architectures, distributed microservices, quantitative risk engines, physics-informed neural digital twins, and advanced robotics/computer vision applications.

---

## 🛠️ Flagship Projects

### 1. 📈 [QuantRiskPro](./QuantRiskPro) — Distributed Real-Time Quantitative Risk Engine
*📁 Location: [`./QuantRiskPro`](./QuantRiskPro)*

A distributed, institutional-grade quantitative risk analytics and portfolio intelligence platform engineered for real-time risk assessment, financial mathematics, and live market streaming.

- **Domain:** Distributed Systems, Quantitative Finance, Real-Time Streaming, Financial Engineering.
- **Architectural Highlights:**
  - **Microservices Pipeline:** Containerized architecture separating market ingestion, risk computation, event-driven consumption, and REST/WebSocket API delivery.
  - **Risk Analytics:** Closed-form and Monte Carlo Value-at-Risk (Parametric & Historical VaR, CVaR/Expected Shortfall), Black-Scholes European option pricing, and full analytical Greeks ($\Delta, \Gamma, \Theta, \mathcal{V}, \rho$).
  - **Reactive Dashboard:** Live tick-by-tick real-time portfolio updates without page reload via persistent WebSocket channels.
- **Tech Stack:** Python 3.11, FastAPI, Redis, TimescaleDB / PostgreSQL, React, TypeScript, TailwindCSS, Docker Compose.

---

### 2. ⚙️ [PhysiTwin](./PhysiTwin) — Multi-Physics PINN Digital Twin for Structural Fracture & FEA
*📁 Location: [`./PhysiTwin`](./PhysiTwin)*

A Physics-Informed Neural Network (PINN) digital twin platform that solves Navier-Cauchy structural PDEs and predicts multi-physics fracture fields (LEFM, EPFM, XFEM) in real-time.

- **Domain:** Computational Mechanics, Physics-Informed Machine Learning (SciML), WebGL 3D Scientific Visualization.
- **Architectural Highlights:**
  - **PINN PDE Loss Formulations:** Embedded partial differential equation losses for equilibrium, strain-displacement, and boundary conditions yielding $100\times$ faster stress inference than traditional iterative solvers.
  - **FEA Mesh Ingestion:** Native Abaqus and CalculiX `.vtk` / `.inp` mesh parsing with sub-millimeter displacement resolution.
  - **Interactive 3D WebGL Interface:** Custom Three.js viewport allowing real-time rotating, slicing, and stress field contour mapping.
- **Tech Stack:** PyTorch, FastAPI, PyVista, React 18, Three.js, WebGL, Docker.

---

### 3. 🏢 [Enterprise MERN ERP & CRM Platform](./enterprise-erp-crm)
*📁 Location: [`./enterprise-erp-crm`](./enterprise-erp-crm)*

A full-stack, enterprise-grade cloud ERP and CRM platform built to streamline corporate procurement, lead pipelines, quote generation, and accounting.

- **Domain:** Enterprise SaaS, Scalable Full-Stack Architecture, Role-Based Access Control (RBAC).
- **Architectural Highlights:**
  - **Transaction Management:** Multi-currency invoice calculation, quote-to-invoice automation, and payment reconciliation.
  - **Document Generation Engine:** Server-side PDF generation pipeline rendering vector invoice templates on the fly.
  - **Security & Authorization:** JWT authentication, granular permission matrices, and protected RESTful endpoints.
- **Tech Stack:** React 18, Ant Design (AntD), Redux Toolkit, Node.js, Express.js, MongoDB Atlas, Docker, Nginx.

---

### 4. 🤖 [AI-Powered Code Reviewer & PR Security Inspector](./ai-code-reviewer)
*📁 Location: [`./ai-code-reviewer`](./ai-code-reviewer)*

An automated developer productivity platform providing deep static code analysis, vulnerability scanning, and refactoring recommendations powered by the Google Gemini API.

- **Domain:** Developer Tooling, Large Language Models (LLM), Code Quality & Security.
- **Architectural Highlights:**
  - **Live Code Analysis:** Multi-language syntax parsing with contextual feedback on security vulnerabilities (OWASP Top 10), performance bottlenecks, and architectural anti-patterns.
  - **Interactive UI:** Split-pane real-time code editor with syntax highlighting and instant Markdown review rendering.
- **Tech Stack:** React 19, Vite, PrismJS, Node.js, Express.js, `@google/generative-ai` SDK, Docker.

---

## 🔬 Specialized AI, Robotics & Computer Vision Suites

Beyond the core full-stack platforms in this repository, here are companion specialized open-source engineering systems developed by Om Giri:

| System | Domain | Tech Stack | Link |
|---|---|---|---|
| **Robotics Manipulator Kinematics** | 2-DOF Planar Trajectory Planning & 6-DOF Industrial Forward Kinematics Dashboard | Python, NumPy, Matplotlib, Tkinter | [View Repo ↗](https://github.com/Omgiri01/robotics-manipulator-kinematics) |
| **Spherical Robot Workspace** | 3-DOF Spherical Manipulator (R-R-P) Denavit–Hartenberg Kinematics & 3D Volumetric Modeler | Python, NumPy, Matplotlib, JSON Datasets | [View Repo ↗](https://github.com/Omgiri01/spherical-robot-workspace) |
| **Spherical Robot Unity Simulator** | Real-Time 3D Kinematics Simulation, Virtual Touch Joysticks & Trajectory Tracing (Windows & Android) | Unity 2022.3 LTS, C#, URP, Input System | [View Repo ↗](https://github.com/Omgiri01/spherical-robot-unity) |
| **Industrial Defect Detection** | Mechanical Transmission (Gear & Bearing) & Surface Quality Fault Detection | PyTorch, ResNet-50, STFT Spectrograms, Scikit-Learn | [View Repo ↗](https://github.com/Omgiri01/industrial-defect-detection-computer-vision) |
| **Biometric Attendance System** | Real-Time Face Detection, Anti-Spoofing Liveness Verification & Database Logging | OpenCV, DeepFace, SQLite, pyttsx3 | [View Repo ↗](https://github.com/Omgiri01/face-detection-attendance-system) |

---

## 💻 Core Technical Competencies

- **Languages:** Python, JavaScript (ES6+), TypeScript, C#, C++, SQL, HTML5/CSS3
- **Backend & Distributed Systems:** FastAPI, Node.js, Express.js, Microservices, Redis, WebSocket, REST APIs
- **Frontend & Visualization:** React 18/19, Three.js, WebGL, Redux Toolkit, Vite, TailwindCSS, Ant Design
- **AI / Deep Learning / Scientific Computing:** PyTorch, TensorFlow, SciPy, NumPy, Scikit-Learn, OpenCV, DeepFace, PINNs (Physics-Informed Neural Networks)
- **Database & Storage:** PostgreSQL, TimescaleDB, MongoDB, SQLite, Redis
- **DevOps & Cloud:** Docker, Docker Compose, Git / GitHub Actions, Linux, Nginx, Vercel

---

## 👤 Author & Contact

**Om Giri**  
*Software Development Engineer | Multiscale Mechanics & AI Specialist*  
- **GitHub:** [@Omgiri01](https://github.com/Omgiri01)
- **Profile:** [https://github.com/Omgiri01](https://github.com/Omgiri01)

---

## 📄 License

This repository is distributed under the MIT License — see [LICENSE](LICENSE) for details.
