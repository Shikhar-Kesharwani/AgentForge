# AgentForge Deployment Guide

This repository supports two distinct execution models: **Local (Docker)** and **Cloud (Managed)**.

---

## Model 1: Local Execution (Docker Compose)
Use this model if you want to run the stack entirely on your own machine. It uses local storage (SQLite for relationships, ChromaDB for vectors).

**Requirements:** Docker & Docker Compose installed.

1. Create a `.env` file in the root directory and add your keys:
   ```env
   GEMINI_API_KEY=your_google_api_key_here
   API_KEY=your_custom_agentforge_password
   ```
2. Run the stack:
   ```bash
   docker-compose up --build -d
   ```
3. Access the frontend at **http://localhost:3000**
4. *Note: Data is saved to the `./workspace` and `./memory_db` folders locally.*

---

## Model 2: Cloud Execution (Vercel + Render + Pinecone/Postgres)
Use this model to deploy a highly available, globally accessible application.

### Step 1: Deploy the Backend (Render.com)
1. Create a free account on [Render.com](https://render.com).
2. Click **New +** -> **Web Service**.
3. Connect your GitHub repository (`AyushGU12/AgentForge`).
4. Render will automatically detect the Dockerfile. In settings, make sure the **Dockerfile path** is set to `backend.Dockerfile`.
5. Add the following **Environment Variables** in the Render dashboard:
   - `GEMINI_API_KEY`: (Your Gemini Key)
   - `API_KEY`: (Your custom API password)
   - `DATABASE_URL`: (Optional: URL to a managed PostgreSQL DB like Supabase/Neon for Chat Sessions)
   - `PINECONE_API_KEY`: (Optional: Your Pinecone API Key for Cloud Vector Memory)
   - `PINECONE_INDEX_NAME`: `agentforge`
6. Click **Deploy**. Once finished, Render will give you a public URL (e.g., `https://agentforge-backend.onrender.com`).

### Step 2: Update the Frontend
Before deploying the frontend, open `static/app.js` locally.
Find the `API_BASE_URL` variable around line 226 and replace `https://YOUR_BACKEND_URL.onrender.com` with the actual URL Render gave you.

### Step 3: Deploy the Frontend (Vercel)
1. Create a free account on [Vercel](https://vercel.com).
2. Click **Add New Project** and import your GitHub repository.
3. In the **Framework Preset**, select **Other**.
4. In the **Root Directory**, click Edit and select the `static` folder. 
5. Click **Deploy**.

Vercel will give you a lightning-fast public URL for your frontend UI. 

**Congratulations! Your decoupled AgentForge application is now live on the cloud.**
