import os
import gradio as gr
from modules.input_handler import InputHandler
from modules.skill_normalizer import save_normalized_skills
from modules.profile_summary import save_profile_summary
import json

# Initialize the input handler
input_handler = InputHandler()

def process_inputs(resume_file, skills_json_file, manual_skills):
    """Process all inputs, extract skills, normalize them, and generate summary."""
    try:
        # Process all inputs and extract skills
        result = input_handler.process_inputs(
            resume_path=resume_file.name if resume_file else "",
            skills_json_path=skills_json_file.name if skills_json_file else "",
            manual_skills=manual_skills
        )
        
        if not result["success"] or not result["skills"]:
            return "❌ No skills were extracted. Please check your inputs and try again."
        
        # Get the extracted skills
        skills = result["skills"]
        output = ["✅ Skills extracted and saved!\n"]
        output.extend(f"• {skill}" for skill in sorted(skills))
        
        try:
            # Normalize skills
            norm_result = save_normalized_skills()
            if norm_result.get("normalized_skills"):
                output.append("\n🔄 Skills normalized successfully!")
                
                # Generate profile summary
                summary_result = save_profile_summary()
                if summary_result.get("profile_summary"):
                    output.append("\n\n📝 Profile Summary:")
                    output.append(summary_result["profile_summary"])
                else:
                    output.append("\n⚠️ Could not generate profile summary.")
            else:
                output.append("\n⚠️ Could not normalize skills.")
                
        except Exception as e:
            output.append(f"\n⚠️ An error occurred during processing: {str(e)}")
        
        return "\n".join(output)
        
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
                    extract_btn = gr.Button("Extract Skills & Generate Summary", variant="primary")
            
            with gr.Column():
                output = gr.Textbox(label="Output", lines=15, interactive=False)
        
        # Button action
        extract_btn.click(
            fn=process_inputs,
            inputs=[resume_upload, json_upload, manual_input],
            outputs=output
        )
        
        gr.Markdown("### How to use")
        gr.Markdown("""
        1. Upload your resume (PDF or DOCX) or enter skills manually
        2. Click 'Extract Skills & Generate Summary' to process everything
        3. View your extracted skills and generated profile summary
        """)
    
    return demo

if __name__ == "__main__":
    # Ensure the data directory exists
    os.makedirs("data", exist_ok=True)
    
    # Create and launch the Gradio interface
    demo = create_ui()
    demo.launch(server_name="127.0.0.1", server_port=7860, share=False)
