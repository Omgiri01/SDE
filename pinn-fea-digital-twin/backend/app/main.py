import asyncio
import json
import torch
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from app.pinn_model import NavierCauchyPINN, compute_von_mises_stress

app = FastAPI(
    title="PINN FEA Digital Twin API",
    description="Physics-Informed Neural Network API for Structural Stress & Crack Inference",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize trained PINN surrogate model
model = NavierCauchyPINN()
model.eval()

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "PINN-FEA-DigitalTwin API",
        "author": "Om Giri",
        "pinn_status": "model_ready"
    }

@app.post("/api/predict-stress")
def predict_stress(mesh_points: list):
    """
    Evaluates stress field invariants on input mesh node coordinates.
    """
    coords_tensor = torch.tensor(mesh_points, dtype=torch.float32)
    with torch.no_grad():
        preds = model(coords_tensor)
        sigma_xx = preds[:, 2]
        sigma_yy = preds[:, 3]
        tau_xy = preds[:, 4]
        sigma_vm = compute_von_mises_stress(sigma_xx, sigma_yy, tau_xy)
    
    return {
        "node_count": len(mesh_points),
        "von_mises_stress": sigma_vm.numpy().tolist(),
        "max_stress_mpa": float(torch.max(sigma_vm).item() / 1e6)
    }

@app.websocket("/ws/live-simulation")
async def websocket_simulation(websocket: WebSocket):
    """
    WebSockets endpoint streaming live load step predictions to Three.js canvas.
    """
    await websocket.accept()
    try:
        load_step = 0
        while True:
            load_step += 1
            # Generate synthetic mesh node stress arrays for 3D visualization stream
            nodes = np.random.uniform(-1.0, 1.0, (200, 2)).astype(np.float32)
            coords = torch.tensor(nodes)
            with torch.no_grad():
                preds = model(coords)
                stress = compute_von_mises_stress(preds[:, 2], preds[:, 3], preds[:, 4]).numpy()
            
            payload = {
                "step": load_step,
                "nodes": nodes.tolist(),
                "stress": stress.tolist(),
                "max_stress_mpa": float(np.max(stress) * 150)
            }
            await websocket.send_json(payload)
            await asyncio.sleep(0.1) # 10 FPS stream
    except WebSocketDisconnect:
        print("WebSocket client disconnected.")
