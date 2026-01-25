import os
import json
import gradio as gr
from typing import List, Dict, Any
from modules.input_handler import InputHandler
from modules.test_generator import generate_test
from modules.skill_normalizer import save_normalized_skills
from modules.profile_summary import save_profile_summary

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
        os.makedirs("data", exist_ok=True)
        with open("data/normalized_skills.json", "w") as f:
            json.dump({"normalized_skills": unique_skills}, f, indent=2)
        return unique_skills
    except Exception as e:
        print(f"Error saving normalized skills: {e}")
        return []

def parse_test_output(test_text: str) -> List[Dict[str, Any]]:
    """Parse the raw test output into a structured format."""
    questions = []
    current_question = None
    current_options = []
    
    # Split the test text into lines and process each line
    lines = [line.strip() for line in test_text.split('\n') if line.strip()]
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Check for question line
        if line.lower().startswith('question') and ':' in line:
            if current_question and current_question.get('options'):
                questions.append(current_question)
                
            # Extract question text
            question_text = line.split(':', 1)[1].strip()
            current_question = {
                'question': question_text,
                'options': [],
                'correct_answer': None
            }
            current_options = []
            i += 1
            continue
            
        # Check for answer options (a), b), etc.)
        if (current_question is not None and 
            len(line) > 2 and 
            line[0].lower() in 'abcd' and 
            line[1] in '.)'):
            
            option_text = line[3:].strip()  # Skip the "X) " part
            current_question['options'].append(option_text)
            i += 1
            continue
            
        # Check for correct answer
        if (current_question is not None and 
            'correct answer:' in line.lower()):
            
            # Extract the letter of the correct answer
            correct_letter = line.split(':')[-1].strip().lower()
            if correct_letter and correct_letter in 'abcd':
                answer_index = ord(correct_letter) - ord('a')
                if 0 <= answer_index < len(current_question['options']):
                    current_question['correct_answer'] = current_question['options'][answer_index]
            i += 1
            continue
            
        i += 1
    
    # Add the last question if it exists
    if current_question and current_question.get('options') and current_question.get('correct_answer'):
        questions.append(current_question)
    
    return questions

def process_inputs(resume_file, skills_json_file, manual_skills):
    """Process inputs and generate test questions."""
    try:
        # Process all inputs and extract skills
        result = input_handler.process_inputs(
            resume_path=resume_file.name if resume_file else None,
            skills_json_path=skills_json_file.name if skills_json_file else None,
            manual_skills=manual_skills
        )
        
        if not result["success"] or not result["skills"]:
            error_response = ["❌ No skills were extracted. Please check your inputs and try again."]
            error_response.extend([gr.update(visible=False)] * 23)
            return error_response
        
        # Save normalized skills
        print(f"\n[DEBUG] Raw skills before normalization: {result['skills']}")
        try:
            normalized_skills = save_normalized_skills(result["skills"])
            print(f"[DEBUG] Normalized skills: {normalized_skills}")
            if not normalized_skills:
                error_response = ["❌ Failed to normalize skills. No valid skills were found."]
                error_response.extend([gr.update(visible=False)] * 23)
                return error_response
        except Exception as e:
            print(f"[ERROR] Error during skill normalization: {str(e)}")
            error_response = [f"❌ Error normalizing skills: {str(e)}"]
            error_response.extend([gr.update(visible=False)] * 23)
            return error_response
        
        # Generate profile summary
        save_profile_summary()
        
        # Generate test
        test_text = generate_test(normalized_skills, "Professional Skills")
        
        if not test_text or "error" in test_text.lower():
            error_response = [f"❌ Error generating test: {test_text}"]
            error_response.extend([gr.update(visible=False)] * 23)
            return error_response
        
        # Parse test questions
        test_questions = parse_test_output(test_text)
        
        if not test_questions:
            error_response = ["❌ Failed to generate valid test questions. Please try again."]
            error_response.extend([gr.update(visible=False)] * 23)
            return error_response        
        
        # Update test state
        test_state.questions = [q['question'] for q in test_questions]
        test_state.correct_answers = [q['correct_answer'] for q in test_questions]
        test_state.user_answers = [None] * len(test_questions)
        
        # Debug: Print parsed questions
        for i, q in enumerate(test_questions):
            print(f"Q{i+1}: {q['question']}")
            print(f"Options: {q['options']}")
            print(f"Correct: {q['correct_answer']}\n")
        
        print("\n[DEBUG] Creating UI response...")
        
        # 1. Status message and container
        response = [
            gr.update(value="✅ Test generated successfully! Please answer the questions below:", visible=True),  # status_output
            gr.update(visible=True)  # test_container
        ]
        print("[DEBUG] Added status and container visibility")
        
        # 2. Question components (10 questions = 20 components)
        for i in range(10):
            if i < len(test_questions):
                q = test_questions[i]
                question_text = f"**{i+1}. {q['question']}**"
                
                # For markdown - make sure it's visible and has content
                response.append(gr.update(
                    value=question_text,
                    visible=True
                ))
                
                # For radio buttons - ensure proper formatting
                response.append(gr.update(
                    choices=q['options'],
                    value=None,
                    label=f"Question {i+1}",
                    visible=True,
                    interactive=True
                ))
                
                print(f"[DEBUG] Added question {i+1}")
                print(f"Question: {question_text}")
                print(f"Options: {q['options']}")
                print(f"Correct: {q['correct_answer']}")
            else:
                # For hidden questions
                response.extend([
                    gr.update(visible=False),
                    gr.update(visible=False)
                ])
        
        # 3. Submit button and results output
        response.extend([
            gr.update(visible=True),  # submit_btn
            gr.update(visible=False)  # results_output
        ])
        
        # Debug: Print the response structure
        print("\n[DEBUG] Response structure:")
        for i, item in enumerate(response):
            print(f"{i}: {type(item).__name__} - {getattr(item, 'visible', 'N/A')}")
        
        print(f"[DEBUG] Total response elements: {len(response)}")
        return response
        
    except Exception as e:
        import traceback
        print(f"[ERROR] Exception in process_inputs: {str(e)}")
        print(traceback.format_exc())
        error_response = [f"❌ An error occurred: {str(e)}"]
        error_response.extend([gr.update(visible=False)] * 23)
        return error_response

