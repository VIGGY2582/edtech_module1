import os
import json
import gradio as gr
from typing import List, Dict, Any
from modules.input_handler import InputHandler
from modules.test_generator import generate_test
from modules.skill_normalizer import save_normalized_skills
from modules.profile_summary import save_profile_summary
from modules.domain_suggester import get_domain_suggestions

# Create data directory if it doesn't exist
os.makedirs("data", exist_ok=True)

# Initialize the input handler
input_handler = InputHandler()

class TestState:
    def __init__(self):
        self.questions = []
        self.correct_answers = []
        self.user_answers = []
        self.current_question = 0
        self.score = 0

test_state = TestState()

def save_normalized_skills(skills: List[str]) -> List[str]:
    """Save normalized skills to a file."""
    try:
        normalized_skills = [skill.strip().lower() for skill in skills if skill.strip()]
        seen = set()
        unique_skills = []
        for skill in normalized_skills:
            if skill not in seen:
                seen.add(skill)
                unique_skills.append(skill)
        
        os.makedirs("data", exist_ok=True)
        with open("data/normalized_skills.json", "w") as f:
            json.dump({"normalized_skills": unique_skills}, f, indent=2)
        return unique_skills
    except Exception as e:
        print(f"Error saving normalized skills: {e}")
        return []

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

def parse_test_output(test_text: str) -> List[Dict[str, Any]]:
    """Parse the raw test output into a structured format."""
    questions = []
    current_question = None
    current_options = []
    
    lines = [line.strip() for line in test_text.split('\n') if line.strip()]
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        if line.lower().startswith('question') and ':' in line:
            if current_question and current_question.get('options'):
                questions.append(current_question)
                
            question_text = line.split(':', 1)[1].strip()
            current_question = {
                'question': question_text,
                'options': [],
                'correct_answer': None
            }
            current_options = []
            i += 1
            continue
            
        if (current_question is not None and 
            len(line) > 2 and 
            line[0].lower() in 'abcd' and 
            line[1] in '.)'):
            
            option_text = line[3:].strip()
            current_question['options'].append(option_text)
            i += 1
            continue
            
        if (current_question is not None and 
            'correct answer:' in line.lower()):
            
            correct_letter = line.split(':')[-1].strip().lower()
            if correct_letter and correct_letter in 'abcd':
                answer_index = ord(correct_letter) - ord('a')
                if 0 <= answer_index < len(current_question['options']):
                    current_question['correct_answer'] = current_question['options'][answer_index]
            i += 1
            continue
            
        i += 1
    
    if current_question and current_question.get('options') and current_question.get('correct_answer'):
        questions.append(current_question)
    
    return questions

def process_skill_extraction(resume_file, skills_json_file, manual_skills):
    """Process inputs and extract skills only."""
    try:
        result = input_handler.process_inputs(
            resume_path=resume_file.name if resume_file else None,
            skills_json_path=skills_json_file.name if skills_json_file else None,
            manual_skills=manual_skills
        )
        
        if not result["success"] or not result["skills"]:
            return "❌ No skills were extracted. Please check your inputs and try again."
        
        print(f"\n[DEBUG] Raw skills before normalization: {result['skills']}")
        normalized_skills = save_normalized_skills(result["skills"])
        print(f"[DEBUG] Normalized skills: {normalized_skills}")
        
        if not normalized_skills:
            return "❌ Failed to normalize skills. No valid skills were found."
        
        save_profile_summary()
        
        skills_list = "\n".join([f"- {skill}" for skill in normalized_skills])
        success_message = f"""## ✅ Skills Extracted Successfully!

### Extracted Skills:
{skills_list}

**Total Skills:** {len(normalized_skills)}

Your skills have been saved to `data/normalized_skills.json`. You can now use the **Terminal-Style Test** tab to test your knowledge!
"""
        return success_message
        
    except Exception as e:
        import traceback
        print(f"[ERROR] Exception in process_skill_extraction: {str(e)}")
        print(traceback.format_exc())
        return f"❌ An error occurred: {str(e)}"

