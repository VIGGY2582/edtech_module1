"""
Module 3: Test Generator for SkillScope
Generates skill tests using Ollama AI model (phi3:mini).
"""
from typing import List
import random
import os
import json

def load_normalized_skills() -> List[str]:
    """Load skills from normalized_skills.json file."""
    try:
        filepath = os.path.join("data", "normalized_skills.json")
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                skills = data.get("normalized_skills", [])
                print(f"[INFO] Loaded {len(skills)} skills from {filepath}")
                return skills
        else:
            print(f"[WARNING] File not found: {filepath}")
            return []
    except Exception as e:
        print(f"[ERROR] Error loading normalized skills: {e}")
        return []


def generate_test(skills: List[str] = None, domain: str = "Professional Skills") -> str:
    """
    Generate a skill test based on skills from normalized_skills.json.
    
    Args:
        skills: Optional list of skills (will load from file if not provided)
        domain: Domain/industry context for the test
    """
    # Load skills from file if not provided
    if not skills:
        skills = load_normalized_skills()
    
    if not skills:
        return "❌ Error: No skills found. Please extract skills first."
    
    try:
        import requests
    except ImportError:
        return "❌ Error: requests library not installed. Run: pip install requests"
    
    try:
        questions = []
        question_number = 1
        
        print(f"\n[INFO] Generating ONE question per skill for {len(skills)} skills using Ollama phi3:mini...")
        
        # Generate exactly ONE question per skill
        for skill in skills:
            print(f"[INFO] Generating question for skill: {skill}")
            
            question = generate_question_with_ollama(question_number, skill, domain)
            if question:
                questions.append(question)
                question_number += 1
            else:
                print(f"[WARNING] Failed to generate question for {skill}")
        
        if not questions:
            return "❌ Error: Failed to generate any questions. Make sure Ollama is running."
        
        print(f"[INFO] Successfully generated {len(questions)} questions")
        return "\n".join(questions)
        
    except Exception as e:
        return f"❌ Error generating test: {str(e)}"


