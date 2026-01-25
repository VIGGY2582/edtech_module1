# In the imports section at the top of the file, make sure these are included:
import os
import json
from typing import List, Dict, Any
import gradio as gr
from modules.input_handler import InputHandler
from modules.skill_normalizer import save_normalized_skills
from modules.profile_summary import save_profile_summary
from modules.test_generator import generate_test

# Initialize the input handler
input_handler = InputHandler()

# Global state to store questions
test_questions = []

def parse_test_output(test_text: str) -> List[Dict[str, Any]]:
    """Parse the raw test output into a structured format."""
    questions = []
    current_question = None
    
    for line in test_text.split('\n'):
        line = line.strip()
        if not line:
            continue
            
        # Check for question
        if line.lower().startswith(('question', 'q:')):
            if current_question is not None:
                questions.append(current_question)
            current_question = {
                'question': line.split(':', 1)[1].strip() if ':' in line else line,
                'options': [],
                'correct_answer': None
            }
        # Check for options (A, B, C, D)
        elif line and line[0] in 'ABCD' and (line[1] == '.' or line[1] == ')'):
            option_text = line[3:].strip()
            current_question['options'].append(option_text)
            # Check if this is the correct answer
            if line.endswith('*'):
                current_question['correct_answer'] = option_text.rstrip('*').strip()
                current_question['options'][-1] = current_question['correct_answer']
        # Check for correct answer indicator in the format [Correct: X]
        elif line.lower().startswith('[correct:') and current_question:
            correct_letter = line.split(':')[1].strip(' ]').upper()
            if correct_letter in 'ABCD' and len(current_question['options']) > 0:
                idx = ord(correct_letter) - ord('A')
                if 0 <= idx < len(current_question['options']):
                    current_question['correct_answer'] = current_question['options'][idx]
    
    # Add the last question if it exists
    if current_question is not None:
        questions.append(current_question)
    
    # Validate questions
    valid_questions = []
    for q in questions:
        if (q.get('question') and 
            len(q.get('options', [])) >= 2 and 
            q.get('correct_answer') in q.get('options', [])):
            valid_questions.append(q)
    
    return valid_questions

def process_inputs(resume_file, skills_json_file, manual_skills):
    """Process all inputs, extract skills, normalize them, and generate test."""
    global test_questions
    
    try:
        # Process all inputs and extract skills
        result = input_handler.process_inputs(
            resume_path=resume_file.name if resume_file else None,
            skills_json_path=skills_json_file.name if skills_json_file else None,
            manual_skills=manual_skills
        )
        
        if not result["success"] or not result["skills"]:
            return ["❌ No skills were extracted. Please check your inputs and try again."] + [gr.update(visible=False)] * 21
        
        # Save normalized skills
        normalized_skills = save_normalized_skills(result["skills"])
        if not normalized_skills:
            return ["❌ Failed to normalize skills. Please try again."] + [gr.update(visible=False)] * 21
        
        # Generate profile summary
        summary = save_profile_summary(normalized_skills)
        if not summary:
            return ["❌ Failed to generate profile summary. Please try again."] + [gr.update(visible=False)] * 21
        
        # Generate test
        test_text = generate_test(normalized_skills, "Professional Skills")
        if not test_text or "error" in test_text.lower():
            return [f"❌ Error generating test: {test_text}"] + [gr.update(visible=False)] * 21
        
        # Parse test questions
        test_questions = parse_test_output(test_text)
        if not test_questions:
            return ["❌ Failed to generate valid test questions. Please try again."] + [gr.update(visible=False)] * 21
        
        # Prepare updates for UI
        updates = [
            f"✅ Successfully processed {len(normalized_skills)} skills and generated {len(test_questions)} questions. Please go to the 'Skill Test' tab.",
            gr.update(visible=True)  # Show test container
        ]
        
        # Update question components
        for i in range(10):
            if i < len(test_questions):
                q = test_questions[i]
                updates.extend([
                    gr.update(value=f"**{i+1}. {q['question']}**", visible=True),
                    gr.update(choices=q['options'], value=None, visible=True, interactive=True)
                ])
            else:
                updates.extend([
                    gr.update(visible=False),
                    gr.update(visible=False)
                ])
        
        # Make sure we have exactly 21 elements (1 status + 1 container + 2*10 questions)
        while len(updates) < 21:
            updates.append(gr.update(visible=False))
        
        return updates
        
    except Exception as e:
        return [f"❌ An error occurred: {str(e)}"] + [gr.update(visible=False)] * 20

