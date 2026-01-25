"""
Module 3: Test Generator for SkillScope
Generates skill tests using a simple template-based approach.
"""
from typing import List
import random
import os

def generate_test(skills: List[str], domain: str) -> str:
    """
    Generate a skill test based on provided skills and domain.
    
    Args:
        skills: List of skill strings to include in the test
        domain: Domain/industry context for the test
    """
    if not skills:
        return "❌ Error: No skills provided"

    try:
        # Shuffle skills to get random selection
        random.shuffle(skills)
        selected_skills = skills[:min(5, len(skills))]  # Use up to 5 skills
        
        questions = []
        question_number = 1
        
        for skill in selected_skills:
            # Generate different types of questions for each skill
            questions.append(generate_question(question_number, skill, "purpose"))
            question_number += 1
            
            questions.append(generate_question(question_number, skill, "feature"))
            question_number += 1

        return "\n".join(questions)
        
    except Exception as e:
        return f"❌ Error generating test: {str(e)}"

def generate_question(number: int, skill: str, q_type: str) -> str:
    """Generate a single question based on type."""
    if q_type == "purpose":
        question = f"Question {number}: What is the primary purpose of {skill.upper()} in software development?"
        options = [
            "To manage database operations",
            "To handle user interface design",
            "To implement business logic",
            "To optimize network performance"
        ]
        correct = 2  # Index of correct answer
    else:  # feature question
        question = f"Question {number}: Which of these is a key feature of {skill.upper()}?"
        options = [
            "Object-oriented programming support",
            "Functional programming paradigm",
            "Both A and B",
            "None of the above"
        ]
        correct = 2  # Index of correct answer
    
    # Shuffle options but keep track of correct answer
    correct_answer = options[correct]
    random.shuffle(options)
    correct_letter = "abcd"[options.index(correct_answer)]
    
    # Format the question and options
    question_text = [f"{question}"]
    for i, option in enumerate(options):
        question_text.append(f"{'abcd'[i]}) {option}")
    question_text.append(f"Correct Answer: {correct_letter}\n")
    
    return "\n".join(question_text)

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
    print("🚀 Starting SkillScope Test Generator")
    print("="*50)
    
    # Example usage
    sample_skills = ["Python", "JavaScript", "SQL", "Git", "Docker"]
    domain = "Software Development"
    
    print("\n🔧 Generating test with sample skills...")
    test = generate_test(sample_skills, domain)
    
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