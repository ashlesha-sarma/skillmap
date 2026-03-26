# SkillMap  
A personalized learning path and skill tracking platform for developers

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Available-green?style=for-the-badge&logo=vercel)](https://skillmap-eight.vercel.app)

---

### 🧱 Tech Stack

![Next.js](https://img.shields.io/badge/Frontend-Next.js-black?style=for-the-badge&logo=nextdotjs)
![Node.js](https://img.shields.io/badge/Backend-Node.js-339933?style=for-the-badge&logo=nodedotjs)
![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL-316192?style=for-the-badge&logo=postgresql)
![Prisma](https://img.shields.io/badge/ORM-Prisma-2D3748?style=for-the-badge&logo=prisma)
![Render](https://img.shields.io/badge/Deployment-Render-46E3B7?style=for-the-badge&logo=render)
![Vercel](https://img.shields.io/badge/Frontend%20Hosting-Vercel-000000?style=for-the-badge&logo=vercel)

---

### 🧠 Problem

Developers often struggle with unstructured learning paths and lack visibility into their progress, leading to inefficient skill development.

---

### 💡 Solution

SkillMap provides a structured, trackable roadmap system where users can follow curated paths, monitor progress, and manage learning efficiently.

---

### ✨ Features

- Structured skill roadmaps (topic-wise progression)  
- Progress tracking across learning modules  
- Authentication and user-specific data  
- Persistent storage with relational database  
- Clean and responsive UI  

---

### 🏗️ Architecture

Client (Next.js) → API (Node.js / Express) → ORM (Prisma) → PostgreSQL

---

### ⚙️ Setup

```bash
git clone https://github.com/your-username/skillmap.git
cd skillmap

# install dependencies
npm install

# setup environment
cp .env.example .env

# run development server
npm run dev
