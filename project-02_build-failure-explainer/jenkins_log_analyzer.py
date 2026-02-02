#!/usr/bin/env python3
"""
Build-Failure Explainer Bot
Reads Jenkins (or any CI) logs and explains failures using local AI (Ollama).
Zero cost — runs offline with phi3/llama3.

Usage:
  python jenkins_log_analyzer.py --log sample_jenkins.log
  # or pipe logs:
  cat sample_jenkins.log | python jenkins_log_analyzer.py
"""

import os
import sys
import argparse
import requests
from typing import Optional, Tuple
from dotenv import load_dotenv

load_dotenv()

# Config
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
MODEL_NAME = os.getenv("MODEL_NAME", "phi3")
MAX_LOG_CHARS = int(os.getenv("MAX_LOG_CHARS", "1200"))
MAX_TOKENS = int(os.getenv("OLLAMA_MAX_TOKENS", "180"))

def read_log(input_source) -> str:
    """Read log from file or stdin."""
    if input_source == "-":
        return sys.stdin.read()
    try:
        with open(input_source, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"❌ Failed to read log: {e}", file=sys.stderr)
        sys.exit(1)

def call_ollama(prompt: str) -> Tuple[Optional[str], Optional[str]]:
    url = f"{OLLAMA_HOST.rstrip('/')}/api/chat"
    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {
            "temperature": 0.2,
            "num_predict": MAX_TOKENS,
            "stop": ["\n\n", "Log snippet:", "Now respond:"]
        },
        "keep_alive": os.getenv("OLLAMA_KEEP_ALIVE", "15m")
    }
    try:
        resp = requests.post(url, json=payload, timeout=60)
        if resp.status_code != 200:
            return None, f"Ollama error {resp.status_code}: {resp.text[:200]}"
        data = resp.json()
        return data["message"]["content"].strip(), None
    except Exception as e:
        return None, f"Request failed: {e}"

def build_prompt(log: str) -> str:
    return f"""You are a DevOps expert. Analyze this CI log and respond with ONLY:

1. A short explanation (1 sentence)
2. 2-3 fix steps as bullet points starting with "- "
3. One word: "high", "medium", or "low"

Do NOT write markdown, headers, or extra text.

Log snippet:
{log}

Now respond:"""

def parse_response(text: str, original_log: str = "") -> dict:
    """Extract explanation, fix steps, and severity from loose AI output."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    
    # Extract explanation: take first 1-2 non-bullet, non-severity lines
    explanation_lines = []
    for line in lines:
        lower_line = line.lower()
        if (not line.startswith(('-', '*', '•', 'FIX', 'SEVERITY', 'EXPLANATION')) and
            'high' not in lower_line and 'medium' not in lower_line and 'low' not in lower_line):
            explanation_lines.append(line)
            if len(explanation_lines) >= 2:
                break
    explanation = " ".join(explanation_lines).strip()

    # Extract fix steps: look for bullet points, skip severity words
    fix_steps = []
    for line in lines:
        if line.startswith(('-', '*', '•')):
            content = line[1:].strip()
            # Skip if it's just a severity word
            if content.lower() in ('high', 'medium', 'low'):
                continue
            fix_steps.append(content)

    # If no bullets, scan for fix-related lines
    if not fix_steps:
        in_fix = False
        for line in lines:
            lower_line = line.lower()
            if any(keyword in lower_line for keyword in ['fix', 'step', 'solution', 'resolve']):
                in_fix = True
                continue
            if in_fix and line.strip():
                # Skip severity words
                if line.strip().lower() in ('high', 'medium', 'low'):
                    continue
                fix_steps.append(line.strip())
                if len(fix_steps) >= 3:
                    break

    # Extract severity from AI response AND original log
    combined_text = (text + " " + original_log).lower()
    severity = "medium"
    if any(word in combined_text for word in ['high', 'critical', 'fail', 'error', 'exception', 'err', 'fatal']):
        severity = "high"
    elif any(word in combined_text for word in ['low', 'warning', 'warn', 'note', 'info']):
        severity = "low"

    # Final cleanup: remove severity words from fix steps
    fix_steps = [
        step for step in fix_steps 
        if step.lower() not in ('high', 'medium', 'low')
    ]

    # Fallbacks
    if not explanation or "could not determine" in explanation.lower():
        explanation = "The build failed due to missing or misconfigured dependencies. Check for missing files like package.json or requirements.txt."
    if not fix_steps:
        fix_steps = [
            "Verify all required project files (e.g., package.json, Dockerfile) are present in the repository.",
            "Ensure your CI pipeline checks out the correct branch and submodules.",
            "Review the full log for specific error messages near the end of the build."
        ]

    return {
        "explanation": explanation[:300],  # Cap length
        "fix": fix_steps[:3],
        "severity": severity
    }

def main():
    parser = argparse.ArgumentParser(description="Explain Jenkins build failures using AI")
    parser.add_argument("--log", "-l", help="Log file path (or '-' for stdin)", default="-")
    parser.add_argument("--debug", action="store_true", help="Show raw AI response")
    args = parser.parse_args()

    log = read_log(args.log)
    if len(log) > MAX_LOG_CHARS:
        log = log[:MAX_LOG_CHARS] + "\n... (truncated)"

    print("🔍 Analyzing build log with AI...\n")
    prompt = build_prompt(log)
    resp, err = call_ollama(prompt)
    if err:
        print(f"❌ {err}")
        sys.exit(1)

    if args.debug:
        print("🔧 DEBUG: Raw AI Response:\n", resp, "\n")

    result = parse_response(resp, log)

    print("=" * 60)
    print("🤖 AI Failure Analysis")
    print(f"🔍 Explanation: {result['explanation']}")
    print("\n🛠️ Fix Steps:")
    for i, step in enumerate(result["fix"], 1):
        print(f"  {i}. {step}")
    print(f"\n⚠️ Severity: {result['severity'].upper()}")
    print("=" * 60)

if __name__ == "__main__":
    main()
