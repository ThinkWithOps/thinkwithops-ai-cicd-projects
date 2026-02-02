# 🤖 Project 2: Build-Failure Explainer Bot

Automatically explains why your CI/CD build failed using local AI (Ollama) — **100% free, offline, and open-source**.

> 💡 Works with Jenkins, GitHub Actions, or any log file. Uses `phi3`, `llama3`, or other local models — no cloud APIs, no cost!

## 🎯 What It Does

- Reads a **CI build log** (from file or stdin)
- Sends the error snippet to a **local LLM** (via Ollama)
- Outputs:
  - A clear **root cause explanation**
  - **Actionable fix steps** (2–3 bullet points)
  - **Severity level**: high / medium / low

Perfect for quickly diagnosing build failures without digging through hundreds of log lines — all on your laptop, with no internet.

## 🛠️ Prerequisites

### 1. Install Ollama (Windows)
1. Go to https://ollama.com/download  
2. Download and install the **Windows version**  
3. After install, Ollama runs automatically in the background (check system tray)

> 🔍 **Ollama Install Location (Windows):**  
> `C:\Users\<YOUR_USERNAME>\AppData\Local\Programs\Ollama\`  
> You should see `ollama.exe` in that folder.

### 2. Add Ollama to Windows PATH *(Critical for CLI access)*

> ⚠️ Skip this if `ollama --version` already works in Git Bash/PowerShell.

#### Steps:
1. Press `Win + R` → type `sysdm.cpl` → Enter  
2. Go to **Advanced** tab → Click **Environment Variables**  
3. Under **System Variables**, find `Path` → Click **Edit**  
4. Click **New** → Add:  
   `C:\Users\<YOUR_USERNAME>\AppData\Local\Programs\Ollama`  
5. Click **OK** → restart your terminal  

### 3. Verify Ollama Installation

Open **Git Bash**, **PowerShell**, or **CMD** and run:

`ollama --version`

✅ Expected output:  
`ollama version 0.1.x`

Then check if Ollama is running:  
`ollama list`

✅ You should see:  
`NAME    ID    SIZE    MODIFIED`

### 4. Pull a Model (We Recommend `phi3`)

`ollama pull phi3`

> 💡 Why `phi3`?  
> - Smaller (~2.3 GB) → faster load time  
> - Excellent at following instructions  
> - Ideal for short diagnostic tasks  

You can also use `llama3`:  
`ollama pull llama3`

> ❗ No Jenkins server needed! Use **any log file** (real or mock) for testing.

## ▶️ How to Use

## 📌 Table of Contents (How to Use)
1. [Step 1: Install Python Dependencies](#step-1-install-python-dependencies)
2. [Step 2: Configure `.env` (Optional but Recommended)](#step-2-configure-env-optional-but-recommended)
3. [Step 3: Prepare a Log File](#step-3-prepare-a-log-file)
4. [Step 4: Run the Analyzer](#step-4-run-the-analyzer)
5. [Step 5: (Optional) Pipe Logs Directly](#step-5-optional-pipe-logs-directly)


### Step 1: Install Python Dependencies
`pip install -r requirements.txt`

### Step 2: Configure `.env` (Optional but Recommended)
`cp .env.example .env`

Edit `.env` to customize:
OLLAMA_HOST=http://localhost:11434
MODEL_NAME=phi3
MAX_LOG_CHARS=1200
OLLAMA_MAX_TOKENS=180
OLLAMA_KEEP_ALIVE=15m

> 🔒 **Note**: `.env` is in `.gitignore` — never committed.

### Step 3: Prepare a Log File
Create a sample log (e.g., `sample_jenkins.log`) with real or simulated errors:
```bash
npm install
npm WARN enoent ENOENT: no such file or directory, open '/workspace/package.json'
npm ERR! code ENOENT
npm ERR! syscall open
npm ERR! path /workspace/package.json
```

### Step 4: Run the Analyzer
`python jenkins_log_analyzer.py --log sample_jenkins.log`
```bash
✅ Example output:
🤖 AI Failure Analysis
🔍 Explanation: The build failed because package.json is missing in the workspace.
🛠️ Fix Steps:
  1. Verify package.json exists in your repository root
  2. Ensure your CI pipeline checks out the correct branch
⚠️ Severity: HIGH
```

### Step 5: (Optional) Pipe Logs Directly
`cat build.log | python jenkins_log_analyzer.py`

> 💡 Tip: Use this in your terminal workflow to debug builds instantly!

## ⚙️ Configuration Options (via `.env`)

| Variable | Default | Purpose |
|--------|--------|--------|
| `MODEL_NAME` | `phi3` | LLM to use (`phi3`, `llama3`, `mistral`) |
| `MAX_LOG_CHARS` | `1200` | Max log size sent to AI (smaller = faster) |
| `OLLAMA_MAX_TOKENS` | `180` | Max output tokens (shorter = faster) |
| `OLLAMA_KEEP_ALIVE` | `15m` | Keep model in memory for faster repeat runs |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama API endpoint |

## ❓ FAQ

**Q: Do I need a real Jenkins server?**  
A: **No!** Just save any CI log (Jenkins, GitHub Actions, GitLab CI) as a text file and analyze it locally.

**Q: Can I test without writing a log file?**  
A: Yes! Pipe logs directly: `your-build-command 2>&1 | python jenkins_log_analyzer.py`

**Q: Does this work offline?**  
A: **Yes!** Entirely offline after installing Ollama and `phi3`. No internet or API keys required.

## 📦 Project Structure
```text
project-02_build-failure-explainer/
├── jenkins_log_analyzer.py     # Main script
├── requirements.txt            # Python dependencies
├── .env.example                # Config template
├── README.md                   # This file
└── (optional) sample_jenkins.log  # For local testing
```
Made with ❤️ for DevOps engineers who hate debugging build logs.
