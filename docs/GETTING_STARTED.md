# Getting Started with Ultimate Advisor

A complete step-by-step guide for beginners to set up and run the Ultimate Advisor RAG application **natively on Windows 11**.

**✅ 100% Windows Native** - No Docker, no containers, runs directly on your Windows machine.

## Prerequisites

Before you begin, make sure you have:

### 1. Python 3.12 or Higher

```bash
# Check if you have Python
python --version
```

**If you need to install Python:**
- Download from https://www.python.org/downloads/
- During installation, **check "Add Python to PATH"**
- Restart your terminal after installation

### 2. Git

```bash
# Check if you have Git
git --version
```

**If you need to install Git:**
- Download from https://git-scm.com/download/win
- Use default installation settings

### 3. API Keys

**Anthropic API Key** (for Claude AI):
- Go to https://console.anthropic.com/
- Sign up and create an API key (starts with `sk-ant-api03-...`)

**VoyageAI API Key** (for embeddings):
- Go to https://www.voyageai.com/
- Sign up and get your API key (starts with `pa-...`)
- **Free tier**: 200 million tokens!

---

## Installation Steps

### Step 1: Clone the Project

```bash
cd Desktop
git clone https://github.com/dev-it-with-me/RagUltimateAdvisor.git
cd RagUltimateAdvisor
```

### Step 2: Install UV

```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
uv --version
```

### Step 3: Install Dependencies

```bash
uv sync
```

### Step 4: Configure Environment

```bash
copy .env.example .env
```

Edit `.env` with your API keys:
```env
APP_ANTHROPIC_API_KEY=sk-ant-api03-YOUR-KEY-HERE
APP_VOYAGE_API_KEY=pa-YOUR-KEY-HERE
```

### Step 5: Initialize Database

```bash
uv run python src/scripts/run_init_db.py
```

### Step 6: Load Documents

```bash
uv run python src/scripts/run_load_embeddings.py
```

### Step 7: Start the Application

```bash
uv run fastapi dev src/main.py --host 0.0.0.0 --port 8000
```

### Step 8: Open Your Browser

Visit: **http://localhost:8000**

---

## What Gets Created

When you run the application, these files/folders are created:

- `.chroma/` - Vector embeddings (can delete to re-index)
- `ultimate_advisor.db` - Query history (can delete to clear)
- `.venv/` - Python virtual environment (don't delete)
- `logs/` - Application logs

---

## Troubleshooting

**Port 8000 in use:**
```bash
uv run fastapi dev src/main.py --host 0.0.0.0 --port 8001
```

**No results from queries:**
- Re-run: `uv run python src/scripts/run_load_embeddings.py`

**API key errors:**
- Double-check your `.env` file has correct keys

**To start fresh:**
```bash
rmdir /s .chroma
del ultimate_advisor.db
uv run python src/scripts/run_init_db.py
uv run python src/scripts/run_load_embeddings.py
```

---

For detailed documentation, see `CLAUDE.md` or `README.md`.

Happy querying! 🎯
