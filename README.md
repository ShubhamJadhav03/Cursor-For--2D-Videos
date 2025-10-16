# 🎨 Manim AI — Text-to-Animation Video Generator

<div align="center">

> **An AI-powered platform that transforms text prompts into dynamic 2D animations — built with Manim, FastAPI, React, and Ollama.**

[![Docker](https://img.shields.io/badge/Docker-Ready-blue?logo=docker)](https://www.docker.com/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/Frontend-React-61DAFB?logo=react)](https://reactjs.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

</div>

---

## 🌟 Overview

**Manim AI** is a **full-stack web application** that generates stunning 2D animations directly from text prompts.  
It uses an **AI model (CodeLlama)** to produce Python code for the [Manim Engine](https://www.manim.community/) — bringing ideas to life as animated scenes.

The project includes a **3-panel scene editor** that allows users to preview, rearrange, and export multi-scene videos — all in a browser.



https://github.com/user-attachments/assets/527d7ac1-3cb2-4e1d-9298-41d8bf15ce78



---

## ✨ Key Features

| Category | Description |
|-----------|--------------|
| 🤖 **AI-Generated Animations** | Converts text prompts into executable Manim scripts using **CodeLlama** via **Ollama**. |
| 🎬 **3-Panel Scene Editor** | Built with React + Tailwind — includes Scene Bin, Drag-and-Drop Timeline, and Live Preview. |
| 🎞️ **Smart Video Stitching** | Combines multiple scenes into one polished `.mp4` file using **FFmpeg**. |
| ⚙️ **Scalable Backend** | Asynchronous FastAPI server with **Celery** workers for non-blocking video jobs. |
| 🐳 **One-Command Setup** | Entire stack runs in **Docker** — Frontend, Backend, Worker, Redis, PostgreSQL. |
| ✅ **CI/CD Ready** | Includes **GitHub Actions** + **Pytest** for automated backend testing. |

---

## 🧩 System Architecture

The application follows a **modern, microservices-oriented design**, ensuring scalability and fault isolation.

```mermaid
graph TD
    subgraph Browser
        A[React Frontend]
    end

    subgraph Server
        B[FastAPI Backend] --> C{Redis Queue}
        C --> D[Celery Worker]
        D --> E[Ollama - CodeLlama]
        D --> F[Manim Engine]
        F --> G[Rendered Videos]
        B <--> H[PostgreSQL Database]
        D <--> H
    end

    A -- "1️⃣ Send Text Prompt" --> B
    B -- "2️⃣ Create Job → Return ID" --> A
    A -- "3️⃣ Poll Job Status" --> B
    B -- "4️⃣ Check DB" --> H
    D -- "5️⃣ Update Job Status" --> H
    D -- "6️⃣ Render Video" --> F
    F -- "7️⃣ Output File" --> G
    B -- "8️⃣ Return Video URL" --> A
```

### 🧠 Workflow Summary
1. The **React frontend** sends the user’s prompt to the **FastAPI backend**.  
2. FastAPI logs the task in **PostgreSQL** and enqueues it in **Redis**.  
3. A **Celery worker** pulls the job, calls **Ollama → CodeLlama**, and runs **Manim** to render the animation.  
4. The worker updates the database with progress and file paths.  
5. The frontend polls for updates and previews the generated scene when ready.


## 🛠️ Tech Stack

| Layer | Technologies |
|-------|---------------|
| **Frontend** | `React`, `Tailwind CSS`, `@dnd-kit` (drag-and-drop) |
| **Backend** | `Python`, `FastAPI`, `SQLAlchemy`, `Celery`, `Redis`, `PostgreSQL` |
| **AI Engine** | `Ollama` (local LLM runtime) with `CodeLlama:7b` |
| **Animation** | `Manim` for 2D rendering, `FFmpeg` for stitching |
| **DevOps / CI** | `Docker`, `Docker Compose`, `GitHub Actions`, `Pytest` |

---

## ⚡ Getting Started (Local Setup)

The app is **fully containerized**, so you can spin it up with one command.

### 🧰 Prerequisites

Make sure you have:
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed & running  
- [Ollama](https://ollama.com/) installed and the model pulled:

  ```bash
  ollama pull codellama:7b
  ```

---

### 🚀 Installation & Setup

1. **Clone this repository**
   ```bash
   git clone https://github.com/ShubhamJadhav03/Cursor-For--2D-Videos.git
   cd Cursor-For--2D-Videos
   ```

2. **Build & start all services**
   ```bash
   docker-compose up --build
   ```
   > This command launches the Frontend, Backend, Worker, Redis, and PostgreSQL services simultaneously.

3. **Access the app**
   - 🌐 Frontend: [http://localhost:3000](http://localhost:3000)  
   - ⚙️ API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

4. **Shut down all services**
   ```bash
   Ctrl + C
   ```
   Or use:
   ```bash
   docker-compose down
   ```

---

## 🧭 Project Structure

```
Cursor-For--2D-Videos/
│
├── frontend/                # React UI with drag-and-drop scene editor
├── backend/
│   ├── main.py              # FastAPI entrypoint
│   ├── generation.py        # AI → Manim code logic
│   ├── worker.py            # Celery worker for background jobs
│   ├── config.py            # Database & environment configuration
│   └── models.py            # SQLAlchemy ORM models
│
├── docker-compose.yml       # Container orchestration
├── requirements.txt         # Python dependencies
├── package.json             # Frontend dependencies
└── README.md
```

---

## 🔮 Future Enhancements

| Feature | Description |
|----------|--------------|
| ☁️ **Cloud Deployment** | Deploy stack to **Render**, **AWS**, or **Azure**. |
| 🗣️ **AI Voiceovers** | Add **Text-to-Speech** narration with lip-sync support. |
| 👤 **User Accounts** | Add authentication + project management dashboard. |
| 🎨 **Custom Themes** | Enable users to modify Manim colors, fonts, or styles dynamically. |
| 📈 **Job Analytics** | Track render times, prompt complexity, and system metrics. |

---

## 💡 Inspiration & Learning

This project represents a deep dive into:
- Asynchronous job handling with **Celery + Redis**
- End-to-end AI workflow integration with **Ollama**
- Real-time UI feedback with **React hooks**
- Complex system orchestration using **Docker Compose**

> It’s more than a project — it’s a demonstration of full-stack AI engineering skills, from low-level system design to UX polish.

---

## 🧑‍💻 Author

**Shubham Jadhav**  
🚀 *AI & Full-Stack Developer*  
📍 Passionate about creating intelligent and scalable web systems.  

[![GitHub](https://img.shields.io/badge/GitHub-ShubhamJadhav03-black?logo=github)](https://github.com/ShubhamJadhav03)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-ShubhamJadhav-blue?logo=linkedin)](https://www.linkedin.com/in/shubham-jadhav-3058a42a7/)

---

## 🪪 License

This project is licensed under the **MIT License** — feel free to use, modify, and distribute it with attribution.

