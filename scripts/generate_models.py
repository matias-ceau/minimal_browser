#!/usr/bin/env python3
"""Generate models.json using LLM with web search for up-to-date OpenRouter models."""

import json
import sys
from datetime import datetime
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from minimal_browser.ai.auth import auth_manager
from minimal_browser.ai.models import get_model, DEFAULT_MODEL
from minimal_browser.ai.client import AIClient


def fetch_openrouter_models():
    """Fetch available models from OpenRouter API."""
    try:
        response = requests.get("https://openrouter.ai/api/v1/models", timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Warning: Could not fetch OpenRouter models API: {e}")
        return {}


def generate_models_with_llm(openrouter_data, output_path):
    """Use LLM to generate models.json."""
    model_name = DEFAULT_MODEL
    print(f"Using model: {model_name} for generation")
    
    models_context = ""
    if openrouter_data and "data" in openrouter_data:
        models_list = sorted(openrouter_data["data"], key=lambda x: x.get("id", ""))[:100]
        simplified = [{"id": m.get("id"), "name": m.get("name"), "context_length": m.get("context_length", 0), "pricing": m.get("pricing", {})} for m in models_list]
        models_context = json.dumps(simplified, indent=2)
    
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    system_prompt = f"""You are an AI model researcher. Generate a JSON file with the top 10-20 AI models on OpenRouter as of {current_date}.

Use web search to find:
- Current best performing models (latest benchmarks 2024-2025)
- Latest releases (GPT-5, Claude Opus 4.5, Gemini 3, etc.)
- Current pricing
- Model specs (context windows, capabilities)

Select top 10-20 models based on: performance, popularity, cost-effectiveness, context size, utility.
Include diverse providers (OpenAI, Anthropic, Google, Meta, etc.).

For each model provide:
- name: short name (e.g., "gpt-5.2")
- provider: "openrouter" or direct provider
- max_tokens: context window (4000-8000 typical, up to 128000 for large)
- supports_streaming: true
- cost_per_token: USD per token
- model_id: full OpenRouter ID if provider is "openrouter"

Output ONLY valid JSON:
{{
  "models": {{
    "model-name": {{
      "name": "model-name",
      "provider": "openrouter",
      "max_tokens": 8000,
      "supports_streaming": true,
      "cost_per_token": 0.000006,
      "model_id": "provider/model-name"
    }}
  }},
  "default_model": "best-model",
  "fallback_model": "second-best",
  "generated_date": "{current_date}",
  "generated_by": "{model_name}"
}}"""

    user_query = f"""Research and generate JSON with top 10-20 OpenRouter models as of {current_date}.

OpenRouter API data:
{models_context[:3000] if models_context else "No API data - use web search"}

Use web search for latest info on best models, releases, pricing, specs.
Output ONLY JSON, no markdown."""

    try:
        client = AIClient(system_prompt=system_prompt, model_name=model_name)
        messages = [{"role": "user", "content": user_query}]
        
        print("Generating models list...")
        response_text = ""
        for chunk in client.get_streaming_response(messages):
            response_text += chunk
            print(chunk, end="", flush=True)
        print("\n")
        
        json_start = response_text.find("{")
        json_end = response_text.rfind("}") + 1
        
        if json_start >= 0 and json_end > json_start:
            json_text = response_text[json_start:json_end]
            try:
                models_data = json.loads(json_text)
                if "models" in models_data:
                    if "default_model" not in models_data:
                        models_data["default_model"] = list(models_data["models"].keys())[0] if models_data["models"] else "gpt-5.2"
                    if "fallback_model" not in models_data:
                        keys = list(models_data["models"].keys())
                        models_data["fallback_model"] = keys[1] if len(keys) > 1 else keys[0]
                    models_data["generated_date"] = current_date
                    models_data["generated_by"] = model_name
                    
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(output_path, "w") as f:
                        json.dump(models_data, f, indent=2)
                    print(f"\n✓ Generated {output_path} with {len(models_data['models'])} models")
                    return
            except json.JSONDecodeError as e:
                print(f"\nError parsing JSON: {e}")
        
        print("\nWarning: Could not parse response. Creating fallback...")
        create_fallback_models(output_path, current_date)
    except Exception as e:
        print(f"\nError: {e}")
        create_fallback_models(output_path, current_date)


def create_fallback_models(output_path, current_date):
    """Create fallback models.json."""
    from minimal_browser.ai.models import MODELS, DEFAULT_MODEL, FALLBACK_MODEL
    
    models_dict = {}
    for key, model in MODELS.items():
        model_dict = {
            "name": model.name,
            "provider": model.provider,
            "max_tokens": model.max_tokens,
            "supports_streaming": model.supports_streaming,
            "cost_per_token": model.cost_per_token,
        }
        if model.model_id:
            model_dict["model_id"] = model.model_id
        models_dict[key] = model_dict
    
    output_data = {
        "models": models_dict,
        "default_model": DEFAULT_MODEL,
        "fallback_model": FALLBACK_MODEL,
        "generated_date": current_date,
        "generated_by": "fallback",
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(output_data, f, indent=2)
    print(f"✓ Created fallback {output_path}")


def main():
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    models_json_path = project_root / "src" / "minimal_browser" / "ai" / "models.json"
    
    print("Generating models.json...")
    print(f"Output: {models_json_path}")
    
    print("\nFetching OpenRouter API...")
    openrouter_data = fetch_openrouter_models()
    if openrouter_data and "data" in openrouter_data:
        print(f"  ✓ Fetched {len(openrouter_data['data'])} models")
    
    print("\nGenerating with LLM...")
    generate_models_with_llm(openrouter_data, models_json_path)
    print("\nDone!")


if __name__ == "__main__":
    main()
