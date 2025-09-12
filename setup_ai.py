#!/usr/bin/env python3
"""
Setup script for OpenRouter API integration
"""

import os
import sys

def setup_openrouter():
    print("🤖 Vim Browser AI Setup")
    print("=" * 40)
    print()
    print("To use the AI features, you need an OpenRouter API key.")
    print("1. Go to https://openrouter.ai/")
    print("2. Sign up for an account")
    print("3. Get your API key from the dashboard")
    print("4. Enter it below")
    print()
    
    api_key = input("Enter your OpenRouter API key: ").strip()
    
    if not api_key:
        print("❌ No API key provided. AI features will use fallback mode.")
        return
    
    # Set environment variable for current session
    os.environ['OPENROUTER_API_KEY'] = api_key
    
    # Create a .env file for persistence
    with open('.env', 'w') as f:
        f.write(f'OPENROUTER_API_KEY={api_key}\n')
    
    print("✅ API key saved to .env file")
    print()
    print("To use the AI features:")
    print("1. Run: export OPENROUTER_API_KEY=$(cat .env | cut -d'=' -f2)")
    print("2. Or add 'source .env' to your shell profile")
    print("3. Then run the browser: python minimal_browser.py")
    print()
    print("AI Commands in browser:")
    print("- Press Space: Native AI chat")
    print("- Examples:")
    print("  * 'navigate to github'")
    print("  * 'create a todo list'") 
    print("  * 'explain quantum physics'")
    print("  * 'make a calculator'")

if __name__ == "__main__":
    setup_openrouter()