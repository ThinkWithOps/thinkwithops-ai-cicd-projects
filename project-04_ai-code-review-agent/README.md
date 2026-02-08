# 🤖 Project 04: AI Code Review Agent

Your AI teammate reviews every pull request - faster than your team lead, using local LLMs (Ollama), zero cloud APIs, and no cost.

> 💡Works with GitHub Actions. Reviews code for bugs, security issues, and best practices - offline, private, and reliable.

## 🎯 What It Does

- Runs when a pull request is opened or updated
- Uses local AI (phi3 or qwen2 via Ollama) to analyze code changes
- Posts structured, actionable feedback directly as a PR comment
- If Ollama is not available (e.g., in CI), falls back to fast rule-based checks (e.g., hardcoded secrets, debug prints)

Perfect for catching issues early - without slowing down your team or leaking code to the cloud.

## 🔁 Workflow Flowchart
```mermaid
flowchart LR
    A[💻 git push] --> B[🚀 GitHub Actions]
    B --> C{🔍 Analyze PR Diff}
    C -->|✅ Local Dev| D[🧠 LangChain + Ollama<br/>(Full AI Review)]
    C -->|❌ CI Environment| E[⚡ Rule-Based Fallback<br/>(Grep Checks)]
    D --> F[💬 Post Comment to PR]
    E --> F
    F --> G[🧑‍💻 Developer sees review instantly]
    style D fill:#4CAF50,stroke:#388E3C,color:white
    style E fill:#FF9800,stroke:#E65100,color:white
    style F fill:#26A69A,stroke:#00796B,color:white
```
## 🛠️ Prerequisites

### 1. Install Ollama (Windows)
- Go to https://ollama.com/download
- Download and install the Windows version
- After install, Ollama runs automatically in the background (check system tray)

> 🔍 Ollama install location (Windows):
>C:\Users\<YOUR_USERNAME>\AppData\Local\Programs\Ollama\

### 2. Add Ollama to Windows PATH (Critical for CLI access)*

> ⚠️ Skip this if `ollama --version` already works in Git Bash/PowerShell.

#### Steps:
1. Press Win + R -> type `sysdm.cpl` -> Enter
2. Go to Advanced tab -> Click Environment Variables
3. Under System Variables, find Path -> Click Edit
4. Click New -> Add:
   `C:\Users\<YOUR_USERNAME>\AppData\Local\Programs\Ollama`
5. Click OK -> restart your terminal

### 3. Verify Ollama Installation

Open **Git Bash**, **PowerShell**, or **CMD** and run:

`ollama --version`

✅ Expected output:  
`ollama version 0.1.x`

Then check if Ollama is running:  
`ollama list`

✅ You should see:  
`NAME    ID    SIZE    MODIFIED`

### 4. Pull a Model (We Recommend phi3 or qwen2)

`ollama pull phi3`


`ollama pull phi3`

> 💡 Why phi3?  
> - Smaller (~2.3 GB) → faster load time  
> - Excellent at following instructions  
> - Ideal for short diagnostic tasks  

You can also use `llama3`:  
`ollama pull llama3`


### 5. Create a GitHub Personal Access Token (PAT)

Required to post comments on pull requests.

1. Go to https://github.com/settings/tokens
2. Click Generate new token -> Classic
3. Name it: `AI-Code-Reviewer`
4. Select scope: `repo` (full control of private/public repos)
5. Click Generate token
6. Copy the token (`ghp_...`)

> 🔒 Do not use the default `${{ secrets.GITHUB_TOKEN }}` if your setup needs broader PR comment permissions.

### 6. Store Token in Repository Secrets

1. Go to your GitHub repo -> Settings -> Secrets and variables -> Actions
2. Click New repository secret
3. Name: `CUSTOM_GITHUB_TOKEN`
4. Value: paste your `ghp_...` token

## ▶️ How to Use

## Table of Contents
- [Step 1: Install Python Dependencies](#step-1-install-python-dependencies)
- [Step 2: Configure .env (Optional but Recommended)](#step-2-configure-env-optional-but-recommended)
- [Step 3: Test Locally](#step-3-test-locally)
- [Step 4: Use in GitHub Actions](#step-4-use-in-github-actions)

### Step 1: Install Python Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Configure .env (Optional but Recommended)

```bash
cp .env.example .env
```

Edit `.env`:

```env
GITHUB_TOKEN=your_github_token_here
OLLAMA_HOST=http://localhost:11434
MODEL_NAME=phi3
```

Note: `.env` is in `.gitignore` - never committed.

### Step 3: Test Locally

```bash
python review_agent.py
```

You will see AI-generated feedback in your terminal.
If Ollama is running, it uses full LangChain + phi3/qwen2.

### Step 4: Use in GitHub Actions

1. Ensure you have added `CUSTOM_GITHUB_TOKEN` as a repo secret (see Step 6 above)
2. Your workflow (`.github/workflows/project-04-pr-review.yml`) auto-triggers on PR events
3. On PR open/update, it runs rule-based checks and posts a comment

In CI, no Ollama AI runs - only fast, safe fallback checks. In local dev, you can run full AI.

## Configuration Options (via .env)

| Variable | Default | Purpose |
|---|---|---|
| OLLAMA_MODEL | phi3 | LLM to use (phi3, qwen2, llama3) |
| OLLAMA_HOST | http://localhost:11434 | Ollama API endpoint |
| CUSTOM_GITHUB_TOKEN | (required) | GitHub PAT with repo scope |

## ❓FAQ

Q: Do I need OpenAI, Anthropic, or cloud APIs?  
A: No. This uses local Ollama models.

Q: Can I test without opening a real PR?  
A: Yes. Run `review_agent.py` locally with a sample diff file.

Q: Why does it not use AI in GitHub Actions?  
A: GitHub runners do not have Ollama running by default. So CI uses a reliable fallback.

Q: Which models work best?  
A: `phi3` (fast) or `qwen2` (strong reasoning).

## 📦 Project Structure

```text
project-04_ai-code-review-agent/
├── agent.py                 # Main LangChain + Ollama logic
├── github_client.py         # Posts comments to PR
├── prompts/
│   └── review_prompt.txt    # System prompt for AI
├── requirements.txt         # Python deps
├── .env.example             # Config template
├── sample_diff.patch        # For local testing
└── README.md                # This file
```

Note: The GitHub Actions workflow lives at `.github/workflows/project-04-pr-review.yml` in your repo root.

Made with ❤️ for DevOps engineers who want smarter, quieter, and more human code reviews.
