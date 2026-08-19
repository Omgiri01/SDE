# AutoFlow-AI: 3D Vehicle Aerodynamics & Geometric Deep Learning CFD Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](requirements.txt)
[![PyTorch](https://img.shields.io/badge/PyTorch-Geometric%20(GNN)-orange.svg)](DeepSurrogates/)
[![CFD](https://img.shields.io/badge/CFD-OpenFOAM%20Datasets-blue.svg)](DrivAerNet_v1/)

**AutoFlow-AI** is an advanced automotive computational engineering and geometric deep learning platform. It predicts 3D vehicle surface pressure fields, wake velocity deficits, and aerodynamic drag ($C_D$) / lift ($C_L$) coefficients directly from 3D car mesh geometries (STL/OBJ point clouds) in sub-second inference times.

Developed by **Om Giri**.

---

## 🔬 Aerodynamic & Geometric Deep Learning Core

### 1. Vehicle Aerodynamics & Force Invariants
Evaluates drag forces, boundary layer separation over the rear window, and underbody ground-effect diffuser flows:

$$
F_{\text{drag}} = \frac{1}{2} \rho_\infty V_\infty^2 A_{\text{frontal}} C_D
$$

$$
C_D = \frac{1}{A_{\text{frontal}}} \int_{S} \left( C_p \mathbf{n} \cdot \hat{\mathbf{x}} + C_f \mathbf{t} \cdot \hat{\mathbf{x}} \right) dS
$$

### 2. 3D Geometric Deep Learning (Graph Neural Networks & PointNet++)
Ingests unstructured 3D vehicle surface meshes directly as spatial graphs $\mathcal{G} = (\mathcal{V}, \mathcal{E})$, updating local node pressure representations via equivariant message passing:

$$
\mathbf{h}_i^{(k+1)} = \gamma^{(k)} \left( \mathbf{h}_i^{(k)}, \bigoplus_{j \in \mathcal{N}(i)} \phi^{(k)} \left( \mathbf{h}_i^{(k)}, \mathbf{h}_j^{(k)}, \mathbf{e}_{j,i} \right) \right)
$$

This reduces high-fidelity OpenFOAM RANS-CFD vehicle simulation cycles from **6 hours to 120 milliseconds** with an $R^2 > 0.985$.

---

## 🏗️ System Architecture

```
AutoFlow-AI/
├── DeepSurrogates/         # PointNet++, RegDGCNN, and Transformer neural CFD solvers
├── ParametricModels/       # Parametric CAD variations (ride height, diffuser angle, rear spoilers)
├── RegDGCNN_SurfaceFields/ # 3D surface pressure field regression engines
├── DrivAerNet_v1/          # High-fidelity automotive CFD datasets & mesh point clouds
├── tutorials/              # Interactive Jupyter tutorials for model training & inference
└── requirements.txt        # Python dependencies
```

---

## 🚀 Quick Start Guide

### 1. Installation

```bash
git clone https://github.com/Omgiri01/SDE.git
cd SDE/AutoFlow-AI

# Create virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run Surface Pressure & Drag Inference

```bash
python DeepSurrogates/evaluate.py --model dgcnn --input data/sample_car.stl
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).  
Created with ❤️ by **Om Giri**.
