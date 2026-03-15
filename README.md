# Job Hunter Dashboard 🚀

A fully automated, AI-powered web dashboard designed to help job seekers bypass manual job board hunting. Automatically scrape company career pages, filter postings matching your precise candidate profile using Anthropic's Claude 3.5 API, and manage your applications in a sleek, centralized dashboard.

**Live Demo**: [job-hunter-dashboard-kf6x.onrender.com](https://job-hunter-dashboard-kf6x.onrender.com)

---

## 🌟 How It Works

1. **Add Companies:** You input the name and career page URL of companies you want to track.
2. **Automated Scraping:** The backend uses `BeautifulSoup4` to parse the live HTML of target career pages, stripping away unnecessary javascript/css to extract the core text.
3. **AI Resume Matching:** The extracted text, along with your actual Resume in PDF format, is sent to Anthropic's **Claude-3.5-Sonnet** LLM. Claude is prompted with your precise requirements (e.g., F1 Visa Sponsorship friendly, strict entry-level, Data Science / MLE roles).
4. **Intelligent Extraction:** Claude responds with a structured JSON array of only the jobs that perfectly match your candidate profile.
5. **Persistent Tracking:** Results are stored in a cloud **Neon PostgreSQL** database.
6. **Application Management:** Review matched jobs in the UI. If you apply, click "Apply", and the job is moved to your "Applied" tab, ensuring the AI never scans or shows you that job again.

---

## 💻 Tech Stack

### Frontend (Client-Side)
- **HTML5 & CSS3**: Custom-built, responsive user interface featuring a modern "glassmorphism" aesthetic, CSS grid layouts, and smooth micro-animations.
- **Vanilla JavaScript**: Lightweight DOM manipulation, asynchronous fetching from the backend API, and interactive toast notifications without the overhead of heavy frameworks like React.

### Backend (Server-Side)
- **FastAPI**: Exceptionally fast, modern Python web framework handling routing and API endpoints asynchronously.
- **Uvicorn**: Lightning-fast ASGI web server for production deployment.
- **BeautifulSoup4 & Requests**: Used for making HTTP requests and robustly parsing irregular HTML structures from thousands of different company career sites.
- **Anthropic API (Claude 3.5 Sonnet)**: The core AI engine. Processes massive amounts of unstructured DOM text alongside a base64 encoded PDF resume to do highly intelligent, context-aware semantic screening.

### Database & Data Persistence
- **PostgreSQL**: Robust relational database engine.
- **Neon**: Serverless Postgres hosting platform. Provides a permanent free-tier database with native IPv4 pooling, acting as the single source of truth for all tracked companies, matched jobs, and applied application history.
- **Psycopg2**: Python adapter for Postgres, handling all database I/O via the custom `db.py` module.

### Infrastructure & Deployment
- **Render.com**: Fully managed PaaS. The Python backend and frontend static files are Dockerized and deployed as a unified Web Service hosted automatically via GitHub pushes.

---

## 🚀 Setup for Local Development

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Atharva309/job-hunter-dashboard.git
   cd job-hunter-dashboard
   ```

2. **Install requirements:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set your Environment Variables:**
   You will need to create two critical environment variables:
   - `ANTHROPIC_API_KEY`: Your Claude API token.
   - `DATABASE_URL`: Your PostgreSQL connection string (ex: from Neon or Supabase).
   
   *Tip: Create a `.env` file locally or export them in your terminal: `export DATABASE_URL="postgresql://..."`*

4. **Add your Resume:**
   Place your resume securely in the root directory named `portfolio.pdf`. This file is read by the AI for candidate matching.

5. **Run the Server:**
   ```bash
   uvicorn app:app --reload
   ```
   *The application will boot at `http://127.0.0.1:8000`*

---

## 📦 File Architecture
- `app.py`: The FastAPI server containing all endpoints (`GET /api/jobs`, `POST /api/companies`, etc.) and serving the static frontend files.
- `job_agent.py`: The AI and Scraping brain. Contains the logic for fetching HTML, cleaning it, wrapping it in the system prompt, and querying the Anthropic API.
- `db.py`: The Postgres interface. Safely parses connection strings, executes CRUD operations, and manages schema creation for `jobs` and `applied` tables.
- `static/`: Contains `styles.css`, `script.js`, and `index.html`.
- `requirements.txt`: Python package dependencies.