def calculate_score(*user_answers):
    """Calculate and display test results."""
    try:
        score = 0
        results = []
        
        for i, (user_ans, correct_ans) in enumerate(zip(user_answers, test_state.correct_answers)):
            is_correct = user_ans == correct_ans
            if is_correct:
                score += 1
            results.append({
                'question': test_state.questions[i],
                'user_answer': user_ans or "Not answered",
                'correct_answer': correct_ans,
                'is_correct': is_correct
            })
        
        total = len(test_state.questions)
        percentage = (score / total * 100) if total > 0 else 0
        
        # Format results
        result_text = f"## Test Results\n\n**Score: {score}/{total} ({percentage:.1f}%)**\n\n### Detailed Results:\n\n"
        
        for i, result in enumerate(results):
            status = '✅' if result['is_correct'] else '❌'
            result_text += f"""**{i+1}. {result['question']}**
- Your answer: {result['user_answer']}
- Correct answer: {result['correct_answer']}
{status} {'Correct' if result['is_correct'] else 'Incorrect'}

"""
        
        return gr.update(value=result_text, visible=True)
        
    except Exception as e:
        return gr.update(value=f"❌ Error calculating score: {str(e)}", visible=True)

def start_terminal_test(skills_input):
    """Start a terminal-style test with the given skills."""
    skills = [s.strip() for s in skills_input.split(',') if s.strip()]
    if not skills:
        skills = ["Python", "Git", "SQL", "JavaScript", "Docker"]
    
    # Generate test
    test_text = generate_test(skills, "Professional Skills")
    test_questions = parse_test_output(test_text)
    
    if not test_questions:
        return "❌ Failed to generate test questions. Please try again.", gr.update(visible=False)
    
    # Save test state
    test_state.questions = test_questions
    test_state.current_question = 0
    test_state.score = 0
    test_state.user_answers = []
    test_state.correct_answers = [q['correct_answer'] for q in test_questions]
    
    # Show first question
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
        return "No active test. Please start a new test.", gr.update(visible=False)
    
    q_index = test_state.current_question
    q = test_state.questions[q_index]
    answer = answer.strip().lower()
    
    # Process answer
    if answer in ['a', 'b', 'c', 'd']:
        user_answer = q['options'][ord(answer) - ord('a')]
        test_state.user_answers.append(user_answer)
        
        if user_answer == q['correct_answer']:
            test_state.score += 1
            result = "✅ Correct!\n\n"
        else:
            result = f"❌ Incorrect. The correct answer was: {q['correct_answer']}\n\n"
        
        # Move to next question
        test_state.current_question += 1
        next_question = show_question(test_state.current_question)
        if isinstance(next_question, tuple):
            return result + next_question[0], next_question[1]
        return current_output + "\n" + result + next_question, gr.update(visible=False)
    else:
        return current_output + "\nInvalid input. Please enter a, b, c, or d: ", gr.update(visible=True)

