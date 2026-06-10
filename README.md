# ITR HUB - Distributed RPA & Asynchronous Processing Engine

ITR HUB is a highly scalable, distributed job processing system and Robotic Process Automation (RPA) engine built with FastAPI. It automates Income Tax Return (ITR) operations by accepting user-uploaded Excel files containing PAN IDs and passwords, asynchronously scraping the Indian Income Tax e-portal using headless Selenium browsers, and returning the extracted refund statuses directly into the original Excel file.

## 🚀 Key Features

* **Asynchronous Batch Processing:** Processes thousands of records concurrently without blocking the main web server using Redis and RQ (Redis Queue).
* **Headless Web Automation:** Utilizes Selenium WebDriver equipped with advanced anti-bot evasion heuristics (bypassing WAFs) to interact with the tax portal.
* **Smart Job Scheduling:** Supports deferred execution of scraping jobs via `rq-scheduler`, allowing Chartered Accountants to run bulk checks during off-peak night hours.
* **Real-time Notifications:** Leverages the Redis Pub/Sub messaging pattern to instantly compile Excel files and notify the frontend when a background batch completes.
* **Command Center AI:** Features an NLP-to-SQL integration using Google Gemini, allowing users to query their database and job histories using plain English (e.g., *"Show me all failed jobs from yesterday"*).
* **Microservices Architecture:** Orthogonally decoupled Gateway API, Tasks API, and Background Workers for independent horizontal scaling.

## 🏗️ Architecture Overview

The system is built on a strictly decoupled microservices topology:

1. **Frontend API (Gateway - Port 8001):** The sole public-facing service. Handles secure JWT authentication, sanitizes `.xlsx` file uploads via `openpyxl`, and runs a daemon listener thread for Redis Pub/Sub events.
2. **Tasks API (Router - Port 8000):** An internal routing service that receives parsed JSON payloads from the Gateway and dispatches them to the appropriate Redis data structures (immediate queue vs. deferred scheduler).
3. **Execution Nodes (RQ Workers):** Independent Python processes that poll Redis, launch headless Chromium/Firefox browsers, execute the web scraping algorithm, and write output results to PostgreSQL.
4. **Redis:** Acts as the high-speed, in-memory message broker and Pub/Sub event handler.
5. **PostgreSQL:** The ACID-compliant relational persistence layer utilizing `JSONB` for dynamic payloads and `UUIDv4` for cryptographic primary keys.

## 🛠️ Technology Stack

* **Backend Framework:** FastAPI (v0.135.1) / Uvicorn (ASGI)
* **Task Queues & Scheduling:** Redis, RQ, RQ-Scheduler
* **Database:** PostgreSQL (with `psycopg2`)
* **Web Automation:** Selenium WebDriver (ChromeDriver / GeckoDriver)
* **File Handling:** openpyxl
* **Security:** PyJWT, Bcrypt
* **AI Integration:** Google Generative AI (Gemini)
* **Deployment & CI/CD:** Railway.app, GitHub Webhooks, Nixpacks

## ⚙️ Environment Variables

To run this project locally or in production, configure the following environment variables (e.g., in a `.env` file or cloud dashboard):

```env
DATABASE_URL=postgresql://user:password@localhost:5432/itr_hub
REDIS_URL=redis://localhost:6379/0
JWT_SECRET_KEY=your_super_secret_cryptographic_key
API2URL=http://localhost:8000/job    # Internal Tasks API Route
UPLOAD_DIRECTORY=./local_storage/    # Local path for file ingestion
ENVIRONMENT=development              # Set to 'production' for cloud deployment
RAILWAY=true                         # Set to true if deploying on Railway PaaS

```

## 💻 Local Installation & Setup

1. **Clone the repository:**
```bash
git clone [https://github.com/cgamingpro/ITR_hub.git](https://github.com/cgamingpro/ITR_hub.git)
cd ITR_hub

```


2. **Install dependencies:**
```bash
pip install -r requirements.txt

```


3. **Start local Infrastructure:**
Ensure your local instances of **Redis** and **PostgreSQL** are active.
4. **Boot the Internal Tasks API (Router):**
```bash
uvicorn tasks_main:app --port 8000 --reload

```


5. **Boot the Frontend Gateway API:**
```bash
uvicorn frontend_main:app --port 8001 --reload

```


6. **Start the Background RQ Worker:**
```bash
rq worker high default low --with-scheduler

```



## ☁️ Cloud Deployment (Railway.app)

ITR_hub is fully optimized for GitOps deployment on Railway.app using **Nixpacks** containerization.

1. Link your GitHub repository to a new Railway Project.
2. Provision managed **PostgreSQL** and **Redis** plugins within the Railway environment.
3. Nixpacks will automatically handle the complex OS-level dependencies required for headless Selenium (e.g., `chromium` and `chromedriver` binaries).
4. The system utilizes a `Procfile` to asymmetrically orchestrate the web gateway and the worker nodes:
```procfile
web: uvicorn main:app --host 0.0.0.0 --port $PORT
worker: rq worker high default low --with-scheduler

```



## 📡 Core API Endpoints

| Method | Endpoint | Description |
| --- | --- | --- |
| `POST` | `/login` | Authenticates user and issues a Bearer JWT. |
| `POST` | `/upload` | Accepts multipart/form-data Excel uploads and queues batch jobs. |
| `GET` | `/requests/{id}/download` | Returns the compiled `.xlsx` file with automation results appended. |
| `GET` | `/stats` | Aggregates global user job statistics for analytical dashboards. |
| `POST` | `/ai/query` | Executes natural-language NLP-to-SQL queries inside a CTE Sandbox. |

```

```
