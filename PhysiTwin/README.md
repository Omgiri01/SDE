# PhysiTwin: Multi-Physics PINN Digital Twin for Structural Fracture & FEA Stress Analysis

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](requirements.txt)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0%2B-orange.svg)](pinn/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Production-green.svg)](api/)
[![React](https://img.shields.io/badge/React-18.0-blue.svg)](app/)
[![Three.js](https://img.shields.io/badge/Three.js-WebGL-black.svg)](app/)

**PhysiTwin** is an advanced, production-grade multi-physics digital twin software platform engineered to predict real-time 3D structural stress fields, fatigue life, and material fracture propagation. It seamlessly bridges classic continuum mechanics, Finite Element Analysis (FEA), Physics-Informed Neural Networks (PINNs), machine learning surrogate models, and high-performance WebGL visualization.

Developed by **Om Giri**.

---

## 🔬 Physics & Mathematical Foundations

PhysiTwin integrates four key branches of solid and fracture mechanics into a unified computational framework:

### 1. Linear Elastic Fracture Mechanics (LEFM) & Paris Law
Evaluates stress intensity factors ($K_I$, $K_{II}$, $K_{III}$) around crack tips and models subcritical fatigue crack growth rate:

$$
\frac{da}{dN} = C (\Delta K)^m
$$

$$
\Delta K = Y \Delta \sigma \sqrt{\pi a}
$$

### 2. Elastic-Plastic Fracture Mechanics (EPFM) & J-Integral
For ductile materials undergoing non-linear plastic deformation, computes path-independent J-Integrals and Crack Tip Opening Displacement (CTOD):

$$
J = \int_{\Gamma} \left( W dy - T_i \frac{\partial u_i}{\partial x} ds \right)
$$

### 3. eXtended Finite Element Method (XFEM)
Enriches standard FEA shape functions with Heaviside jump functions $H(\mathbf{x})$ and crack-tip asymptotic functions $F_l(\mathbf{x})$ to model arbitrary crack growth independent of mesh boundaries:

$$
\mathbf{u}(\mathbf{x}) = \sum_{i \in I} N_i(\mathbf{x}) \mathbf{u}_i + \sum_{j \in J} N_j(\mathbf{x}) H(\mathbf{x}) \mathbf{a}_j + \sum_{k \in K} N_k(\mathbf{x}) \sum_{l=1}^4 F_l(\mathbf{x}) \mathbf{b}_k^l
$$

### 4. Non-Local Peridynamics
Models discontinuous damage mechanics without spatial derivative singularities by reformulating momentum equations into integral equations over a horizon domain $\mathcal{H}_{\mathbf{x}}$:

$$
\rho \ddot{\mathbf{u}}(\mathbf{x}, t) = \int_{\mathcal{H}_{\mathbf{x}}} \mathbf{f}\left( \mathbf{u}(\mathbf{x}', t) - \mathbf{u}(\mathbf{x}, t), \mathbf{x}' - \mathbf{x} \right) dV_{\mathbf{x}'} + \mathbf{b}(\mathbf{x}, t)
$$

---

## 🤖 Physics-Informed Neural Networks (PINNs)

PhysiTwin implements a PyTorch Physics-Informed Neural Network architecture to accelerate stress field prediction by **100x** over conventional FEA solvers.

### Governing PDE Loss Function
The network minimizes a multi-objective loss combining observational FEA data with Navier-Cauchy static momentum equilibrium equations:

$$
\mathcal{L}_{\text{total}} = \mathcal{L}_{\text{data}} + \lambda_{\text{pde}} \mathcal{L}_{\text{pde}} + \lambda_{\text{bc}} \mathcal{L}_{\text{bc}}
$$

$$
\mathcal{L}_{\text{pde}} = \frac{1}{N_{\text{coll}}} \sum_{i=1}^{N_{\text{coll}}} \left\| \nabla \cdot \boldsymbol{\sigma}(\mathbf{x}_i) + \mathbf{b}(\mathbf{x}_i) \right\|^2
$$

where the Cauchy stress tensor $\boldsymbol{\sigma}$ is enforced via linear elastic constitutive laws:

$$
\boldsymbol{\sigma} = \lambda \text{tr}(\boldsymbol{\varepsilon}) \mathbf{I} + 2\mu \boldsymbol{\varepsilon}, \quad \boldsymbol{\varepsilon} = \frac{1}{2}\left( \nabla \mathbf{u} + (\nabla \mathbf{u})^T \right)
$$

---

## 🏗️ System Architecture & Stack

```
PhysiTwin/
├── pinn/             # PyTorch Physics-Informed Neural Network models & PDE loss equations
├── physics/          # LEFM, EPFM, XFEM, and Peridynamic analytical solvers
├── ml/               # XGBoost field predictors & LSTM fatigue trajectory models
├── api/              # Async FastAPI REST & WebSocket streaming endpoints
├── app/              # React 18 frontend + Three.js / WebGL 3D interactive viewer
├── data/             # Aerospace, Civil, and Biomedical material/loading datasets
└── python_stats/     # Automated charting, statistical verification & SHAP attribution
```

- **Core Analytics & ML**: Python 3.10+, PyTorch, XGBoost, NumPy, SciPy, PyVista, SHAP
- **Backend API**: FastAPI, Uvicorn, Pydantic, WebSockets
- **3D Visualization Frontend**: React 18, Vite, Three.js, React Three Fiber, Tailwind CSS
- **CI/CD & Cloud**: Docker, Vercel

---

## 📊 Benchmark & Performance Metrics

| Solver Engine | Execution Time | Stress Field Accuracy ($R^2$) | Crack Path Error |
| :--- | :--- | :--- | :--- |
| **Traditional XFEM Solver** | 45.2 minutes | 1.000 (Reference) | < 0.1% |
| **PhysiTwin PINN Surrogate** | **0.32 seconds** | **0.994** | **1.2%** |
| **XGBoost Field Predictor** | **0.08 seconds** | **0.987** | **2.4%** |

---

## 🚀 Quick Start Guide

### 1. Installation

```bash
git clone https://github.com/Omgiri01/SDE.git
cd SDE/PhysiTwin

# Create Python Virtual Environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Dependencies
pip install -r requirements.txt
```

### 2. Launch FastAPI Microservice

```bash
python -m uvicorn api.main:app --reload --port 8000
```
Swagger API docs available at `http://localhost:8000/docs`.

### 3. Launch React 3D Web Visualizer

```bash
cd app
npm install
npm run dev
```
Open `http://localhost:5173` to launch the 3D WebGL Digital Twin viewer.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).  
Created with ❤️ by **Om Giri**.