def generate_question_with_ollama(number: int, skill: str, domain: str) -> str:
    """Generate a single question using Ollama API."""
    try:
        import requests
        
        # Ollama API endpoint
        url = "http://localhost:11434/api/generate"
        
        # Create prompt for generating a question
        prompt = f"""Generate ONE multiple-choice question to test knowledge of {skill} in {domain}.

Requirements:
1. Create ONE technical question about {skill}
2. Provide exactly 4 answer options (a, b, c, d)
3. Mark the correct answer clearly
4. Make it challenging and specific to {skill}
5. Focus on practical knowledge, not just definitions
6. Ensure the question tests real understanding of {skill}

Format your response EXACTLY like this:
Question: [Your question here]
a) [Option A]
b) [Option B]
c) [Option C]
d) [Option D]
Correct Answer: [letter]

Generate the question now:"""

        payload = {
            "model": "phi3:mini",
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "max_tokens": 500
            }
        }
        
        # Make request to Ollama
        print(f"[DEBUG] Requesting Ollama for question {number} ({skill})...")
        response = requests.post(url, json=payload, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            generated_text = result.get("response", "").strip()
            
            print(f"[DEBUG] Ollama response received for question {number}")
            
            # Format the question with number
            formatted_question = format_ollama_response(number, generated_text)
            return formatted_question
        else:
            print(f"[ERROR] Ollama API error: {response.status_code}")
            # Fallback to template-based question
            return generate_fallback_question(number, skill)
            
    except requests.exceptions.ConnectionError:
        print("[ERROR] Cannot connect to Ollama. Make sure Ollama is running (ollama serve)")
        return generate_fallback_question(number, skill)
    except requests.exceptions.Timeout:
        print(f"[ERROR] Ollama request timeout for question {number}")
        return generate_fallback_question(number, skill)
    except Exception as e:
        print(f"[ERROR] Error in generate_question_with_ollama: {str(e)}")
        return generate_fallback_question(number, skill)


def format_ollama_response(number: int, response_text: str) -> str:
    """Format the Ollama response to match expected format."""
    try:
        lines = response_text.strip().split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if line.startswith("Question:"):
                formatted_lines.append(f"Question {number}: {line.replace('Question:', '').strip()}")
            elif line and (line[0].lower() in 'abcd' and len(line) > 1 and line[1] in '):'):
                formatted_lines.append(line)
            elif line.lower().startswith("correct answer:"):
                formatted_lines.append(line)
        
        if formatted_lines:
            formatted_lines.append("")  # Add blank line after question
            return "\n".join(formatted_lines)
        else:
            return response_text  # Return as-is if formatting fails
            
    except Exception as e:
        print(f"[WARNING] Error formatting response: {e}")
        return response_text


def generate_fallback_question(number: int, skill: str) -> str:
    """Generate a fallback question when Ollama is unavailable."""
    question_types = [
        {
            "question": f"What is a primary use case for {skill.upper()} in modern software development?",
            "options": [
                f"Building scalable applications with {skill}",
                f"Managing version control for {skill} projects",
                f"Debugging {skill} code efficiently",
                f"Deploying {skill} applications to production"
            ],
            "correct": 0
        },
        {
            "question": f"Which of the following best describes {skill.upper()}?",
            "options": [
                f"A programming language for web development",
                f"A framework for building applications",
                f"A tool for version control",
                f"A database management system"
            ],
            "correct": 0
        },
        {
            "question": f"What is the main advantage of using {skill.upper()}?",
            "options": [
                f"Improved code readability and maintainability",
                f"Better performance and optimization",
                f"Enhanced security features",
                f"Simplified deployment process"
            ],
            "correct": 0
        }
    ]
    
    q_template = random.choice(question_types)
    
    # Shuffle options but track correct answer
    correct_answer = q_template["options"][q_template["correct"]]
    random.shuffle(q_template["options"])
    correct_letter = "abcd"[q_template["options"].index(correct_answer)]
    
    # Format question
    question_text = [f"Question {number}: {q_template['question']}"]
    for i, option in enumerate(q_template["options"]):
        question_text.append(f"{'abcd'[i]}) {option}")
    question_text.append(f"Correct Answer: {correct_letter}\n")
    
    return "\n".join(question_text)


def check_ollama_status() -> bool:
    """Check if Ollama is running and phi3:mini model is available."""
    try:
        import requests
        
        # Check if Ollama is running
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        
        if response.status_code == 200:
            models = response.json().get("models", [])
            model_names = [m.get("name", "") for m in models]
            
            if any("phi3:mini" in name for name in model_names):
                print("[INFO] ✅ Ollama is running and phi3:mini model is available")
                return True
            else:
                print("[WARNING] ⚠️ Ollama is running but phi3:mini model not found")
                print("[INFO] Run: ollama pull phi3:mini")
                return False
        else:
            print("[WARNING] ⚠️ Ollama is not responding properly")
            return False
            
    except requests.exceptions.ConnectionError:
        print("[WARNING] ⚠️ Cannot connect to Ollama")
        print("[INFO] Make sure Ollama is running: ollama serve")
        return False
    except Exception as e:
        print(f"[ERROR] Error checking Ollama status: {e}")
        return False


def save_test_to_file(test_content: str, filename: str = "skill_test.txt") -> None:
    """Save the generated test to a file."""
    try:
        os.makedirs("data", exist_ok=True)
        filepath = os.path.join("data", filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(test_content)
        print(f"✅ Test saved to {filepath}")
    except Exception as e:
        print(f"❌ Error saving test: {e}")


if __name__ == "__main__":
    print("="*50)
    print("🚀 Starting SkillScope Test Generator with Ollama")
    print("="*50)
    
    # Check Ollama status
    print("\n🔍 Checking Ollama status...")
    ollama_available = check_ollama_status()
    
    if not ollama_available:
        print("\n⚠️ Ollama is not available. Tests will use fallback templates.")
        print("\nTo use AI-generated questions:")
        print("1. Install Ollama: https://ollama.ai")
        print("2. Run: ollama serve")
        print("3. Run: ollama pull phi3:mini")
    
    # Load skills from normalized_skills.json
    print("\n📂 Loading skills from normalized_skills.json...")
    skills = load_normalized_skills()
    
    if not skills:
        print("\n⚠️ No skills found. Using sample skills for demonstration.")
        skills = ["Python", "JavaScript", "SQL", "Git", "Docker"]
    
    domain = "Professional Skills"
    
    print(f"\n🔧 Generating ONE question for each of {len(skills)} skills...")
    test = generate_test(skills, domain)
    
    if test.startswith("❌"):
        print(f"\n❌ Error: {test}")
    else:
        print("\n📝 Generated Test:")
        print("-"*50)
        print(test)
        print("-"*50)
        
        # Save the test
        save_test_to_file(test)
        print("\n✨ Test generation complete!")