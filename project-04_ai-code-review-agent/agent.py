#!/usr/bin/env python3
import os
import sys
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain
from github_client import GitHubClient

def main():
    if len(sys.argv) < 4:
        print("Usage: python agent.py <owner> <repo> <pr_number>")
        sys.exit(1)

    owner, repo, pr_num = sys.argv[1], sys.argv[2], int(sys.argv[3])
    
    # Read diff (in real CI, you'd get this from git or GitHub API)
    with open("sample_diff.patch") as f:
        diff = f.read()

    # Set up LangChain + Ollama
    model_name = os.getenv("OLLAMA_MODEL", "phi3")
    llm = OllamaLLM(model=model_name, temperature=0.1)
    
    with open("prompts/review_prompt.txt") as f:
        template = PromptTemplate.from_template(f.read())
    
    chain = LLMChain(llm=llm, prompt=template)
    
    print("🔍 AI is reviewing your code...")
    review = chain.run(diff=diff).strip()
    
    print("\n🤖 AI Review:\n")
    print(review)
    
    # Optional: post to GitHub PR
    # client = GitHubClient()
    # client.post_pr_comment(owner, repo, pr_num, f"🤖 **AI Code Review**\n\n{review}")

if __name__ == "__main__":
    main()