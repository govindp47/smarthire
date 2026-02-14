"""
Resume parser service: Extract structured data from resume text using LLM.
"""
import json
import logging
from typing import Dict, Any
from datetime import datetime, timezone

from app.core.config import settings
from app.core import get_openai_client

logger = logging.getLogger(__name__)


class ResumeParserService:
    """Parse resumes using LLM to extract structured data."""
    
    def __init__(self):
        """Initialize OpenAI client."""
        self.client = get_openai_client()  # Use singleton instance
        self.model = settings.OPENAI_MODEL
    
    async def parse_resume(self, resume_text: str) -> Dict[str, Any]:
        """
        Parse resume text and extract structured data.
        
        Args:
            resume_text: Full text extracted from resume
            
        Returns:
            Dictionary with structured resume data
        """
        try:
            logger.info("Starting resume parsing with LLM")
            
            # Create prompt for structured extraction
            prompt = self._create_extraction_prompt(resume_text)
            
            # Call OpenAI API
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert HR assistant that extracts structured information from resumes. Always respond with valid JSON only, no additional text."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,  # Low temperature for consistent extraction
                response_format={"type": "json_object"}
            )
            
            # Parse response
            result = response.choices[0].message.content
            parsed_data = json.loads(result)
            
            # Post-process and validate
            structured_data = self._post_process_data(parsed_data)
            
            logger.info("Resume parsing completed successfully")
            return structured_data
            
        except Exception as e:
            logger.error(f"Resume parsing failed: {str(e)}")
            raise Exception(f"Failed to parse resume: {str(e)}")
    
    def _create_extraction_prompt(self, resume_text: str) -> str:
        """Create prompt for LLM extraction."""
        return f"""Extract the following information from this resume and return it as a JSON object:

RESUME TEXT:
{resume_text[:4000]}  # Limit to avoid token limits

Extract:
1. candidate_name: Full name of the candidate
2. candidate_email: Email address
3. phone: Phone number (if available)
4. skills: List of technical skills, tools, and technologies
5. experience: List of work experiences, each with:
   - title: Job title
   - company: Company name
   - location: Location (city, state/country)
   - start_date: Start date (YYYY-MM format if possible, or text)
   - end_date: End date (YYYY-MM format, or "Present" if current)
   - duration_months: Estimated duration in months
   - description: Brief description of responsibilities
6. education: List of education entries, each with:
   - degree: Degree type (e.g., "Bachelor of Science")
   - field: Field of study (e.g., "Computer Science")
   - institution: School/University name
   - graduation_year: Year of graduation
   - gpa: GPA if mentioned
7. certifications: List of certifications (simple string list)
8. languages: List of languages spoken
9. summary: A 2-3 sentence professional summary

Return ONLY valid JSON with this exact structure:
{{
  "candidate_name": "string",
  "candidate_email": "string",
  "phone": "string or null",
  "skills": ["skill1", "skill2"],
  "experience": [
    {{
      "title": "string",
      "company": "string",
      "location": "string",
      "start_date": "string",
      "end_date": "string",
      "duration_months": number,
      "description": "string"
    }}
  ],
  "education": [
    {{
      "degree": "string",
      "field": "string",
      "institution": "string",
      "graduation_year": number,
      "gpa": number or null
    }}
  ],
  "certifications": ["cert1", "cert2"],
  "languages": ["lang1", "lang2"],
  "summary": "string"
}}

If any field cannot be found, use null or empty array as appropriate."""
    
    def _post_process_data(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Post-process and validate extracted data.
        
        Args:
            parsed_data: Raw data from LLM
            
        Returns:
            Cleaned and validated data
        """
        # Calculate total experience
        total_months = 0
        if parsed_data.get("experience"):
            for exp in parsed_data["experience"]:
                if exp.get("duration_months"):
                    total_months += exp["duration_months"]
        
        total_years = round(total_months / 12, 1) if total_months > 0 else 0
        
        # Ensure all required fields exist
        result = {
            "candidate_name": parsed_data.get("candidate_name"),
            "candidate_email": parsed_data.get("candidate_email"),
            "phone": parsed_data.get("phone"),
            "skills": parsed_data.get("skills", []),
            "experience": parsed_data.get("experience", []),
            "education": parsed_data.get("education", []),
            "certifications": parsed_data.get("certifications", []),
            "languages": parsed_data.get("languages", []),
            "summary": parsed_data.get("summary"),
            "total_experience_years": total_years,
            "metadata": {
                "parsed_at": datetime.now(timezone.utc).isoformat(),
                "parser_model": self.model
            }
        }
        
        return result
    
    async def generate_summary(self, resume_data: Dict[str, Any]) -> str:
        """
        Generate a professional summary from resume data.
        
        Args:
            resume_data: Structured resume data
            
        Returns:
            Generated summary
        """
        try:
            # If summary already exists, return it
            if resume_data.get("summary"):
                return resume_data["summary"]
            
            # Create prompt for summary generation
            prompt = f"""Based on this resume data, write a concise 2-3 sentence professional summary:

Skills: {', '.join(resume_data.get('skills', [])[:10])}
Experience: {resume_data.get('total_experience_years', 0)} years
Latest role: {resume_data.get('experience', [{}])[0].get('title', 'N/A') if resume_data.get('experience') else 'N/A'}

Write a professional summary highlighting key qualifications."""
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional resume writer."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=150
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.warning(f"Summary generation failed: {str(e)}")
            return "Professional with diverse experience and skills."


# Global instance
resume_parser = ResumeParserService()
