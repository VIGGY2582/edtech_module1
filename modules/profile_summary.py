import json
import os
from pathlib import Path

def load_user_skills():
    """Load skills from user_skills.json"""
    skills_file = Path("data/user_skills.json")
    if not skills_file.exists():
        return []
    
    with open(skills_file, "r") as f:
        data = json.load(f)
        return data.get("raw_skills", [])

def generate_profile_summary():
    """Generate a profile summary based on user skills"""
    skills = load_user_skills()
    
    if not skills:
        return "Candidate profile is currently incomplete. Please add skills to generate a profile summary."
    
    # Simple summary generation without API
    skills_text = ", ".join(skills)
    return f"A motivated professional with skills in {skills_text}. Quick learner with strong problem-solving abilities and a passion for continuous improvement."

def save_profile_summary():
    """Save the generated profile summary to a file"""
    summary = generate_profile_summary()
    output = {"profile_summary": summary}
    
    # Ensure directory exists
    os.makedirs("data", exist_ok=True)
    
    with open("data/profile_summary.json", "w") as f:
        json.dump(output, f, indent=4)
    
    return output

if __name__ == "__main__":
    result = save_profile_summary()
    print("Profile summary generated:")
    print(json.dumps(result, indent=2))