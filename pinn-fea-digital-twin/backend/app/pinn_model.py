import os
import torch
import torch.nn as nn

class NavierCauchyPINN(nn.Module):
    """
    Physics-Informed Neural Network (PINN) for 2D/3D Elasticity & Fracture Mechanics.
    Predicts Displacement Field (u, v) and Stress Tensor Components (sigma_xx, sigma_yy, tau_xy).
    Enforces momentum equilibrium: div(sigma) + b = 0
    """
    def __init__(self, in_features=2, hidden_dim=64, out_features=5):
        super(NavierCauchyPINN, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(in_features, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, out_features)
        )

    def forward(self, x):
        return self.net(x)

def compute_von_mises_stress(sigma_xx, sigma_yy, tau_xy):
    """
    Computes 2D Von Mises Stress invariant from stress tensor components.
    sigma_vm = sqrt(sigma_xx^2 - sigma_xx*sigma_yy + sigma_yy^2 + 3*tau_xy^2)
    """
    return torch.sqrt(torch.clamp(
        sigma_xx**2 - sigma_xx * sigma_yy + sigma_yy**2 + 3 * (tau_xy**2),
        min=1e-8
    ))

def physics_loss_function(model, coords, E=210e9, nu=0.3):
    """
    Physics Loss: Navier-Cauchy Momentum Balance Equations in Continuum Mechanics.
    d(sigma_xx)/dx + d(tau_xy)/dy = 0
    d(tau_xy)/dx + d(sigma_yy)/dy = 0
    """
    coords.requires_grad_(True)
    predictions = model(coords)
    
    u = predictions[:, 0:1]
    v = predictions[:, 1:2]
    sigma_xx = predictions[:, 2:3]
    sigma_yy = predictions[:, 3:4]
    tau_xy = predictions[:, 4:5]
    
    # Automatic differentiation for spatial derivatives
    d_sig_xx_dx = torch.autograd.grad(sigma_xx, coords, torch.ones_like(sigma_xx), create_graph=True)[0][:, 0:1]
    d_tau_xy_dy = torch.autograd.grad(tau_xy, coords, torch.ones_like(tau_xy), create_graph=True)[0][:, 1:2]
    
    d_tau_xy_dx = torch.autograd.grad(tau_xy, coords, torch.ones_like(tau_xy), create_graph=True)[0][:, 0:1]
    d_sig_yy_dy = torch.autograd.grad(sigma_yy, coords, torch.ones_like(sigma_yy), create_graph=True)[0][:, 1:2]
    
    f_x = d_sig_xx_dx + d_tau_xy_dy
    f_y = d_tau_xy_dx + d_sig_yy_dy
    
    loss_pde = torch.mean(f_x**2) + torch.mean(f_y**2)
    return loss_pde
