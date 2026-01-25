"""
Module 3: Test Generator for SkillScope
Generates skill tests using local Ollama LLM.
"""
import os
import json
from typing import List
import ollama

def generate_test(skills: List[str], domain: str) -> str:
    """
    Generate a skill test based on provided skills and domain using Ollama.
    
    Args:
        skills: List of skill strings to include in the test
        domain: Domain/industry context for the test
    """
    if not skills:
        return "❌ Error: No skills provided"

    try:
        # Format the skills for the prompt
        skills_text = ", ".join(skills[:5])  # Use up to 5 skills to keep the test focused
        
        # Create a clear prompt
        prompt = f"""Generate a 5-question multiple choice test for a {domain} professional.
Focus on these skills: {skills_text}.

Requirements:
- Each question should have 4 options (a-d) with one correct answer
- Format as plain text, no markdown
- Clearly indicate the correct answer after each question
- Keep questions concise and practical
- Focus on practical, real-world scenarios
- Include a mix of conceptual and practical questions

Format each question exactly like this:
Question 1: [question text]
a) [option 1]
b) [option 2]
c) [option 3]
d) [option 4]
Correct Answer: [letter]

Example:
Question 1: What is the time complexity of a binary search algorithm?
a) O(1)
b) O(log n)
c) O(n)
d) O(n²)
Correct Answer: b
"""
        # Generate content using Ollama
        response = ollama.chat(
            model="phi3:mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that generates professional skill assessment tests. Provide clear, well-formatted multiple choice questions with exactly 4 options each and indicate the correct answer."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            options={
                'temperature': 0.7,
                'top_p': 0.9
            }
        )
        
        # Extract and clean the response
        test_content = response['message']['content'].strip()
        
        # Ensure the response follows the required format
        if "question 1:" not in test_content.lower():
            # If the response doesn't follow the format, try to fix it
            questions = []
            lines = test_content.split('\n')
            current_question = None
            
            for line in lines:
                line = line.strip()
                if line.lower().startswith(('question', 'q:')):
                    if current_question:
                        questions.append(current_question)
                    current_question = [line]
                elif current_question is not None:
                    current_question.append(line)
            
            if current_question:
                questions.append(current_question)
            
            # Reformat the questions
            reformatted = []
            for i, q in enumerate(questions, 1):
                if len(q) >= 6:  # At least question + 4 options + answer
                    reformatted.append(f"Question {i}: {q[0].split(':', 1)[1].strip()}")
                    for j in range(1, 5):
                        if j-1 < len(q):
                            reformatted.append(f"{'abcd'[j-1]}) {q[j].strip()}")
                    reformatted.append(f"Correct Answer: {q[-1][-1].lower()}")
                    reformatted.append("")
            
            test_content = "\n".join(reformatted).strip()
        
        return test_content
        
    except Exception as e:
        return f"❌ Error generating test: {str(e)}"

def save_test_to_file(test_content: str, filename: str = "skill_test.txt") -> bool:
    """Save the generated test to a file."""
    try:
        os.makedirs("data", exist_ok=True)
        filepath = os.path.join("data", filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(test_content)
        return True
    except Exception as e:
        print(f"❌ Error saving test: {str(e)}")
        return False

if __name__ == "__main__":
    print("="*50)
    print("🚀 Starting SkillScope Test Generator (Local AI)")
    print("="*50)
    
    # Test the module
    test_skills = ["Python", "Machine Learning", "Data Analysis"]
    test_domain = "Data Science"
    
    print(f"Generating test for skills: {', '.join(test_skills)}")
    test = generate_test(test_skills, test_domain)
    
    if test.startswith("❌"):
        print(test)
    else:
        print("\n" + "="*50)
        print("📝 Generated Test:")
        print("="*50)
        print(test)
        
        # Save to file
        if save_test_to_file(test):
            print("\n✅ Test generated successfully and saved to data/skill_test.txt")
        else:
            print("\n❌ Failed to save test to file")
    
    print("\n" + "="*50)
    print("🏁 Test generation completed")
    print("="*50)