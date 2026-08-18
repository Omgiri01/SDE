# PhysiTwin-FEA: Multi-Physics PINN Digital Twin for Material Fracture & Stress Analysis

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](requirements.txt)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0%2B-orange.svg)](pinn/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Production-green.svg)](api/)
[![React](https://img.shields.io/badge/React-18.0-blue.svg)](app/)

**PhysiTwin-FEA** is an end-to-end multi-physics digital twin application designed for real-time structural stress field prediction and material fracture propagation. It seamlessly bridges classical solid mechanics, Finite Element Analysis (FEA), Physics-Informed Neural Networks (PINNs), and interactive web technologies.

Developed by **Om Giri**.

---

## 🌟 Architectural Overview & Highlights

1. **Continuum & Fracture Mechanics Core**:
   - Implements Linear Elastic Fracture Mechanics (LEFM), Elastic-Plastic Fracture Mechanics (EPFM), eXtended Finite Element Method (XFEM), and Peridynamics models.
   - Evaluates stress intensity factors ($K_I$, $K_{II}$), strain energy release rates ($G$), and Von Mises yield criteria.

2. **Physics-Informed Neural Networks (PINNs)**:
   - Formulates PDE loss functions enforcing Navier-Cauchy momentum balance equations:
     $$\nabla \cdot \boldsymbol{\sigma} + \mathbf{b} = \mathbf{0}$$
   - Accelerates FEA stress contour evaluation by up to 100x compared to traditional iterative solvers.

3. **FastAPI High-Performance Microservice**:
   - RESTful and WebSocket API endpoints providing async inference and real-time stress array streaming.

4. **React & WebGL Visualizer**:
   - Interactive web interface for uploading parametric meshes, configuring mechanical loads, and rendering real-time 3D stress heatmaps.

---

## 🛠️ Tech Stack

- **Physics & ML Engine**: Python 3.10+, PyTorch, NumPy, SciPy, PyVista, Meshio
- **Backend Service**: FastAPI, Uvicorn, Pydantic, WebSockets
- **Frontend App**: React 18, Vite, Three.js / React Three Fiber, Tailwind CSS
- **Deployment**: Docker, Docker Compose, Vercel

---

## 📁 Repository Structure

```
pinn-fea-digital-twin/
├── api/             # FastAPI REST & WebSocket server
├── app/             # React 18 web UI & Three.js 3D visualizer
├── pinn/            # PyTorch Physics-Informed Neural Network models & PDE losses
├── physics/         # LEFM, EPFM, XFEM & Peridynamics solid mechanics solvers
├── ml/              # Surrogate ML models & training pipelines
├── data/            # Material database & FEA mesh datasets
└── requirements.txt # Python dependencies
```

---

## 🚀 Quick Start Guide

### 1. Environment Setup

```bash
cd pinn-fea-digital-twin
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Launch FastAPI Backend

```bash
python -m uvicorn api.main:app --reload --port 8000
```
API Documentation will be available at `http://localhost:8000/docs`.

### 3. Launch React Frontend

```bash
cd app
npm install
npm run dev
```
Open `http://localhost:5173` to interact with the 3D digital twin UI.

---

## 📄 License

Distributed under the MIT License. Created with ❤️ by **Om Giri**.
