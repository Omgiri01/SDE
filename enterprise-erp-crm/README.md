# Enterprise MERN ERP & CRM Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Stack](https://img.shields.io/badge/Stack-MERN%20(MongoDB%2C%20Express%2C%20React%2C%20Node)-green)](#tech-stack)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue)](docker-compose.yml)

A production-grade, multi-tenant Enterprise Resource Planning (ERP) and Customer Relationship Management (CRM) platform built with the **MERN Stack** (MongoDB, Express.js, React.js, Node.js), Ant Design UI, and Redux Toolkit.

Developed by **Om Giri**.

---

## 🌟 Key Features

- 🧾 **Automated Invoice & Quote Management**: Generate, customize, and track invoices, receipts, quotes, and payment statuses.
- 👥 **Customer & Lead CRM**: Comprehensive contact management, lead pipeline tracking, and customer interaction logs.
- 💳 **Payment & Multi-Currency Processing**: Flexible payment recording with currency calculations.
- 🔐 **Role-Based Access Control (RBAC)**: Fine-grained security for Admin, Staff, and Client roles.
- 📄 **Automated PDF Generation**: Download and email PDF invoices directly to clients.
- 🐳 **Dockerized Deployment**: Fully containerized environment with Nginx reverse proxy and multi-stage builds.
- ⚡ **Automated CI/CD**: Pre-configured GitHub Actions pipelines for automated testing and cloud deployment.

---

## 🛠️ Tech Stack

- **Frontend**: React 18, Ant Design (AntD), Redux Toolkit, React Router v6, Vite
- **Backend**: Node.js v20, Express.js, Mongoose, JWT Authentication, Nodemailer/Resend, PDFKit/HTML-PDF
- **Database**: MongoDB Atlas (with indexing & multi-tenant schema isolation)
- **DevOps**: Docker, Docker Compose, Nginx, GitHub Actions CI/CD

---

## 📁 Repository Structure

```
enterprise-erp-crm/
├── backend/            # Express REST API, Mongoose Models, Controllers, Auth
├── frontend/           # React SPA, Ant Design Components, Redux Slices
├── docker-compose.yml  # Multi-container orchestration (MongoDB + Node API + Nginx React)
└── .github/workflows/ # CI/CD deployment pipelines
```

---

## 🚀 Quick Start (Docker Setup)

The easiest way to run the entire stack locally is via Docker:

```bash
# 1. Clone your repository
git clone https://github.com/omgiri01/enterprise-erp-crm.git
cd enterprise-erp-crm

# 2. Start all services (Backend, Frontend, MongoDB)
docker-compose up --build -d
```

Access the frontend at `http://localhost:3000` and the API at `http://localhost:8888/api`.

---

## 💻 Manual Local Development

### 1. Backend Setup

```bash
cd backend
npm install
cp .env.example .env
# Update MongoDB URI and JWT secrets in .env
npm run dev
```

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
Created with ❤️ by **Om Giri**.
