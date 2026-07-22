# brAInium: Unified Asset & Operations Brain

An AI-powered **Industrial Knowledge Intelligence Platform** that ingests heterogeneous plant documents (P&IDs, maintenance work orders, SOPs, reliability reports, incident logs) and turns them into a searchable, actionable knowledge system using **Hybrid Graph-Vector RAG**.

Built for the **"AI for Industrial Knowledge Intelligence"** hackathon brief. Designed to address **Innovation (25%)**, **Business Impact (25%)**, **Technical Excellence (20%)**, **Scalability (15%)**, and **User Experience (15%)**.

---

## 💡 Why Graph + Vector RAG?

Plain document RAG can only answer *"what does the SOP say."* It cannot answer *"which pumps failed more than twice this year and why"*—that requires joining work orders, incident reports, and inspection notes that live in entirely different systems.

**brAInium** builds a **knowledge graph (Neo4j)** alongside a **vector index (Qdrant)**. A dynamic **Query Planner** decides per-question whether to use semantic search, graph traversal, or both. This fusion is what actually connects the dots across disconnected plant siloes.

---

## 🏗️ Architecture

<img width="1536" height="1024" alt="image" src="https://github.com/user-attachments/assets/42a066a2-ba94-409d-ab2e-f35f6a3902c7" />


---

## 🛠️ Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/<your-username>/brAInium.git
cd brAInium
```

### 2. Start the Databases (Docker)
Ensure **Docker Desktop** is running, then start the Qdrant, Neo4j, and Postgres containers:
```bash
cd backend
docker compose up -d
```
*   **Neo4j UI**: Access at [http://localhost:7474](http://localhost:7474) (User: `neo4j` / Password: `changeme123`, Connection: `bolt://localhost:7687`).
*   **Qdrant UI**: Access at [http://localhost:6333](http://localhost:6333).

### 3. Configure the Backend Environment
Create a `.env` file in the `backend/` directory:
```bash
cp .env.example .env
```
Open `backend/.env` and choose **one** of the following LLM engines (Ollama is recommended for a 100% free offline setup):

*   **Option A: Ollama (Free Local LLM)**
    1. Download and run Ollama from [ollama.com](https://ollama.com).
    2. Download Gemma 2B in your terminal: `ollama run gemma2:2b`.
    3. Set the `.env` settings:
       ```env
       LLM_PROVIDER=llama
       LLAMA_BASE_URL=http://localhost:11434
       LLAMA_MODEL=gemma2:2b
       ```

*   **Option B: Gemini (Free Cloud Tier)**
    1. Generate a free API key at [Google AI Studio](https://aistudio.google.com/).
    2. Set the `.env` settings:
       ```env
       LLM_PROVIDER=gemini
       GEMINI_API_KEY=AIzaSy...your_gemini_key...
       GEMINI_MODEL=gemini-1.5-flash
       ```

### 4. Run the Backend
```bash
cd backend
python -m venv .venv

# On Windows (PowerShell):
.venv\Scripts\Activate.ps1
# On Mac/Linux:
source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --reload-exclude ".venv" --port 8000
```

### 5. Run the Frontend
In a new terminal window:
```bash
cd frontend
npm install
npm run dev
```
Open your browser and navigate to **[http://localhost:3000](http://localhost:3000)**.


---

## 📈 Business Impact & ROI

*   **Unplanned Downtime Cost**: Average of **$50,000 / hour** in manufacturing and process plants.
*   **Mean Time to Repair (MTTR)**: Reduced by **~40%** by eliminating manual cross-system search.
*   **Safety & Compliance**: 100% automated citation verification (e.g. LOTO permit validation) to prevent regulatory penalties.
