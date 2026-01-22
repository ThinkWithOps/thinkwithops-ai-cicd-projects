#!/usr/bin/env python3
"""
AI Commit & Changelog Generator (Local Version)
Uses Ollama (llama3, codellama, etc.) to generate:
- A conventional commit message (<72 chars)
- A user-friendly changelog snippet (2-3 bullet points)

Designed to run locally where Ollama is installed and running.
"""

import os
import sys
import subprocess
import requests
import json
from datetime import date
from typing import Optional, Tuple

# Configuration
MAX_DIFF_CHARS = 2000
DEFAULT_OLLAMA_HOST = "http://localhost:11434"
DEFAULT_MODEL_NAME = "llama3"


def get_git_diff() -> Tuple[Optional[str], Optional[str]]:
    """Get diff of the last commit (HEAD vs HEAD~1) using UTF-8 encoding."""
    try:
        # Force UTF-8 to handle emojis, special chars, etc.
        result = subprocess.run(
            ["git", "diff", "HEAD~1", "HEAD"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
            encoding='utf-8',          # Critical: force UTF-8
            errors='replace'           # Replace undecodable chars instead of crashing
        )
    except FileNotFoundError:
        return None, "❌ Git not found. Is Git installed and in PATH?"
    except Exception as e:
        return None, f"❌ Failed to run git: {e}"

    if result.returncode != 0:
        err = result.stderr.strip().lower()
        if "not a git repository" in err:
            return None, "❌ Not a Git repository."
        if "unknown revision" in err or "bad revision" in err:
            return None, "❌ Need at least one prior commit (push after first commit)."
        return None, f"❌ Git error: {result.stderr.strip()}"

    diff = result.stdout.strip()
    if not diff:
        return None, "ℹ️ No changes detected in the last commit."

    return diff[:MAX_DIFF_CHARS], None


def build_prompt(diff: str) -> str:
    return f"""You are a senior DevOps engineer. Analyze the following git diff and respond EXACTLY in this format:

COMMIT_MESSAGE:
<one line, max 72 chars, conventional style>

CHANGELOG:
- Bullet point 1
- Bullet point 2

Do not add any other text.

Git diff:
{diff}"""


def call_ollama(prompt: str, host: str, model: str) -> Tuple[Optional[str], Optional[str]]:
    """Call Ollama's /api/chat endpoint."""
    url = f"{host.rstrip('/')}/api/chat"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {"temperature": 0.3}
    }

    try:
        resp = requests.post(url, json=payload, timeout=120)
    except requests.RequestException as e:
        return None, f"❌ Failed to connect to Ollama at {url}: {e}"

    if resp.status_code != 200:
        return None, f"❌ Ollama error ({resp.status_code}): {resp.text[:200]}"

    try:
        content = resp.json()["message"]["content"]
        return content.strip(), None
    except (KeyError, json.JSONDecodeError):
        return None, "❌ Unexpected response format from Ollama."


def parse_ai_response(response: str) -> Tuple[str, str]:
    """Extract commit message and changelog from AI output."""
    commit_msg = "chore: update changes"
    changelog_lines = ["- Minor updates."]

    lines = response.splitlines()
    state = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if line.upper().startswith("COMMIT_MESSAGE"):
            state = "commit"
            continue
        elif line.upper().startswith("CHANGELOG"):
            state = "changelog"
            continue

        if state == "commit" and commit_msg == "chore: update changes":
            commit_msg = line[:72]  # enforce length
        elif state == "changelog":
            if line.startswith("- "):
                changelog_lines.append(line)

    # Remove default if real content found
    if len(changelog_lines) > 1:
        changelog_lines = changelog_lines[1:]

    changelog = "\n".join(changelog_lines)
    return commit_msg, changelog


def main():
    print("🔍 Analyzing your latest commit with AI...\n")

    diff, error = get_git_diff()
    if error:
        print(error)
        if "Need at least one prior commit" in error:
            print("\n💡 Tip: Make your first commit, then run this after the second.")
        sys.exit(1 if "❌" in error else 0)

    # Load config
    ollama_host = os.getenv("OLLAMA_HOST", DEFAULT_OLLAMA_HOST)
    model_name = os.getenv("MODEL_NAME", DEFAULT_MODEL_NAME)

    print(f"🧠 Using model: {model_name} @ {ollama_host}")
    print("⏳ This may take 10-30 seconds (first run loads model)...\n")

    prompt = build_prompt(diff)
    response, error = call_ollama(prompt, ollama_host, model_name)
    if error:
        print(error)
        sys.exit(1)

    commit_msg, changelog = parse_ai_response(response)

    # Output
    print("=" * 60)
    print("✅ AI-Generated Commit Message:")
    print(f"\033[1m{commit_msg}\033[0m\n")
    print("📝 Changelog Snippet:")
    print(f"### Unreleased (v1.0) — {date.today().isoformat()}")
    print(changelog)
    print("=" * 60)
    print("\n💡 Copy the commit message above and use:\n")
    print(f'git commit --amend -m "{commit_msg}"')
    print("# or for new commit:")
    print(f'git commit -m "{commit_msg}"')


if __name__ == "__main__":
    main()