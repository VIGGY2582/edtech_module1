# modules/domain_suggester.py
import json
import subprocess
from typing import List, Dict, Any
from pathlib import Path

def load_evaluation_results() -> Dict[str, Any]:
    """Load evaluation results from JSON file."""
    try:
        with open("data/evaluation_result.json", "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading evaluation results: {e}")
        return {}

def generate_domain_suggestions(model: str = "gemma3:1b") -> List[str]:
    """
    Generate domain suggestions using Ollama.
    Returns a list of 2-3 suggested domains.
    """
    eval_data = load_evaluation_results()
    if not eval_data:
        return ["General IT", "Software Development", "IT Operations"]
    
    prompt = f"""Based on the following skill assessment results, suggest 2-3 most suitable IT career domains.
Only return the domain names, one per line. No numbering or extra text.

Assessment:
- Level: {eval_data.get('level', 'Beginner')}
- Strengths: {', '.join(eval_data.get('strengths', []))}
- Weak Areas: {', '.join(eval_data.get('weak_areas', []))}
- Score: {eval_data.get('score', 0)}/{eval_data.get('total_questions', 10)}

Suggested domains:"""
    
    try:
        result = subprocess.run(
            ["ollama", "run", model, prompt],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            domains = [
                line.strip() 
                for line in result.stdout.split('\n') 
                if line.strip()
            ]
            domains = domains[:3]
            while len(domains) < 2:
                domains.append("General IT")
            return domains[:3]
    except Exception as e:
        print(f"Error generating domain suggestions: {e}")
    
    return ["General IT", "Software Development", "IT Operations"]

def save_domain_suggestions(domains: List[str]) -> None:
    """Save domain suggestions to JSON file."""
    try:
        data = {"suggested_domains": domains}
        with open("data/domain_suggestions.json", "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error saving domain suggestions: {e}")

def get_domain_suggestions() -> List[str]:
    """Get domain suggestions, generating them if needed."""
    try:
        with open("data/domain_suggestions.json", "r") as f:
            data = json.load(f)
            if "suggested_domains" in data:
                return data["suggested_domains"]
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    
    domains = generate_domain_suggestions()
    save_domain_suggestions(domains)
    return domains