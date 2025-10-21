# Getting Started with Ultimate Advisor

A complete step-by-step guide for beginners to set up and run the Ultimate Advisor RAG application.

## Table of Contents

- [Option 1: Docker Setup (Recommended for Beginners)](#option-1-docker-setup-recommended-for-beginners)
- [Option 2: Manual Setup (Without Docker)](#option-2-manual-setup-without-docker)
- [Using the Application](#using-the-application)
- [Troubleshooting](#troubleshooting)

---

## Option 1: Docker Setup (Recommended for Beginners)

Docker simplifies the setup by automatically installing and configuring everything you need.

### Prerequisites

You need to install these programs first:

1. **Docker Desktop**
   - Windows: Download from https://www.docker.com/products/docker-desktop/
   - Mac: Download from https://www.docker.com/products/docker-desktop/
   - Linux: Follow instructions at https://docs.docker.com/engine/install/
   - After installation, start Docker Desktop

2. **Git** (to download the project)
   - Windows: Download from https://git-scm.com/download/win
   - Mac: Open Terminal and type `git --version` (it will prompt to install if needed)
   - Linux: `sudo apt-get install git` (Ubuntu/Debian) or `sudo yum install git` (CentOS/RedHat)

### Step 1: Download the Project

Open your terminal (Command Prompt on Windows, Terminal on Mac/Linux):

```bash
# Navigate to where you want to store the project (e.g., your Desktop)
cd Desktop

# Download the project
git clone https://github.com/dev-it-with-me/RagUltimateAdvisor.git

# Enter the project folder
cd RagUltimateAdvisor
```

### Step 2: Get API Keys

You'll need two API keys (both have free tiers):

1. **Anthropic API Key** (for Claude AI):
   - Go to https://console.anthropic.com/
   - Sign up for an account
   - Navigate to API Keys section
   - Create a new key (starts with `sk-ant-api03-...`)
   - Copy and save it securely

2. **VoyageAI API Key** (for embeddings):
   - Go to https://www.voyageai.com/
   - Sign up for an account
   - Get your API key (starts with `pa-...`)
   - **Free tier**: 200 million tokens for voyage-3.5
   - Copy and save it securely

### Step 3: Configure Environment Variables

1. **Create your environment file:**

   **On Windows (Command Prompt):**
   ```cmd
   copy .env.example .env
   ```

   **On Mac/Linux (Terminal):**
   ```bash
   cp .env.example .env
   ```

2. **Edit the environment file:**
   - Open `.env` with a text editor (Notepad, VS Code, etc.)
   - Add your configuration:

   ```env
   # Database Configuration
   APP_PG_USER=postgres
   APP_PG_PASSWORD=your_secure_password
   APP_PG_DATABASE=ultimate_advisor
   APP_PG_PORT=5432

   # Anthropic Configuration
   APP_ANTHROPIC_API_KEY=sk-ant-api03-YOUR-KEY-HERE
   APP_ANTHROPIC_MODEL=claude-sonnet-4-0

   # VoyageAI Configuration (200M tokens FREE)
   APP_VOYAGE_API_KEY=pa-YOUR-KEY-HERE
   APP_VOYAGE_MODEL=voyage-3.5
   ```

   - **Replace the placeholder API keys with your actual keys**
   - **Change `your_secure_password`** to a password of your choice
   - Save the file

### Step 4: Start All Services

In your terminal, make sure you're in the project folder and run:

```bash
docker-compose up -d
```

**What happens:**
- `-d` means "detached mode" (runs in background)
- Docker will start two services: PostgreSQL database and the Backend
- **First time takes 1-2 minutes** to download PostgreSQL image

**Check if everything is running:**
```bash
docker-compose ps
```

You should see two services running:
- `postgres-pgvector`
- `ultimate-advisor-backend`

### Step 5: Watch the Logs (Optional but Helpful)

To see what's happening:

```bash
docker-compose logs -f backend
```

- Press `Ctrl+C` to stop watching (services keep running)
- Look for messages like "Ultimate Advisor API server started successfully"

### Step 6: Load the Ultimate Frisbee Rules

Once the backend is running, load your documents:

```bash
docker exec ultimate-advisor-backend uv run python src/scripts/run_load_embeddings.py
```

**What this does:**
- Reads PDF documents from the `data/` folder
- Converts them into AI-readable embeddings via VoyageAI API
- Stores embeddings in the PostgreSQL database
- Takes 1-3 minutes depending on document size

### Step 7: Access the Application

Open your web browser and go to:

**http://localhost:8000**

You should see the Ultimate Advisor chat interface!

### Managing Docker Services

**Stop all services:**
```bash
docker-compose down
```

**Start services again:**
```bash
docker-compose up -d
```

**View logs:**
```bash
docker-compose logs -f
```

**Restart a specific service:**
```bash
docker-compose restart backend
```

---

## Option 2: Manual Setup (Without Docker)

This method gives you more control but requires installing each component separately.

### Prerequisites

Install these programs in order:

#### 1. Python 3.12 or higher

**Windows:**
- Download from https://www.python.org/downloads/
- During installation, **check "Add Python to PATH"**
- Verify: Open Command Prompt and type `python --version`

**Mac:**
```bash
brew install python@3.12
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3.12 python3.12-venv python3-pip
```

#### 2. UV Package Manager

**Windows (PowerShell):**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Mac/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Verify installation:**
```bash
uv --version
```

#### 3. PostgreSQL 17 with pgvector

**Windows:**
1. Download PostgreSQL 17 from https://www.postgresql.org/download/windows/
2. Install with default settings
3. Remember the password you set for the `postgres` user
4. After installation, download pgvector from https://github.com/pgvector/pgvector/releases
5. Follow pgvector installation instructions for Windows

**Mac:**
```bash
brew install postgresql@17
brew services start postgresql@17
brew install pgvector
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt install postgresql-17 postgresql-17-pgvector
sudo systemctl start postgresql
```

#### 4. API Keys

You'll need API keys from:

1. **Anthropic** (for Claude AI):
   - Sign up at https://console.anthropic.com/
   - Create an API key (starts with `sk-ant-api03-...`)

2. **VoyageAI** (for embeddings):
   - Sign up at https://www.voyageai.com/
   - Get your API key (starts with `pa-...`)
   - **Free tier**: 200 million tokens for voyage-3.5

### Step 1: Download the Project

```bash
# Navigate to your desired folder
cd Desktop

# Download the project
git clone https://github.com/dev-it-with-me/RagUltimateAdvisor.git

# Enter the project folder
cd RagUltimateAdvisor
```

### Step 2: Configure Environment

1. **Create environment file:**

   **Windows:**
   ```cmd
   copy .env.example .env
   ```

   **Mac/Linux:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` file:**

   Open with a text editor and configure:

   ```env
   # Database Configuration
   APP_PG_HOST=localhost
   APP_PG_PORT=5432
   APP_PG_USER=postgres
   APP_PG_PASSWORD=your_postgres_password
   APP_PG_DATABASE=ultimate_advisor

   # Anthropic Configuration
   APP_ANTHROPIC_API_KEY=sk-ant-api03-YOUR-KEY-HERE
   APP_ANTHROPIC_MODEL=claude-sonnet-4-0

   # VoyageAI Configuration (200M tokens FREE)
   APP_VOYAGE_API_KEY=pa-YOUR-KEY-HERE
   APP_VOYAGE_MODEL=voyage-3.5
   ```

   - Replace `your_postgres_password` with your PostgreSQL password
   - Replace the API keys with your actual keys from Anthropic and VoyageAI
   - Save the file

### Step 3: Set Up Python Environment

```bash
# Create virtual environment
uv venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate

# On Mac/Linux:
source .venv/bin/activate

# Install dependencies
uv sync
```

You should see `(.venv)` at the start of your command prompt.

### Step 4: Create the Database

**Open PostgreSQL:**

**Windows:**
- Search for "pgAdmin 4" or "SQL Shell (psql)"

**Mac/Linux:**
```bash
psql -U postgres
```

**Create the database:**
```sql
CREATE DATABASE ultimate_advisor;
\q
```

**Enable pgvector extension:**
```bash
# Connect to the database
psql -U postgres -d ultimate_advisor

# Enable extension
CREATE EXTENSION vector;
\q
```

### Step 5: Initialize the Database Tables

Open a new terminal, navigate to the project folder, and activate the virtual environment:

```bash
cd RagUltimateAdvisor

# Activate virtual environment
# Windows:
.venv\Scripts\activate

# Mac/Linux:
source .venv/bin/activate

# Initialize database
uv run python src/scripts/run_init_db.py
```

When prompted:
- If tables don't exist: Type `y` to create them
- If tables exist: Type `k` to keep them (or `r` to recreate)

### Step 7: Load the Documents

Make sure you have PDF documents in the `data/` folder, then run:

```bash
uv run python src/scripts/run_load_embeddings.py
```

This will:
- Read all PDF files from `data/` folder
- Process them into embeddings
- Store them in the database
- Takes 2-5 minutes

### Step 6: Start the Backend Server

```bash
uv run fastapi dev src/main.py --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 7: Access the Application

Open your web browser and go to:

**http://localhost:8000**

---

## Using the Application

### Web Interface

1. Open http://localhost:8000 in your browser
2. Type your question in the chat box
3. Click Send or press Enter
4. Wait for the AI to respond (takes 5-30 seconds)

### Example Questions

Try asking:
- "What happens if the disc goes out of bounds?"
- "How many players are on the field for each team?"
- "What is a turnover in Ultimate Frisbee?"
- "Explain the spirit of the game rule"
- "What are the dimensions of an Ultimate field?"

### API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

You can test API endpoints directly from these interfaces.

### API Example

Using `curl`:

```bash
curl -X POST "http://localhost:8000/api/rag/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is a turnover?", "top_k": 3}'
```

Using Python:

```python
import requests

response = requests.post(
    "http://localhost:8000/api/rag/query",
    json={"query": "What is a turnover?", "top_k": 3}
)

result = response.json()
print(result["chat_response"])
```

---

## Troubleshooting

### Docker Issues

**Problem: "docker: command not found"**
- Solution: Make sure Docker Desktop is installed and running

**Problem: "Cannot connect to Docker daemon"**
- Solution: Start Docker Desktop application

**Problem: Services won't start**
```bash
# View detailed logs
docker-compose logs

# Restart services
docker-compose down
docker-compose up -d
```

**Problem: Port already in use (8000, 5432, or 11434)**
```bash
# Find what's using the port (Windows)
netstat -ano | findstr :8000

# Find what's using the port (Mac/Linux)
lsof -i :8000

# Kill the process or change the port in docker-compose.yaml
```

### Manual Setup Issues

**Problem: "uv: command not found"**
- Solution: Close and reopen your terminal after installing UV
- Or add UV to your PATH manually

**Problem: "psql: command not found"**
- Solution: Add PostgreSQL to your PATH
  - Windows: Add `C:\Program Files\PostgreSQL\17\bin` to PATH
  - Mac: `echo 'export PATH="/opt/homebrew/opt/postgresql@17/bin:$PATH"' >> ~/.zshrc`

**Problem: "Connection refused" to PostgreSQL**
```bash
# Check if PostgreSQL is running
# Windows: Open Services and look for "postgresql-x64-17"
# Mac: brew services list
# Linux: sudo systemctl status postgresql

# Start PostgreSQL
# Windows: Start the service from Services
# Mac: brew services start postgresql@17
# Linux: sudo systemctl start postgresql
```

**Problem: "Connection refused" to Ollama**
```bash
# Make sure Ollama is running
ollama serve

# Check if models are downloaded
ollama list
```

**Problem: Virtual environment activation fails**
- Windows: You may need to run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` in PowerShell
- Mac/Linux: Make sure you're using `source` command

**Problem: "No documents were loaded"**
- Make sure you have PDF files in the `data/` folder
- Check file permissions (files should be readable)

**Problem: Slow responses or timeouts**
- AI models need significant RAM (4-8 GB)
- First query is always slower (model initialization)
- Consider using smaller models if your system is slow

### Database Issues

**Problem: "Could not determine embedding dimension"**
- Make sure Ollama is running with `ollama serve`
- Verify the model is downloaded with `ollama list`

**Problem: "Dimension mismatch"**
- The embedding model changed and dimensions don't match
- Solution: Run the init script and choose to recreate tables

**Problem: Query returns no results**
- Make sure embeddings are loaded with `run_load_embeddings.py`
- Check document count at http://localhost:8000/api/rag/documents/count

### Getting Help

1. **Check the logs:**
   - Docker: `docker-compose logs -f`
   - Manual: Check the terminal where the server is running
   - Log files: `logs/server_logs/`

2. **Check system health:**
   - Visit http://localhost:8000/api/rag/health
   - Should show all components as healthy

3. **Verify services:**
   - PostgreSQL: Can you connect with `psql -U postgres`?
   - Ollama: Does `ollama list` show your models?
   - Backend: Does http://localhost:8000/health return "healthy"?

4. **Common fixes:**
   ```bash
   # Restart everything (Docker)
   docker-compose down
   docker-compose up -d

   # Restart everything (Manual)
   # Stop the backend (Ctrl+C)
   # Restart PostgreSQL and Ollama
   # Start backend again
   ```

5. **Still having issues?**
   - Open an issue: https://github.com/dev-it-with-me/RagUltimateAdvisor/issues
   - Provide:
     - Your operating system
     - Error messages from logs
     - Steps you've already tried

---

## Next Steps

- **Add your own documents:** Place PDF files in the `data/` folder and run `run_load_embeddings.py`
- **Customize models:** Change `APP_CHAT_MODEL` in `.env` to use different AI models
- **Explore the API:** Visit http://localhost:8000/docs to see all available endpoints
- **Modify the code:** The codebase is well-documented - check `CLAUDE.md` for architecture details

Happy querying! 🎯