def start_terminal_test(use_extracted_skills, manual_skills_input):
    """Start a terminal-style test with skills from file or manual input."""
    skills = []
    
    if use_extracted_skills:
        skills = load_normalized_skills()
        if not skills:
            return "❌ No extracted skills found. Please extract skills first or enter manual skills.", gr.update(visible=False)
    else:
        if manual_skills_input and manual_skills_input.strip():
            skills = [s.strip() for s in manual_skills_input.split(',') if s.strip()]
        else:
            return "❌ Please enter skills manually or select 'Use Extracted Skills'.", gr.update(visible=False)
    
    if not skills:
        return "❌ No skills available. Please extract skills or enter them manually.", gr.update(visible=False)
    
    print(f"[INFO] Generating test for skills: {skills}")
    test_text = generate_test(skills, "Professional Skills")
    test_questions = parse_test_output(test_text)
    
    if not test_questions:
        return "❌ Failed to generate test questions. Please try again.\n\nMake sure Ollama is running if you want AI-generated questions.", gr.update(visible=False)
    
    test_state.questions = test_questions
    test_state.current_question = 0
    test_state.score = 0
    test_state.user_answers = []
    test_state.correct_answers = [q['correct_answer'] for q in test_questions]
    
    return show_question(0)

def show_question(q_index):
    """Display the current question in terminal-style format."""
    if q_index >= len(test_state.questions):
        return show_results()
    
    q = test_state.questions[q_index]
    question_text = f"Question {q_index + 1} of {len(test_state.questions)}\n\n"
    question_text += f"{q['question']}\n\n"
    for i, option in enumerate(q['options']):
        question_text += f"{chr(97+i)}) {option}\n"
    
    question_text += "\nYour answer (a/b/c/d): "
    return question_text, gr.update(visible=True)

def process_terminal_answer(answer, current_output):
    """Process the user's answer in the terminal-style test."""
    if not hasattr(test_state, 'current_question'):
        return "No active test. Please start a new test.", gr.update(visible=False), gr.update()
    
    q_index = test_state.current_question
    q = test_state.questions[q_index]
    answer = answer.strip().lower()
    
    if answer in ['a', 'b', 'c', 'd']:
        user_answer = q['options'][ord(answer) - ord('a')]
        test_state.user_answers.append(user_answer)
        
        if user_answer == q['correct_answer']:
            test_state.score += 1
            result = "✅ Correct!\n\n"
        else:
            result = f"❌ Incorrect. The correct answer was: {q['correct_answer']}\n\n"
        
        test_state.current_question += 1
        
        if test_state.current_question >= len(test_state.questions):
            # Test is complete, show results
            final_result, input_update, domain_msg = show_results()
            return final_result, input_update, domain_msg
        else:
            # Show next question
            next_question = show_question(test_state.current_question)
            if isinstance(next_question, tuple):
                return result + next_question[0], next_question[1], gr.update()
            return current_output + "\n" + result + next_question, gr.update(visible=False), gr.update()
    else:
        return current_output + "\nInvalid input. Please enter a, b, c, or d: ", gr.update(visible=True), gr.update()

