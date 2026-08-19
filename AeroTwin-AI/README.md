# AeroTwin-AI: Autonomous Micro-Turbojet & Airfoil Neural-CFD Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](requirements.txt)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0%2B-orange.svg)](src/)
[![Three.js](https://img.shields.io/badge/Three.js-WebGL-black.svg)](ui/)
[![Streamlit](https://img.shields.io/badge/Streamlit-App-red.svg)](app.py)

**AeroTwin-AI** is an advanced aerospace engineering digital twin and computational propulsion design platform. It bridges parametric 3D turbomachinery CAD modeling, Brayton-cycle thermodynamic analysis, PyTorch-based Neural CFD surrogate models, and interactive WebGL 3D flow visualization.

Developed by **Om Giri**.

---

## 🔬 Engineering & Mathematical Foundations

### 1. Brayton Cycle Thermodynamic Analysis
Evaluates key gas turbine performance metrics including compressor pressure ratio ($r_p$), turbine inlet temperature ($T_4$), specific thrust, and thrust-specific fuel consumption (TSFC):

$$
\eta_{\text{thermal}} = 1 - \frac{1}{r_p^{(\gamma - 1)/\gamma}}
$$

$$
F_{\text{thrust}} = \dot{m} (V_{\text{exhaust}} - V_{\text{inlet}}) + (P_{\text{exhaust}} - P_{\text{ambient}}) A_{\text{nozzle}}
$$

### 2. Neural-CFD Aerodynamic Surrogate Modeling
Replaces traditional 4-hour RANS-CFD mesh solvers with a PyTorch Deep Learning Surrogate Model, predicting pressure coefficient ($C_p$) distributions, shockwave locations, and boundary layer separation in under **40 milliseconds**:

$$
C_p = \frac{P - P_\infty}{\frac{1}{2} \rho_\infty V_\infty^2}
$$

### 3. Multi-Objective Aerodynamic Optimization
Implements NSGA-II genetic algorithms to simultaneously maximize thrust-to-weight ratio while minimizing aerodynamic drag and blade thermal stress.

---

## 🏗️ System Architecture

```
AeroTwin-AI/
├── src/               # Aerodynamic solvers, Brayton cycle thermodynamics, and neural networks
│   ├── aerodynamics/  # Airfoil camber/thickness and RANS-CFD surrogate predictors
│   ├── cad/           # Parametric 3D blade lofting, hub/shroud geometry generation
│   ├── engine/        # Compressor, combustor, turbine, and nozzle stage matching
│   └── surrogate/     # PyTorch neural surrogate models for instant flow inference
├── ui/                # WebGL Three.js 3D blade visualizer & contour renderer
├── config/            # Flight envelopes, atmospheric conditions, and material properties
├── tests/             # PyTest verification suite
├── app.py             # Full-stack interactive dashboard application
└── requirements.txt   # Python dependencies
```

---

## 🚀 Quick Start Guide

### 1. Installation

```bash
git clone https://github.com/Omgiri01/SDE.git
cd SDE/AeroTwin-AI

# Create virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Launch the Application

```bash
streamlit run app.py
```

Open `http://localhost:8501` to access the interactive 3D WebGL engine visualizer and aerodynamic design suite.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).  
Created with ❤️ by **Om Giri**.
