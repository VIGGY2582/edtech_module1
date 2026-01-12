import os
import json
import pdfplumber
from docx import Document
from rapidfuzz import process, fuzz
from typing import List, Dict, Optional, Union

class InputHandler:
    def __init__(self):
        self.skills_file = os.path.join('data', 'skills_master.json')
        self.output_file = os.path.join('data', 'user_skills.json')
        self.skills = self._load_skills()

    def _load_skills(self) -> List[str]:
        """Load skills from the master skills file."""
        try:
            with open(self.skills_file, 'r') as f:
                data = json.load(f)
                return data.get('skills', [])
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading skills: {e}")
            return []

    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file."""
        try:
            text = []
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text.append(page.extract_text() or "")
            return "\n".join(text)
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            return ""

    def extract_text_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX file."""
        try:
            doc = Document(file_path)
            return "\n".join([paragraph.text for paragraph in doc.paragraphs])
        except Exception as e:
            print(f"Error extracting text from DOCX: {e}")
            return ""

    def extract_skills_from_text(self, text: str) -> List[str]:
        """Extract skills from text using fuzzy matching."""
        if not text or not self.skills:
            return []

        found_skills = set()
        for skill in self.skills:
            # Use partial ratio to find partial matches
            match = process.extractOne(
                skill.lower(),
                [text.lower()],
                scorer=fuzz.partial_ratio,
                score_cutoff=85  # Adjust threshold as needed
            )
            if match and match[1] >= 85:  # If match score is above threshold
                found_skills.add(skill)

        return list(found_skills)

    def process_resume(self, file_path: str) -> List[str]:
        """Process resume file and extract skills."""
        if not file_path:
            return []

        file_ext = os.path.splitext(file_path)[1].lower()
        text = ""
        
        if file_ext == '.pdf':
            text = self.extract_text_from_pdf(file_path)
        elif file_ext in ['.docx', '.doc']:
            text = self.extract_text_from_docx(file_path)
        
        return self.extract_skills_from_text(text)

    def load_skills_from_json(self, file_path: str) -> List[str]:
        """Load skills from a JSON file."""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data.get('skills', data.get('raw_skills', []))
                elif isinstance(data, list):
                    return data
                return []
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading skills from JSON: {e}")
            return []

    def parse_manual_skills(self, text: str) -> List[str]:
        """Parse skills from manual text input."""
        if not text:
            return []
        # Split by commas and clean up the skills
        return [skill.strip() for skill in text.split(',') if skill.strip()]

    def save_skills(self, skills: List[str]) -> bool:
        """Save skills to the output file."""
        try:
            # Ensure the output directory exists
            os.makedirs(os.path.dirname(self.output_file), exist_ok=True)
            
            # Prepare data to save
            data = {"raw_skills": list(set(skills))}  # Remove duplicates
            
            with open(self.output_file, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving skills: {e}")
            return False

    def process_inputs(
        self,
        resume_path: str = "",
        skills_json_path: str = "",
        manual_skills: str = ""
    ) -> Dict[str, Union[bool, List[str]]]:
        """
        Process all input methods and return combined skills.
        
        Args:
            resume_path: Path to resume file (PDF/DOCX)
            skills_json_path: Path to skills JSON file
            manual_skills: Comma-separated list of skills
            
        Returns:
            Dictionary with success status and list of skills
        """
        all_skills = set()
        
        # Process resume if provided
        if resume_path and os.path.exists(resume_path):
            resume_skills = self.process_resume(resume_path)
            all_skills.update(resume_skills)
        
        # Process skills JSON if provided
        if skills_json_path and os.path.exists(skills_json_path):
            json_skills = self.load_skills_from_json(skills_json_path)
            all_skills.update(json_skills)
        
        # Process manual skills if provided
        if manual_skills:
            manual_skills_list = self.parse_manual_skills(manual_skills)
            all_skills.update(manual_skills_list)
        
        # Save the combined skills
        success = self.save_skills(list(all_skills))
        
        return {
            "success": success,
            "skills": list(all_skills)
        }