def show_results():
    """Display the test results in terminal-style format and save to JSON."""
    from datetime import datetime
    
    total = len(test_state.questions)
    score = test_state.score
    score_percent = (score / total) * 100
    
    # Determine skill level
    if score_percent < 40:
        level = "Beginner"
    elif score_percent <= 70:
        level = "Intermediate"
    else:
        level = "Advanced"
    
    # Identify strengths and weak areas
    strengths = []
    weak_areas = []
    
    for i, (q, user_ans) in enumerate(zip(test_state.questions, test_state.user_answers)):
        topic = q.get('skill', f"Question {i+1}")
        if user_ans == q['correct_answer']:
            strengths.append(topic)
        else:
            weak_areas.append(topic)
    
    # Create evaluation result
    evaluation_result = {
        "test_id": f"test_{int(datetime.now().timestamp())}",
        "score": score,
        "total_questions": total,
        "percentage": round(score_percent, 2),
        "level": level,
        "strengths": strengths,
        "weak_areas": weak_areas,
        "timestamp": datetime.now().isoformat(),
        "detailed_results": [
            {
                "question": q['question'],
                "user_answer": user_ans,
                "correct_answer": q['correct_answer'],
                "is_correct": user_ans == q['correct_answer']
            }
            for q, user_ans in zip(test_state.questions, test_state.user_answers)
        ]
    }
    
    # Save evaluation result to JSON
    os.makedirs("data", exist_ok=True)
    result_file = os.path.join("data", "evaluation_result.json")
    try:
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump(evaluation_result, f, indent=4, ensure_ascii=False)
        print(f"[INFO] ✅ Evaluation results saved to {result_file}")
    except Exception as e:
        print(f"[ERROR] ❌ Failed to save evaluation results: {e}")
    
    # Get domain suggestions
    try:
        domains = get_domain_suggestions()
        domain_message = "## 🎯 Domain Suggestions\n\n"
        domain_message += "Based on your assessment and skill profile, you might be interested in these career domains:\n\n"
        domain_message += "\n".join([f"### {i+1}. {domain}" for i, domain in enumerate(domains)])
        domain_message += "\n\n---\n\n"
        domain_message += "💡 **Tip:** Research these domains further and align your learning path with your career goals!"
    except Exception as e:
        print(f"[ERROR] ❌ Failed to generate domain suggestions: {e}")
        domain_message = "## ⚠️ Domain Suggestions Unavailable\n\n"
        domain_message += "Could not generate domain suggestions at this time. Please try again later."
    
    # Format terminal output
    result = "="*50 + "\n"
    result += "Test Results\n"
    result += "="*50 + "\n\n"
    result += f"Your score: {score}/{total} ({score_percent:.1f}%)\n"
    result += f"Level: {level}\n\n"
    
    if score_percent >= 80:
        result += "🎉 Excellent work! You have a strong understanding of these skills.\n"
    elif score_percent >= 60:
        result += "👍 Good job! You have a decent understanding, but there's room for improvement.\n"
    else:
        result += "📚 Keep practicing! Review the skills and try again.\n"
    
    result += "\n" + "="*50 + "\n"
    result += "Detailed Results:\n"
    result += "="*50 + "\n\n"
    
    for i, (q, user_ans) in enumerate(zip(test_state.questions, test_state.user_answers), 1):
        result += f"Question {i}: {q['question']}\n"
        result += f"Your answer: {user_ans}\n"
        result += f"Correct answer: {q['correct_answer']}\n"
        if user_ans == q['correct_answer']:
            result += "✅ Correct!\n\n"
        else:
            result += "❌ Incorrect\n\n"
    
    # Add summary
    result += "="*50 + "\n"
    if strengths:
        result += f"✅ Strengths: {', '.join(strengths[:3])}\n"
    if weak_areas:
        result += f"📚 Areas to improve: {', '.join(weak_areas[:3])}\n"
    result += "="*50 + "\n"
    result += "Test completed. Thank you for using SkillScope!\n"
    result += f"📄 Results saved to: {result_file}\n"
    result += "\n💡 Check the 'Domain Suggestions' tab for career recommendations!\n"
    result += "="*50
    
    return result, gr.update(visible=False), gr.update(value=domain_message, visible=True)

