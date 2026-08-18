# PINN-FEA-DigitalTwin: Physics-Informed Neural Network for FEA Stress & Fracture Analysis

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Stack](https://img.shields.io/badge/PyTorch-PINN-orange.svg)](#tech-stack)
[![Frontend](https://img.shields.io/badge/React-Three.js-blue.svg)](#tech-stack)
[![Backend](https://img.shields.io/badge/FastAPI-WebSockets-green.svg)](#tech-stack)

A multi-physics **Physics-Informed Neural Network (PINN)** Digital Twin platform that predicts structural stress field distributions ($\sigma_{xx}, \sigma_{yy}, \tau_{xy}$) and Von Mises yield invariants ($\sigma_{vm}$) on complex finite element meshes in real time.

Developed by **Om Giri**.

---

## 🔬 Mathematical & Physics Formulation

### 1. Navier-Cauchy Momentum Equilibrium Equations
In continuum mechanics, internal static equilibrium without body forces is governed by:

$$\nabla \cdot \boldsymbol{\sigma} + \mathbf{b} = \mathbf{0}$$

In 2D planar elasticity, this simplifies to partial differential equations (PDEs):

$$\frac{\partial \sigma_{xx}}{\partial x} + \frac{\partial \tau_{xy}}{\partial y} = 0$$

$$\frac{\partial \tau_{xy}}{\partial x} + \frac{\partial \sigma_{yy}}{\partial y} = 0$$

### 2. PINN Loss Function Architecture
The neural network enforces both sensor data alignment and physical conservation laws via automatic differentiation ($\text{autograd}$):

$$\mathcal{L}_{\text{total}} = \mathcal{L}_{\text{data}} + \lambda_{\text{pde}} \mathcal{L}_{\text{PDE}} + \lambda_{\text{bc}} \mathcal{L}_{\text{BC}}$$

where:

$$\mathcal{L}_{\text{PDE}} = \frac{1}{N} \sum_{i=1}^{N} \left[ \left( \frac{\partial \sigma_{xx}^{(i)}}{\partial x} + \frac{\partial \tau_{xy}^{(i)}}{\partial y} \right)^2 + \left( \frac{\partial \tau_{xy}^{(i)}}{\partial x} + \frac{\partial \sigma_{yy}^{(i)}}{\partial y} \right)^2 \right]$$

### 3. Von Mises Stress Invariants
The 2D equivalent Von Mises stress invariant ($\sigma_{vm}$) is calculated across all node coordinates:

$$\sigma_{vm} = \sqrt{\sigma_{xx}^2 - \sigma_{xx}\sigma_{yy} + \sigma_{yy}^2 + 3\tau_{xy}^2}$$

---

## 🛠️ Tech Stack & System Architecture

```
                                +---------------------------+
                                |  Three.js / React 18 Canvas|
                                | (3D Stress Heatmap Shaders)|
                                +-------------+-------------+
                                              ^
                                     WebSockets Stream
                                              v
+------------------------+      +-------------+-------------+      +------------------------+
| Abaqus / VTK FEA Mesh  | ---> |   FastAPI Async Gateway   | ---> |  PyTorch PINN Engine   |
| (.inp / .vtk Files)    |      | (Mesh Node Parser Pipeline)|      | (Physics Loss Invariant|
+------------------------+      +---------------------------+      +------------------------+
```

- **Physics & AI Engine**: PyTorch, Automatic Differentiation, Physics-Informed Neural Networks (PINNs), PyVista, NumPy
- **Backend API**: FastAPI, Async WebSockets, Pydantic, Uvicorn
- **Frontend 3D Visualizer**: React 18, Three.js, React Three Fiber (`@react-three/fiber`), Tailwind CSS
- **DevOps & Containerization**: Docker, Docker Compose, Nginx

---

## 🚀 Getting Started

### 🐳 Run with Docker (Recommended)

```bash
git clone https://github.com/Omgiri01/SDE.git
cd SDE/pinn-fea-digital-twin

# Build and launch multi-container architecture:
docker-compose up --build -d
```

* **Frontend Dashboard**: `http://localhost:3000`
* **FastAPI Backend Docs**: `http://localhost:8000/docs`

---

## 💻 Manual Setup

### 1. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).  
Created with ❤️ by **Om Giri**.