def show_results():
    """Display the test results in terminal-style format."""
    total = len(test_state.questions)
    score_percent = (test_state.score / total) * 100
    
    result = "="*50 + "\n"
    result += "Test Results\n"
    result += "="*50 + "\n\n"
    result += f"Your score: {test_state.score}/{total} ({score_percent:.1f}%)\n\n"
    
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
    
    result += "="*50 + "\n"
    result += "Test completed. Thank you for using SkillScope!\n"
    result += "="*50
    
    return result, gr.update(visible=False)

# Create Gradio interface
with gr.Blocks(title="SkillScope - Skill Assessment Tool") as demo:
    gr.Markdown("# SkillScope - Skill Assessment Tool")
    
    # Add custom CSS for better question display
    custom_css = """
    .question-text {
        margin-bottom: 10px;
        font-size: 1.1em;
    }
    .question-options {
        margin-bottom: 20px;
    }
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
    """
    gr.HTML(f'<style>{custom_css}</style>')
    
    with gr.Tabs() as tabs:
        # Original Test Interface
        with gr.TabItem("Standard Test"):
            with gr.Row():
                # Left column - Inputs
                with gr.Column(scale=1):
                    gr.Markdown("### Upload your resume or skills")
                    resume_upload = gr.File(label="Upload Resume (PDF/DOCX)", type="filepath", file_types=[".pdf", ".docx"])
                    skills_upload = gr.File(label="Or upload skills JSON", type="filepath", file_types=[".json"])
                    manual_skills = gr.Textbox(
                        label="Or enter skills manually (comma-separated)", 
                        placeholder="e.g., Python, Machine Learning, Data Analysis"
                    )
                    generate_btn = gr.Button("Generate Skill Test", variant="primary")
                
                # Right column - Outputs
                with gr.Column(scale=2):
                    status_output = gr.Markdown("## Welcome to SkillScope!\n\nUpload your resume, skills JSON, or enter skills manually to begin.")
                    
                    # Test container (initially hidden)
                    test_container = gr.Column(visible=False, variant="panel")
                    with test_container:
                        gr.Markdown("### Answer the following questions:")
                        
                        # Create question components
                        test_questions = []
                        for i in range(10):
                            with gr.Row() as q_row:
                                # Question text
                                q_md = gr.Markdown("", visible=False, elem_classes=["question-text"])
                                
                                # Answer options
                                q_radio = gr.Radio(
                                    choices=[],
                                    value=None,
                                    label="",
                                    interactive=True,
                                    visible=False,
                                    type="value",
                                    elem_classes=["question-options"]
                                )
                                test_questions.extend([q_md, q_radio])
                        
                        # Submit button and results
                        with gr.Row():
                            submit_btn = gr.Button("Submit Test", visible=False, variant="primary")
                        results_output = gr.Markdown("", visible=False)
                        
                        # Debug info
                        debug_output = gr.Textbox(
                            label="Debug Info",
                            visible=False,  # Set to True for debugging
                            interactive=False,
                            lines=10
                        )
            
            # Set up event handlers for standard test
            all_outputs = [status_output, test_container]  # First two outputs
            
            # Add question components (markdown + radio for each question)
            for i in range(0, len(test_questions), 2):
                all_outputs.extend([test_questions[i], test_questions[i+1]])
                
            # Add submit button and results
            all_outputs.extend([submit_btn, results_output])
            
            print(f"[DEBUG] Total outputs: {len(all_outputs)}")
            
            # Generate test button click
            generate_btn.click(
                fn=process_inputs,
                inputs=[resume_upload, skills_upload, manual_skills],
                outputs=all_outputs
            )
            
            # Submit test button click
            submit_btn.click(
                fn=calculate_score,
                inputs=test_questions[1::2],  # Get every second element (the Radio components)
                outputs=results_output
            )
        
        # Terminal-Style Test Tab
        with gr.TabItem("Terminal-Style Test"):
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### Terminal-Style Skill Test")
                    terminal_skills = gr.Textbox(
                        label="Enter your skills (comma-separated)",
                        value="Python, Git, SQL, JavaScript, Docker",
                        placeholder="e.g., Python, Git, SQL, JavaScript, Docker"
                    )
                    start_test_btn = gr.Button("Start Terminal Test", variant="primary")
                    gr.Markdown("""
                    **Instructions:**
                    - Click "Start Terminal Test" to begin
                    - For each question, type your answer (a, b, c, or d) and press Enter
                    - You'll see immediate feedback after each answer
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
            
            # Terminal test event handlers
            start_test_btn.click(
                fn=start_terminal_test,
                inputs=terminal_skills,
                outputs=[terminal_output, terminal_input]
            )
            
            terminal_input.submit(
                fn=process_terminal_answer,
                inputs=[terminal_input, terminal_output],
                outputs=[terminal_output, terminal_input]
            )

if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7861)