# Create Gradio interface
with gr.Blocks(title="SkillScope - Skill Assessment Tool") as demo:
    gr.Markdown("# SkillScope - Skill Assessment Tool")
    
    custom_css = """
    .terminal-output {
        font-family: monospace;
        white-space: pre;
        background-color: #1e1e1e;
        color: #f0f0f0;
        padding: 15px;
        border-radius: 5px;
        height: 400px;
        overflow-y: auto;
    }
    .domain-suggestion {
        padding: 15px;
        font-family: monos
        background: #1e1e1e;
        color: #f0f0f0;
        border-radius: 8px;
        border-left: 4px solid #4CAF50;
    }
    """
    gr.HTML(f'<style>{custom_css}</style>')
    
    with gr.Tabs() as main_tabs:
        # Skill Extraction Tab
        with gr.TabItem("Skill Extraction"):
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### Upload your resume or skills")
                    resume_upload = gr.File(label="Upload Resume (PDF/DOCX)", type="filepath", file_types=[".pdf", ".docx"])
                    skills_upload = gr.File(label="Or upload skills JSON", type="filepath", file_types=[".json"])
                    manual_skills = gr.Textbox(
                        label="Or enter skills manually (comma-separated)", 
                        placeholder="e.g., Python, Machine Learning, Data Analysis"
                    )
                    extract_btn = gr.Button("Extract Skills", variant="primary")
                
                with gr.Column(scale=2):
                    extraction_output = gr.Markdown("""## Welcome to SkillScope!

Upload your resume, skills JSON, or enter skills manually to extract and analyze your skills.

After extraction, you can use the **Terminal-Style Test** tab to test your knowledge!
""")
            
            extract_btn.click(
                fn=process_skill_extraction,
                inputs=[resume_upload, skills_upload, manual_skills],
                outputs=extraction_output
            )
        
        # Terminal-Style Test Tab
        with gr.TabItem("Terminal-Style Test"):
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### Terminal-Style Skill Test")
                    
                    use_extracted = gr.Checkbox(
                        label="Use Extracted Skills from normalized_skills.json",
                        value=True,
                        info="If checked, uses skills from the Skill Extraction tab"
                    )
                    
                    manual_skills_terminal = gr.Textbox(
                        label="Or enter skills manually (comma-separated)",
                        value="",
                        placeholder="e.g., Python, Git, SQL, JavaScript, Docker",
                        info="Only used if 'Use Extracted Skills' is unchecked"
                    )
                    
                    start_test_btn = gr.Button("Start Terminal Test", variant="primary")
                    
                    gr.Markdown("""
**Instructions:**
1. Choose to use extracted skills OR enter manual skills
2. Click "Start Terminal Test" to begin
3. For each question, type your answer (a, b, c, or d) and press Enter
4. You'll see immediate feedback after each answer
5. Complete all questions to see your final score and domain suggestions

**Note:** Questions are generated using Ollama AI (phi3:mini model). Make sure Ollama is running for best results!
                    """)
                
                with gr.Column(scale=2):
                    terminal_output = gr.Textbox(
                        label="Test Output",
                        lines=20,
                        max_lines=50,
                        interactive=False,
                        elem_classes=["terminal-output"]
                    )
                    terminal_input = gr.Textbox(
                        label="Your Answer",
                        placeholder="Type your answer (a/b/c/d) and press Enter",
                        visible=False,
                        container=False
                    )
        
        # Domain Suggestions Tab - Define BEFORE using it
        with gr.TabItem("Domain Suggestions"):
            domain_suggestions_output = gr.Markdown(
                """## 🎯 Domain Suggestions

Complete the skill assessment test to receive personalized career domain recommendations based on your skills and performance.

**How it works:**
1. Complete the Terminal-Style Test
2. Your results will be analyzed
3. Domain suggestions will appear here automatically

Get started by going to the **Terminal-Style Test** tab!
""",
                elem_classes=["domain-suggestion"]
            )
    
    # Event handlers - Define AFTER all components are created
    start_test_btn.click(
        fn=start_terminal_test,
        inputs=[use_extracted, manual_skills_terminal],
        outputs=[terminal_output, terminal_input]
    )
    
    terminal_input.submit(
        fn=process_terminal_answer,
        inputs=[terminal_input, terminal_output],
        outputs=[terminal_output, terminal_input, domain_suggestions_output]
    )

if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7861)