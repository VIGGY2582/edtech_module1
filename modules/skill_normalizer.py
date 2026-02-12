# modules/skill_normalizer.py
import json
import os
from typing import List

def save_normalized_skills(skills: List[str]) -> List[str]:
    """
    Normalize and save the extracted skills.
    
    Args:
        skills: List of skill strings to normalize
        
    Returns:
        List of normalized skills
    """
    if not skills:
        return []
        
    # Simple normalization: convert to lowercase and strip whitespace
    normalized_skills = [skill.strip().lower() for skill in skills if skill.strip()]
    
    # Remove duplicates while preserving order
    seen = set()
    unique_skills = []
    for skill in normalized_skills:
        if skill not in seen:
            seen.add(skill)
            unique_skills.append(skill)
    
    # Save to file
    try:
        os.makedirs("data", exist_ok=True)
        with open("data/normalized_skills.json", "w") as f:
            json.dump({"normalized_skills": unique_skills}, f, indent=2)
        return unique_skills
    except Exception as e:
        print(f"❌ Error saving normalized skills: {e}")
        return []