"""
Module 3: Test Generator for SkillScope
Generates skill tests using Ollama AI model (phi3:mini).
"""
import os
import json
import random
from datetime import datetime
from typing import List, Dict, Any

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

def save_test_data(questions: List[Dict[str, Any]], test_id: str = None) -> str:
    """Save test questions to a JSON file.
    
    Args:
        questions: List of question dictionaries
        test_id: Optional test ID. If not provided, generates one.
        
    Returns:
        str: Path to the saved test file
    """
    if not questions:
        raise ValueError("No questions provided to save")
        
    test_data = {
        "test_id": test_id or f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "timestamp": datetime.now().isoformat(),
        "total_questions": len(questions),
        "questions": questions
    }
    
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    test_file = os.path.join('data', 'test.json')
    
    try:
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, indent=2, ensure_ascii=False)
        print(f"[INFO] Test data saved to {test_file}")
        return test_file
    except Exception as e:
        print(f"[ERROR] Failed to save test data: {e}")
        raise

def generate_question_with_ollama(question_number: int, skill: str, domain: str) -> Dict[str, Any]:
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
                "num_predict": 500
            }
        }
        
        # Make request to Ollama
        print(f"[DEBUG] Requesting Ollama for question {question_number} ({skill})...")
        response = requests.post(url, json=payload, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            generated_text = result.get("response", "").strip()
            
            print(f"[DEBUG] Ollama response received for question {question_number}")
            print(f"[DEBUG] Response preview: {generated_text[:200]}...")
            
            # Parse the response into structured format
            parsed_question = parse_ollama_response(generated_text, skill)
            
            if parsed_question:
                print(f"[SUCCESS] Successfully generated question for {skill}")
                return parsed_question
            else:
                print(f"[WARNING] Failed to parse Ollama response for {skill}")
                return generate_fallback_question(question_number, skill)
        else:
            print(f"[ERROR] Ollama API error: {response.status_code} - {response.text}")
            return generate_fallback_question(question_number, skill)
            
    except requests.exceptions.ConnectionError as e:
        print(f"[ERROR] Cannot connect to Ollama at localhost:11434")
        print(f"[ERROR] Make sure Ollama is running: ollama serve")
        return generate_fallback_question(question_number, skill)
    except requests.exceptions.Timeout as e:
        print(f"[ERROR] Ollama request timeout for {skill}")
        return generate_fallback_question(question_number, skill)
    except Exception as e:
        print(f"[ERROR] Error in generate_question_with_ollama: {type(e).__name__}: {str(e)}")
        import traceback
        print(f"[DEBUG] Traceback: {traceback.format_exc()}")
        return generate_fallback_question(question_number, skill)

def parse_ollama_response(response_text: str, skill: str) -> Dict[str, Any]:
    """Parse Ollama response into structured question format."""
    try:
        lines = response_text.strip().split('\n')
        question_text = ""
        options = []
        correct_answer = None
        
        for line in lines:
            line = line.strip()
            
            # Extract question
            if line.lower().startswith("question:"):
                question_text = line.split(":", 1)[1].strip()
            
            # Extract options
            elif line and len(line) > 2 and line[0].lower() in 'abcd' and line[1] in '):':
                option_text = line[3:].strip()
                options.append(option_text)
            
            # Extract correct answer
            elif line.lower().startswith("correct answer:"):
                answer_letter = line.split(":", 1)[1].strip().lower()
                if answer_letter in 'abcd':
                    answer_index = ord(answer_letter) - ord('a')
                    if 0 <= answer_index < len(options):
                        correct_answer = answer_letter
        
        # Validate parsed data
        if question_text and len(options) == 4 and correct_answer:
            return {
                "question": question_text,
                "options": options,
                "correct_answer": correct_answer,
                "skill": skill
            }
        else:
            print(f"[WARNING] Incomplete parsing: Q={bool(question_text)}, Options={len(options)}, Answer={bool(correct_answer)}")
            return None
            
    except Exception as e:
        print(f"[ERROR] Error parsing Ollama response: {e}")
        return None

def generate_fallback_question(question_number: int, skill: str) -> Dict[str, Any]:
    """Generate a fallback question when Ollama is unavailable."""
    question_templates = [
        {
            "question": f"What is a primary use case for {skill.upper()} in modern software development?",
            "options": [
                f"Building scalable applications",
                f"Managing version control systems",
                f"Debugging and testing code",
                f"Deploying applications to production"
            ],
            "correct": 0
        },
        {
            "question": f"Which of the following best describes {skill.upper()}?",
            "options": [
                f"A tool for improving developer productivity",
                f"A framework for building web applications",
                f"A database management system",
                f"An operating system component"
            ],
            "correct": 0
        },
        {
            "question": f"What is a key advantage of using {skill.upper()}?",
            "options": [
                f"Improved code maintainability",
                f"Better hardware performance",
                f"Reduced network latency",
                f"Enhanced graphic rendering"
            ],
            "correct": 0
        },
        {
            "question": f"In which scenario would you typically use {skill.upper()}?",
            "options": [
                f"When building modern software applications",
                f"When designing hardware circuits",
                f"When managing physical servers",
                f"When creating design mockups"
            ],
            "correct": 0
        }
    ]
    
    template = random.choice(question_templates)
    
    # Shuffle options but track correct answer
    correct_answer_text = template["options"][template["correct"]]
    random.shuffle(template["options"])
    correct_letter = chr(97 + template["options"].index(correct_answer_text))  # a, b, c, or d
    
    return {
        "question": template["question"],
        "options": template["options"],
        "correct_answer": correct_letter,
        "skill": skill
    }

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
            
    except Exception as e:
        print(f"[WARNING] ⚠️ Cannot connect to Ollama: {e}")
        return False

def generate_test(skills: List[str] = None, domain: str = "Professional Skills") -> str:
    """Generate a skill test based on skills from normalized_skills.json."""
    # Load skills from file if not provided
    if not skills:
        skills = load_normalized_skills()
    
    if not skills:
        return "❌ Error: No skills found. Please extract skills first."
    
    try:
        import requests
    except ImportError:
        print("[WARNING] requests library not installed, using fallback questions")
    
    questions = []
    
    print(f"\n[INFO] Generating ONE question per skill for {len(skills)} skills...")
    
    # Check Ollama status
    print("[INFO] Checking Ollama connection...")
    ollama_available = check_ollama_status()
    
    if not ollama_available:
        print("[WARNING] ⚠️  Ollama is not available. Using fallback template questions.")
        print("[INFO] To use AI-generated questions:")
        print("       1. Install Ollama from https://ollama.ai")
        print("       2. Run: ollama serve")
        print("       3. Run: ollama pull phi3:mini")
    
    # Generate exactly ONE question per skill
    for i, skill in enumerate(skills, 1):
        print(f"\n[INFO] === Question {i}/{len(skills)} for skill: {skill} ===")
        
        try:
            if ollama_available:
                question = generate_question_with_ollama(i, skill, domain)
            else:
                print(f"[INFO] Using fallback question for {skill} (Ollama unavailable)")
                question = generate_fallback_question(i, skill)
            
            if question:
                questions.append(question)
                print(f"[SUCCESS] ✅ Question {i} added successfully")
            else:
                print(f"[WARNING] ⚠️  Failed to generate question for {skill}")
        except Exception as e:
            print(f"[ERROR] ❌ Error generating question for {skill}: {str(e)}")
            # Try fallback
            try:
                question = generate_fallback_question(i, skill)
                if question:
                    questions.append(question)
                    print(f"[SUCCESS] ✅ Fallback question {i} added")
            except:
                continue
    
    if not questions:
        return "❌ Error: Failed to generate any questions."
    
    print(f"\n[INFO] ✅ Successfully generated {len(questions)} questions total")
    
    # Save the test data
    try:
        test_file = save_test_data(questions)
        print(f"[INFO] 💾 Test data saved to {test_file}")
    except Exception as e:
        print(f"[WARNING] Could not save test data: {e}")
    
    # Format questions for display
    formatted_questions = []
    for i, q in enumerate(questions, 1):
        formatted = f"Question {i}: {q['question']}\n"
        for j, option in enumerate(q['options']):
            formatted += f"{chr(97+j)}) {option}\n"
        formatted += f"Correct Answer: {q['correct_answer']}\n"
        formatted_questions.append(formatted)
    
    return "\n".join(formatted_questions)

if __name__ == "__main__":
    print("="*50)
    print("🚀 Starting SkillScope Test Generator with Ollama")
    print("="*50)
    
    # Load skills from normalized_skills.json
    print("\n📂 Loading skills from normalized_skills.json...")
    skills = load_normalized_skills()
    
    if not skills:
        print("\n⚠️ No skills found. Using sample skills for demonstration.")
        skills = ["Python", "Git", "SQL", "JavaScript", "Docker"]
    
    domain = "Professional Skills"
    
    print(f"\n🔧 Generating ONE question for each of {len(skills)} skills...")
    test = generate_test(skills, domain)
    
    if test.startswith("❌"):
        print(f"\n❌ Error: {test}")
    else:
        print("\n" + "="*50)
        print("📝 Generated Test Questions:")
        print("="*50)
        print(test)
        print("\n✅ Test generation complete!")