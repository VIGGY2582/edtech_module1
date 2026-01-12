import os
import gradio as gr
from modules.input_handler import InputHandler

# Initialize the input handler
input_handler = InputHandler()

def process_inputs(
    resume_file,
    skills_json_file,
    manual_skills
):
    """Process all inputs and return the extracted skills."""
    try:
        # Process all inputs
        result = input_handler.process_inputs(
            resume_path=resume_file.name if resume_file else "",
            skills_json_path=skills_json_file.name if skills_json_file else "",
            manual_skills=manual_skills
        )
        
        if result["success"]:
            skills = result["skills"]
            if skills:
                return "✅ Skills extracted and saved successfully!\n\n" + "\n".join(f"• {skill}" for skill in sorted(skills))
            else:
                return "ℹ️ No skills were extracted from the provided inputs."
        else:
            return "❌ Error processing inputs. Please check the file formats and try again."
    except Exception as e:
        return f"❌ An error occurred: {str(e)}"

def create_ui():
    """Create the Gradio interface."""
    with gr.Blocks(title="SkillScope - Skill Extractor") as demo:
        gr.Markdown("# 🎯 SkillScope")
        gr.Markdown("Upload your resume, skills JSON, or enter skills manually to extract and save your skills.")
        
        with gr.Row():
            with gr.Column():
                resume_upload = gr.File(label="📄 Upload Resume (PDF/DOCX)", type="filepath")
                json_upload = gr.File(label="📁 Upload Skills JSON", type="filepath")
                manual_input = gr.Textbox(
                    label="✏️ Enter Skills (comma-separated)",
                    placeholder="e.g., Python, JavaScript, Data Analysis"
                )
                submit_btn = gr.Button("Extract Skills", variant="primary")
            
            with gr.Column():
                output = gr.Textbox(label="Extracted Skills", lines=10, interactive=False)
        
        submit_btn.click(
            fn=process_inputs,
            inputs=[resume_upload, json_upload, manual_input],
            outputs=output
        )
        
        gr.Markdown("### How to use")
        gr.Markdown("""
        1. Upload your resume (PDF or DOCX) to extract skills automatically
        2. Or upload a JSON file containing your skills
        3. Or type your skills manually, separated by commas
        4. Click 'Extract Skills' to process and save your skills
        """)
    
    return demo

if __name__ == "__main__":
    # Ensure the data directory exists
    os.makedirs("data", exist_ok=True)
    
    # Create and launch the Gradio interface
    demo = create_ui()
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)
