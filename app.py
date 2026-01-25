import os
import json
import gradio as gr
from typing import List, Dict, Any, Optional
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
            if current_question and current_question['options']:
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
    if current_question and current_question['options'] and current_question['correct_answer']:
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
                
                # For markdown
                response.append(gr.update(value=question_text, visible=True))
                
                # For radio buttons
                response.append(gr.update(
                    choices=q['options'],
                    value=None,
                    label="",
                    visible=True,
                    interactive=True
                ))
                
                print(f"[DEBUG] Added question {i+1}")
                print(f"Question: {question_text}")
                print(f"Options: {q['options']}")
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

# Create Gradio interface
with gr.Blocks(title="SkillScope - Skill Assessment Tool") as demo:
    gr.Markdown("# SkillScope - Skill Assessment Tool")
    
    with gr.Tabs() as tabs:
        with gr.TabItem("Skill Extraction"):
            with gr.Row():
                # Left column - Inputs
                with gr.Column(scale=1):
                    gr.Markdown("### Upload your resume or skills")
                    resume_upload = gr.File(label="Upload Resume (PDF/DOCX)", type="filepath", file_types=[".pdf", ".docx"])
                    skills_upload = gr.File(label="Or upload skills JSON", type="filepath", file_types=[".json"])
                    manual_skills = gr.Textbox(label="Or enter skills manually (comma-separated)", 
                                             placeholder="e.g., Python, Machine Learning, Data Analysis")
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
                            # Each question has a Markdown (question) and Radio (options)
                            with gr.Row() as q_row:
                                with gr.Column():
                                    q_md = gr.Markdown("", visible=False)
                                    q_radio = gr.Radio(
                                        choices=[], 
                                        value=None, 
                                        label="",
                                        interactive=True,
                                        visible=False,
                                        type="value"
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
            
            # Set up event handlers
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

if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7861)