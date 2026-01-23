import os
import gradio as gr
from modules.input_handler import InputHandler
from modules.skill_normalizer import save_normalized_skills
from modules.profile_summary import save_profile_summary
import json

# Initialize the input handler
input_handler = InputHandler()

def process_inputs(resume_file, skills_json_file, manual_skills):
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
                return "✅ Skills extracted and saved!\n\n" + "\n".join(f"• {skill}" for skill in sorted(skills))
            else:
                return "ℹ️ No skills were extracted from the provided inputs."
        else:
            return "❌ Error processing inputs. Please check the file formats and try again."
    except Exception as e:
        return f"❌ An error occurred: {str(e)}"

def normalize_skills():
    """Call the skill normalizer module and return results."""
    try:
        result = save_normalized_skills()
        normalized_skills = result.get("normalized_skills", [])
        if normalized_skills:
            return "✅ Skills normalized successfully!\n\n" + json.dumps(result, indent=2)
        return "⚠️ No skills to normalize. Please extract skills first."
    except Exception as e:
        return f"❌ Error normalizing skills: {str(e)}"

def generate_summary():
    """Call the profile summary module and return results."""
    try:
        result = save_profile_summary()
        summary = result.get("profile_summary", "")
        if summary and not summary.startswith("Candidate profile is currently incomplete"):
            return "✅ Profile summary generated!\n\n" + summary
        return "⚠️ Could not generate summary. Please normalize skills first."
    except Exception as e:
        return f"❌ Error generating profile summary: {str(e)}"

def create_ui():
    """Create the Gradio interface."""
    with gr.Blocks(title="SkillScope - Skill Extractor") as demo:
        gr.Markdown("# 🎯 SkillScope")
        gr.Markdown("Upload your resume, skills JSON, or enter skills manually to extract and save your skills.")
        
        with gr.Row():
            with gr.Column():
                with gr.Group():
                    resume_upload = gr.File(label="📄 Upload Resume (PDF/DOCX)", type="filepath")
                    json_upload = gr.File(label="📁 Upload Skills JSON", type="filepath")
                    manual_input = gr.Textbox(
                        label="✏️ Enter Skills (comma-separated)",
                        placeholder="e.g., Python, JavaScript, Data Analysis"
                    )
                    extract_btn = gr.Button("Extract & Merge Skills", variant="primary")
                
                with gr.Group():
                    normalize_btn = gr.Button("Normalize Skills", variant="secondary")
                    summary_btn = gr.Button("Generate Profile Summary", variant="secondary")
            
            with gr.Column():
                output = gr.Textbox(label="Output", lines=15, interactive=False)
        
        # Button actions
        extract_btn.click(
            fn=process_inputs,
            inputs=[resume_upload, json_upload, manual_input],
            outputs=output
        )
        
        normalize_btn.click(
            fn=normalize_skills,
            inputs=None,
            outputs=output
        )
        
        summary_btn.click(
            fn=generate_summary,
            inputs=None,
            outputs=output
        )
        
        gr.Markdown("### How to use")
        gr.Markdown("""
        1. Upload your resume (PDF or DOCX) or enter skills manually
        2. Click 'Extract & Merge Skills' to process your inputs
        3. Click 'Normalize Skills' to standardize skill names
        4. Click 'Generate Profile Summary' to create a professional summary
        """)
    
    return demo

if __name__ == "__main__":
    # Ensure the data directory exists
    os.makedirs("data", exist_ok=True)
    
    # Create and launch the Gradio interface
    demo = create_ui()
    demo.launch(server_name="127.0.0.1", server_port=7860, share=False)
