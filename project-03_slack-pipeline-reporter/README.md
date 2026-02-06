# 🤖 Project 3: Slack Pipeline Reporter

Your CI pipeline talks to you on Slack like a teammate — using local AI (Ollama), zero cloud APIs, and no cost.

> 💡 Works with GitHub Actions, GitLab CI, or any pipeline. Sends human-friendly build updates to Slack — offline and private.

## 🎯 What It Does

- Runs after your CI job (success or failure)
- Uses local AI (phi3) to generate a friendly, concise message
- Sends it to Slack via Incoming Webhook
- If Ollama isn’t available (e.g., in CI), falls back to a clear plain-text message

Perfect for getting instant, readable pipeline updates — without noise or cost.

## 🛠️ Prerequisites

### 1. Install Ollama (Windows)
1. Go to https://ollama.com/download  
2. Download and install the Windows version  
3. After install, Ollama runs automatically in the background (check system tray)

> 🔍 Ollama Install Location (Windows):  
> C:\Users\<YOUR_USERNAME>\AppData\Local\Programs\Ollama\

### 2. Add Ollama to Windows PATH *(Critical for CLI access)*

> ⚠️ Skip this if ollama --version already works in Git Bash/PowerShell.

#### Steps:
1. Press Win + R → type sysdm.cpl → Enter  
2. Go to Advanced tab → Click Environment Variables  
3. Under System Variables, find Path → Click Edit  
4. Click New → Add:  
   C:\Users\<YOUR_USERNAME>\AppData\Local\Programs\Ollama  
5. Click OK → restart your terminal  

### 3. Verify Ollama Installation

Open Git Bash, PowerShell, or CMD and run:

ollama --version

✅ Expected output:  
ollama version 0.1.x

Then check if Ollama is running:  
ollama list

✅ You should see:  
NAME    ID    SIZE    MODIFIED

### 4. Pull a Model (We Recommend phi3)

ollama pull phi3

> 💡 Why phi3?  
> - Smaller (~2.3 GB) → faster load time  
> - Excellent at following instructions  
> - Ideal for short diagnostic tasks  

You can also use llama3:  
ollama pull llama3

### 5. Create a Slack Incoming Webhook

1. Go to https://api.slack.com/apps → Create New App → From scratch  
2. Name it (e.g., Pipeline Reporter) → pick your workspace  
3. Go to Incoming Webhooks → Activate  
4. Click Add New Webhook → choose channel (e.g., #ci-alerts)  
5. Copy the Webhook URL (starts with https://hooks.slack.com/services/...)

> 🔒 You’ll store this securely in GitHub Secrets (for CI) or .env (for local testing)

## ▶️ How to Use

### Step 1: Install Python Dependencies
pip install -r requirements.txt

### Step 2: Configure .env (Optional but Recommended)
`cp .env.example .env`

Edit `.env` to customize:
```
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
OLLAMA_HOST=http://localhost:11434
MODEL_NAME=phi3
```

> 🔒 Note: .env is in .gitignore — never committed.

### Step 3: Test Locally
python report_to_slack.py --status success --job "build" --log "All tests passed!" --webhook-url "$(grep SLACK_WEBHOOK_URL .env | cut -d'=' -f2)"

Or simulate a failure:
python report_to_slack.py --status failure --job "test" --log "npm ERR! Missing package.json" --webhook-url "$(grep SLACK_WEBHOOK_URL .env | cut -d'=' -f2)"

### Step 4: Use in GitHub Actions
1. Go to your repo → Settings → Secrets and variables → Actions  
2. Add new repository secret:  
   - Name: SLACK_WEBHOOK_URL  
   - Value: Your webhook URL  
3. In your workflow file (.github/workflows/ci.yml), add steps that call the script with --status, --job, --log, and --webhook-url using the secret

> 💡 In CI environments (like GitHub Actions), Ollama won’t be running, so the script automatically uses a plain-text fallback message — no AI, but still useful and reliable.

## ⚙️ Configuration Options (via .env)

| Variable | Default | Purpose |
|--------|--------|--------|
| MODEL_NAME | phi3 | LLM to use (phi3, llama3, mistral) |
| OLLAMA_HOST | http://localhost:11434 | Ollama API endpoint |
| SLACK_WEBHOOK_URL | (required at runtime) | Slack incoming webhook URL |

## ❓ FAQ

**Q: Do I need GPT-4 or OpenAI API?**  
A: No! This uses only local Ollama models — 100% free, offline, and private.

**Q: Can I test without a real CI pipeline?**  
A: Yes! Just run the script locally with sample log text and your Slack webhook.

**Q: Does this work in GitHub Actions?**  
A: Yes — it uses a fallback message when Ollama isn’t available (which is normal in CI). You only need to provide the Slack webhook via secrets.

## 📦 Project Structure
project-03_slack-pipeline-reporter/
├── report_to_slack.py     # Main script
├── requirements.txt      # Python dependencies
├── .env.example          # Config template
└── README.md             # This file

Note: The GitHub Actions workflow file lives at .github/workflows/ci.yml in the root of your repository.

Made with ❤️ for DevOps engineers who want smarter, quieter, and more human CI pipelines.