def calculate_score(*answers):
    """Calculate the test score based on user answers."""
    global test_questions
    
    if not test_questions:
        return "❌ No test questions available. Please process your skills first."
    
    score = 0
    results = []
    
    for i, user_answer in enumerate(answers):
        if i >= len(test_questions):
            break
        
        q = test_questions[i]
        is_correct = user_answer == q['correct_answer']
        if is_correct:
            score += 1
        
        results.append({
            'question': q['question'],
            'user_answer': user_answer or "Not answered",
            'correct_answer': q['correct_answer'],
            'is_correct': is_correct
        })
    
    total = len(test_questions)
    percentage = (score / total * 100) if total > 0 else 0
    
    result_text = f"""
## Test Results
**Score:** {score}/{total} ({percentage:.1f}%)

### Detailed Results:
"""
    
    for i, result in enumerate(results):
        status = '✅ Correct' if result['is_correct'] else '❌ Incorrect'
        result_text += f"""
**{i+1}. {result['question']}**
- Your answer: {result['user_answer']}
- Correct answer: {result['correct_answer']}
- {status}

"""
    
    return result_text

# Main Gradio interface
with gr.Blocks(title="SkillScope - Skill Assessment Tool") as demo:
    with gr.Tabs() as tabs:
        with gr.TabItem("Skill Extraction") as extraction_tab:
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### Upload your resume or enter skills manually")
                    resume_upload = gr.File(label="Upload Resume (PDF/DOCX)", type="filepath")
                    skills_json = gr.File(label="Upload Skills JSON (Optional)", type="filepath")
                    manual_skills = gr.Textbox(
                        label="Or enter skills manually (comma-separated)",
                        placeholder="e.g., Python, JavaScript, Machine Learning"
                    )
                    submit_btn = gr.Button("Process Skills", variant="primary", elem_id="process_btn")
                
                with gr.Column(scale=3):
                    status_output = gr.Markdown("")
        
        with gr.TabItem("Skill Test") as test_tab:
            with gr.Column():
                test_container = gr.Column(visible=False)
                
                with test_container:
                    gr.Markdown("## Skill Assessment Test")
                    gr.Markdown("Please answer the following questions based on your skills.")
                    
                    # Create 10 question slots
                    question_components = []
                    answer_components = []
                    
                    for i in range(10):
                        with gr.Group(visible=False) as q_group:
                            q_text = gr.Markdown("", visible=False)
                            q_answer = gr.Radio(
                                label="",
                                choices=[],
                                visible=False,
                                interactive=True
                            )
                            question_components.append(q_text)
                            answer_components.append(q_answer)
                    
                    submit_test_btn = gr.Button("Submit Test", variant="primary", visible=False)
                    results_output = gr.Markdown("")
    
    # Collect all outputs for the process_inputs function
    all_outputs = [status_output, test_container, submit_test_btn] + \
                 [comp for pair in zip(question_components, answer_components) for comp in pair]
    
    # Handle skill processing
    submit_btn.click(
        fn=process_inputs,
        inputs=[resume_upload, skills_json, manual_skills],
        outputs=all_outputs
    )
    
    # Handle test submission
    submit_test_btn.click(
        fn=calculate_score,
        inputs=answer_components,
        outputs=results_output
    )

if __name__ == "__main__":
    # Create data directory if it doesn't exist
    os.makedirs("data", exist_ok=True)
    
    # Run the Gradio app on port 7861
    demo.launch(server_name="127.0.0.1", server_port=7861)