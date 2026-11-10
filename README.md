<div align="center">

# Software Development Engineering (SDE) Portfolio
### High-Performance Distributed Systems • Physics-Informed AI • Full-Stack SaaS • Robotics & Machine Learning

[![Author](https://img.shields.io/badge/Author-Om%20Giri-0A66C2?style=for-the-badge&logo=github&logoColor=white)](https://github.com/Omgiri01)
[![GitHub](https://img.shields.io/badge/GitHub-Omgiri01-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/Omgiri01)
[![License: MIT](https://img.shields.io/badge/License-MIT-F5A623?style=for-the-badge)](LICENSE)

<br/>

<p align="center">
  <b>A comprehensive showcase of production-grade engineering software, distributed real-time platforms, scientific digital twins, and enterprise full-stack applications built by Om Giri.</b>
</p>

---

</div>

## 📑 Table of Contents

- [Overview & Engineering Philosophy](#-overview--engineering-philosophy)
- [Flagship Repository Systems](#-flagship-repository-systems)
  - [1. QuantRiskPro — Distributed Real-Time Quantitative Risk Platform](#1--quantriskpro--distributed-real-time-quantitative-risk-platform)
  - [2. PhysiTwin — Multi-Physics PINN Digital Twin for Structural Fracture & FEA](#2--physitwin--multi-physics-pinn-digital-twin-for-structural-fracture--fea)
  - [3. Enterprise MERN ERP & CRM Platform](#3--enterprise-mern-erp--crm-platform)
  - [4. AI-Powered Code Reviewer & PR Security Inspector](#4--ai-powered-code-reviewer--pr-security-inspector)
- [Specialized Robotics & Computer Vision Ecosystems](#-specialized-robotics--computer-vision-ecosystems)
- [Technical Skills Matrix](#-technical-skills-matrix)
- [Repository Structure & Quickstart](#-repository-structure--quickstart)
- [Author & Contact](#-author--contact)

---

## 💡 Overview & Engineering Philosophy

This repository is curated to demonstrate end-to-end software development engineering excellence across diverse and demanding problem domains:

- **Distributed Systems & Low-Latency Backends:** Asynchronous event-driven microservices, real-time WebSocket tick ingestion, in-memory caching with Redis, and containerized deployments.
- **Scientific Computing & Physics-Informed AI (SciML):** Incorporating fundamental differential equations (Navier-Cauchy continuum mechanics) into neural loss functions for real-time digital twins.
- **Enterprise SaaS Architecture:** Robust multi-tenant full-stack platforms with strict Role-Based Access Control (RBAC), database normalization, automated document pipelines, and scalable UI component libraries.
- **Robotics Kinematics & Applied Computer Vision:** Closed-form analytical kinematics, Denavit–Hartenberg transformation pipelines, real-time 3D simulation engines, and industrial predictive maintenance classifiers.

---

## 🚀 Flagship Repository Systems

### 1. 📈 [QuantRiskPro](./QuantRiskPro) — Distributed Real-Time Quantitative Risk Platform
> *Institutional-grade portfolio risk engine mirroring high-frequency trading and quantitative hedge fund architecture.*

```
[Market Feeds: Polygon / Binance] ──> [Kafka Ingestion Microservice] ──> [TimescaleDB / Redis]
                                                                                │
                                                                                ▼
[React 18 / Tailwind Dashboard] <─── [WebSocket Gateway] <─── [FastAPI Risk Calculation Engine]
                                                              (Monte Carlo, VaR, Greeks, Markowitz)
```

- **Domain:** Distributed Systems, Quantitative Finance, Event-Driven Architecture, High-Throughput Streaming.
- **Core Engineering Capabilities:**
  - **Risk Measurement Engine:** Computes closed-form Parametric Value-at-Risk (VaR), Historical Simulation VaR, and 100,000-path Monte Carlo Conditional VaR (CVaR / Expected Shortfall).
  - **Derivatives & Sensitivity Analytics:** Black-Scholes analytical option pricing with continuous first- and second-order Greeks calculation ($\Delta, \Gamma, \Theta, \mathcal{V}, \rho$).
  - **Portfolio Optimization:** Markowitz Efficient Frontier optimization maximizing the Sharpe ratio under customizable asset constraints.
  - **Reactive Real-Time UI:** Live tick-by-tick streaming dashboard built with React 18 and WebSockets, rendering responsive price charts and risk gauges without page reloads.
- **Tech Stack:** `Python 3.11`, `FastAPI`, `Apache Kafka`, `Redis`, `PostgreSQL / TimescaleDB`, `React 18`, `TypeScript`, `TailwindCSS`, `Docker Compose`.
- **Directory:** [`./QuantRiskPro`](./QuantRiskPro)

---

### 2. ⚙️ [PhysiTwin](./PhysiTwin) — Multi-Physics PINN Digital Twin for Structural Fracture & FEA
> *Accelerating continuum mechanics and 3D structural stress field inference by 100× using Physics-Informed Neural Networks.*

- **Domain:** Scientific Machine Learning (SciML), Solid Mechanics, Fracture Mechanics, WebGL Visualization.
- **Core Engineering Capabilities:**
  - **Navier-Cauchy PDE Loss Formulations:** PyTorch neural networks trained with custom loss terms enforcing equilibrium, strain-displacement compatibility, and traction boundary conditions.
  - **Fracture Mechanics Integration:** Implements Linear Elastic Fracture Mechanics (LEFM), Elastic-Plastic Fracture Mechanics (EPFM), Extended Finite Element Method (XFEM), Peridynamics, and Paris Law fatigue crack propagation.
  - **FEA Mesh Ingestion:** High-speed parser for Abaqus and CalculiX `.vtk` / `.inp` mesh formats yielding sub-millimeter displacement resolution.
  - **3D WebGL Scientific Visualizer:** Interactive Three.js viewport supporting orbit controls, dynamic mesh slicing, and real-time Von Mises stress contour rendering.
- **Tech Stack:** `Python 3.10+`, `PyTorch`, `FastAPI`, `PyVista`, `React 18`, `Three.js`, `WebGL`, `Docker`.
- **Directory:** [`./PhysiTwin`](./PhysiTwin)

---

### 3. 🏢 [Enterprise MERN ERP & CRM Platform](./enterprise-erp-crm)
> *Production-grade, scalable multi-tenant corporate management platform with automated billing and customer pipelines.*

- **Domain:** Enterprise SaaS, Full-Stack Web Architecture, Database Normalization, RBAC.
- **Core Engineering Capabilities:**
  - **Commercial Pipeline:** End-to-end sales lifecycle tracking from initial client lead capture to quote issuance and final invoice delivery.
  - **Automated Document Synthesis:** Server-side PDF generation pipeline converting dynamic invoice records into vector-quality commercial receipts.
  - **Security & Multi-Tenancy:** Granular Role-Based Access Control (RBAC), JSON Web Token (JWT) session security, and indexed MongoDB querying for rapid pagination.
- **Tech Stack:** `React 18`, `Ant Design (AntD)`, `Redux Toolkit`, `Node.js`, `Express.js`, `MongoDB Atlas`, `Docker`, `Nginx`.
- **Directory:** [`./enterprise-erp-crm`](./enterprise-erp-crm)

---

### 4. 🤖 [AI-Powered Code Reviewer & PR Security Inspector](./ai-code-reviewer)
> *Automated code health, static security vulnerability scanner, and refactoring assistant powered by Google Gemini AI.*

- **Domain:** Developer Productivity Tooling, LLM Integration, AST & Static Analysis.
- **Core Engineering Capabilities:**
  - **Contextual Security Analysis:** Identifies OWASP Top 10 vulnerabilities, resource leaks, race conditions, and algorithmic inefficiencies in submitted code snippets.
  - **Interactive Code Environment:** Dual-pane browser IDE featuring real-time syntax highlighting (`PrismJS`), language auto-detection, and structured Markdown review output.
- **Tech Stack:** `React 19`, `Vite`, `PrismJS`, `Node.js`, `Express.js`, `@google/generative-ai` SDK, `Docker`.
- **Directory:** [`./ai-code-reviewer`](./ai-code-reviewer)

---

## 🔬 Specialized Robotics & Computer Vision Ecosystems

In addition to the systems hosted directly in this repository, the following standalone open-source projects highlight advanced robotics kinematics, 3D game engine simulation, and computer vision:

| Project | Highlights & Domain | Technologies | Repository |
|---|---|---|:---:|
| **Defect Detection in Gear & Bearing** | STFT Vibration Spectrograms + Domain-Adapted ResNet-50 + ML Ensembles. 100% clean / 99.2% noisy accuracy. | `PyTorch`, `ResNet-50`, `Scikit-Learn`, `STFT` | [🔗 View Project](https://github.com/Omgiri01/defect-detection-of-gear-and-bearing-using-ML) |
| **Spherical Robot Unity Simulation** | Real-time 3D simulation of 3-DOF spherical arm (R-R-P) with multi-touch virtual joysticks & trajectory tracing. | `Unity 2022.3 LTS`, `C#`, `URP`, `Android APK` | [🔗 View Project](https://github.com/Omgiri01/spherical-robot-unity) |
| **Spherical Robot Workspace Simulator** | Standard DH forward kinematics, 3D polygonal Matplotlib visualizer, and workspace boundary sweep datasets. | `Python`, `NumPy`, `Matplotlib`, `JSON` | [🔗 View Project](https://github.com/Omgiri01/spherical-robot-workspace) |
| **Robotics Manipulator Kinematics** | 2-DOF planar trajectory inverse kinematics solver + 6-DOF industrial DH forward kinematics GUI dashboard. | `Python`, `NumPy`, `Matplotlib`, `Tkinter` | [🔗 View Project](https://github.com/Omgiri01/robotics-manipulator-kinematics) |
| **Biometric Attendance System** | Real-time face detection, anti-spoofing liveness verification, DeepFace embeddings, and SQLite logging. | `OpenCV`, `DeepFace`, `SQLite`, `pyttsx3` | [🔗 View Project](https://github.com/Omgiri01/face-detection-attendance-system) |

---

## 🛠️ Technical Skills Matrix

```
                     ┌──────────────────────────────────────────────┐
                     │          CORE TECHNICAL DISCIPLINES          │
                     └──────────────────────┬───────────────────────┘
          ┌─────────────────────┬───────────┴───────────┬─────────────────────┐
          ▼                     ▼                       ▼                     ▼
┌──────────────────┐  ┌──────────────────┐    ┌──────────────────┐  ┌──────────────────┐
│ BACKEND & DISTR. │  │ FRONTEND & 3D    │    │ SCIENTIFIC AI    │  │ DEVOPS & CLOUD   │
├──────────────────┤  ├──────────────────┤    ├──────────────────┤  ├──────────────────┤
│ • FastAPI        │  │ • React 18 / 19  │    │ • PyTorch        │  │ • Docker Compose │
│ • Node / Express │  │ • Three.js WebGL │    │ • SciPy / NumPy  │  │ • Nginx Reverse  │
│ • Apache Kafka   │  │ • TypeScript     │    │ • PINNs (SciML)  │  │ • Redis In-Mem   │
│ • WebSockets     │  │ • Redux Toolkit  │    │ • OpenCV         │  │ • PostgreSQL     │
│ • RESTful APIs   │  │ • Tailwind CSS   │    │ • DeepFace       │  │ • MongoDB Atlas  │
│ • Microservices  │  │ • Ant Design     │    │ • Scikit-Learn   │  │ • Linux / Bash   │
└──────────────────┘  └──────────────────┘    └──────────────────┘  └──────────────────┘
```

- **Programming Languages:** Python, JavaScript (ES6+), TypeScript, C#, C++, SQL, HTML5/CSS3
- **Distributed & Backend Engineering:** FastAPI, Node.js, Express.js, Apache Kafka, Redis, WebSockets, Celery, RESTful API Design, Microservices Architecture
- **Frontend & 3D Graphics:** React 18/19, Three.js, WebGL, Vite, Redux Toolkit, TailwindCSS, Ant Design, Canvas API
- **AI, Machine Learning & Computer Vision:** PyTorch, TensorFlow, Physics-Informed Neural Networks (PINNs), Scikit-Learn, OpenCV, DeepFace, ResNet-50 Domain Adaptation, STFT Signal Processing
- **Databases & Time-Series Storage:** PostgreSQL, TimescaleDB, MongoDB Atlas, SQLite, Redis Pub/Sub
- **DevOps, Infrastructure & Tooling:** Docker, Docker Compose, Git, Linux, Nginx, Vercel, PyInstaller

---

## 📂 Repository Structure & Quickstart

```text
SDE/
├── QuantRiskPro/             # Distributed real-time quantitative risk analytics platform
├── PhysiTwin/                # Multi-physics PINN digital twin for fracture & FEA
├── enterprise-erp-crm/       # Full-stack enterprise MERN ERP & CRM platform
├── ai-code-reviewer/         # AI-powered static code analysis & PR inspector
├── builder-ai-assets/        # Shared portfolio visual design assets
└── README.md                 # Primary portfolio documentation
```

### Running Applications Locally

Each project in this repository is fully containerized with its own `docker-compose.yml` for isolated, one-command deployment:

#### 1. Launch QuantRiskPro:
```bash
cd QuantRiskPro
docker compose up --build
```
*Access frontend at `http://localhost:3000`, API documentation at `http://localhost:8000/docs`.*

#### 2. Launch Enterprise ERP & CRM:
```bash
cd enterprise-erp-crm
docker compose up --build
```
*Access web interface at `http://localhost:3000`.*

#### 3. Launch AI Code Reviewer:
```bash
cd ai-code-reviewer
docker compose up --build
```
*Access code reviewer dashboard at `http://localhost:5173`.*

---

## 👤 Author & Contact

**Om Giri**  
*Software Development Engineer | Distributed Systems, Scientific AI & Robotics*  

- **GitHub Profile:** [@Omgiri01](https://github.com/Omgiri01)
- **Portfolio Repository:** [https://github.com/Omgiri01/SDE](https://github.com/Omgiri01/SDE)
- **Email / Inquiries:** Contact via GitHub Profile

---

## 📄 License

This repository and all sub-modules are open-sourced under the [MIT License](LICENSE).
