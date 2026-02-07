#!/usr/bin/env python3
"""
Slack Pipeline Reporter
Sends a human-friendly summary of CI pipeline status to Slack.
Uses local AI (Ollama) to generate message — no GPT-4, no cost.

Usage in CI:
  python report_to_slack.py --status success --job "build" --log "Build passed"
  python report_to_slack.py --status failure --job "test" --log "$(cat test.log)"
"""

import os
import argparse
import requests
import json
import sys


def extract_error_line(log_text: str) -> str:
    """Pick a concise error line from a log snippet."""
    candidates = []
    for line in log_text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        lower = stripped.lower()
        if any(token in lower for token in ["error", "exception", "failed", "fail", "fatal"]):
            candidates.append(stripped)
    if candidates:
        return candidates[0]
    # Fallback to last non-empty line
    for line in reversed(log_text.splitlines()):
        stripped = line.strip()
        if stripped:
            return stripped
    return ""

def call_ollama(prompt: str, model: str = "phi3", host: str = "http://localhost:11434") -> str:
    try:
        resp = requests.post(
            f"{host.rstrip('/')}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.3, "num_predict": 100}
            },
            timeout=30
        )
        return resp.json().get("response", "").strip()
    except Exception as e:
        return f"AI summary failed: {str(e)}"

def send_to_slack(webhook_url: str, message: str):
    payload = {"text": message}
    try:
        resp = requests.post(webhook_url, json=payload, timeout=10)
        if resp.status_code != 200:
            print(f"❌ Slack send failed: {resp.text}", file=sys.stderr)
            return False
        return True
    except Exception as e:
        print(f"❌ Slack error: {e}", file=sys.stderr)
        return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--status", required=True, choices=["success", "failure"])
    parser.add_argument("--job", required=True, help="Job name (e.g., build, test)")
    parser.add_argument("--log", required=True, help="Log snippet or message")
    parser.add_argument("--webhook-url", required=True, help="Slack webhook URL")
    args = parser.parse_args()

    # Truncate log for AI
    log_snippet = (args.log[:800] + "...") if len(args.log) > 800 else args.log
    error_line = extract_error_line(args.log) if args.status == "failure" else ""

    if args.status == "success":
        ai_prompt = f"Summarize this successful CI job in one friendly sentence for a team Slack channel:\nJob: {args.job}\nLog: {log_snippet}"
    else:
        ai_prompt = f"Explain this CI failure briefly for a Slack alert. Be helpful, not alarming:\nJob: {args.job}\nError: {log_snippet}"

    # Generate AI message (fallback if Ollama fails)
    ai_message = call_ollama(ai_prompt)
    if "AI summary failed" in ai_message:
        if args.status == "success":
            ai_message = f"✅ Job `{args.job}` completed successfully."
        else:
            ai_message = f"⚠️ Job `{args.job}` failed. Check logs for details."

    if args.status == "failure" and error_line:
        ai_message = f"{ai_message}\nError: {error_line}"

    # Add emoji and formatting
    workflow_name = os.getenv("GITHUB_WORKFLOW", "").strip()
    workflow_prefix = "🤖 " if workflow_name else ""
    workflow_line = f"{workflow_prefix}{workflow_name}\n" if workflow_name else ""
    if args.status == "success":
        slack_msg = f"🟢 *CI Pipeline Update*\n{workflow_line}{ai_message}"
    else:
        slack_msg = f"🔴 *CI Pipeline Alert*\n{workflow_line}{ai_message}"

    # Send to Slack
    if send_to_slack(args.webhook_url, slack_msg):
        print("✅ Message sent to Slack")
    else:
        print("❌ Failed to send to Slack", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
