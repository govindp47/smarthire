"""
Resume scoring service: Calculate match scores between resumes and jobs.
"""
import logging
from typing import Dict, List, Any

from app.core.config import settings
from app.core import get_openai_client

logger = logging.getLogger(__name__)


class ScoringService:
    """Score resumes based on job requirements."""
    
    def __init__(self):
        """Initialize OpenAI client for embeddings."""
        self.client = get_openai_client()  # Use singleton instance
        self.embedding_model = settings.EMBEDDING_MODEL
    
    async def score_resume(
        self, 
        resume_data: Dict[str, Any],
        job_data: Dict[str, Any]
    ) -> float:
        """
        Calculate overall match score for a resume against a job.
        
        Args:
            resume_data: Parsed resume data (skills, experience, etc.)
            job_data: Job requirements and description
            
        Returns:
            Score from 0-100
        """
        try:
            logger.info("Calculating resume score")
            
            # Extract job requirements
            job_skills = self._extract_skills_from_text(
                f"{job_data.get('requirements', '')} {job_data.get('description', '')}"
            )
            job_experience_level = job_data.get('experience_level', '').lower()
            
            # Extract resume data
            resume_skills = resume_data.get('skills', [])
            resume_experience_years = resume_data.get('total_experience_years', 0)
            
            # Calculate component scores
            skills_score = await self._calculate_skills_score(
                resume_skills, 
                job_skills
            )
            
            experience_score = self._calculate_experience_score(
                resume_experience_years,
                job_experience_level
            )
            
            semantic_score = await self._calculate_semantic_score(
                resume_data,
                job_data
            )
            
            # Weighted average
            weights = {
                'skills': 0.50,      # 50% - Most important
                'experience': 0.25,  # 25% - Important
                'semantic': 0.25     # 25% - Context understanding
            }
            
            overall_score = (
                skills_score * weights['skills'] +
                experience_score * weights['experience'] +
                semantic_score * weights['semantic']
            )
            
            # Round to 1 decimal place
            overall_score = round(overall_score, 1)
            
            logger.info(
                f"Score calculated: {overall_score} "
                f"(skills={skills_score:.1f}, exp={experience_score:.1f}, sem={semantic_score:.1f})"
            )
            
            return overall_score
            
        except Exception as e:
            logger.error(f"Scoring failed: {str(e)}")
            # Return a neutral score on error
            return 50.0
    
    async def _calculate_skills_score(
        self, 
        resume_skills: List[str],
        job_skills: List[str]
    ) -> float:
        """
        Calculate skill match score.
        
        Args:
            resume_skills: Skills from resume
            job_skills: Required skills from job
            
        Returns:
            Score from 0-100
        """
        if not job_skills:
            return 100.0  # If no specific skills required, give full score
        
        if not resume_skills:
            return 0.0
        
        # Normalize skills (lowercase, strip)
        resume_skills_normalized = [s.lower().strip() for s in resume_skills]
        job_skills_normalized = [s.lower().strip() for s in job_skills]
        
        # Exact matches
        exact_matches = sum(
            1 for job_skill in job_skills_normalized 
            if job_skill in resume_skills_normalized
        )
        
        # Partial matches (contains)
        partial_matches = 0
        for job_skill in job_skills_normalized:
            if job_skill not in resume_skills_normalized:
                # Check if job skill is substring of any resume skill
                for resume_skill in resume_skills_normalized:
                    if job_skill in resume_skill or resume_skill in job_skill:
                        partial_matches += 0.5
                        break
        
        total_matches = exact_matches + partial_matches
        match_percentage = (total_matches / len(job_skills_normalized)) * 100
        
        # Cap at 100
        return min(match_percentage, 100.0)
    
    def _calculate_experience_score(
        self,
        resume_years: float,
        job_level: str
    ) -> float:
        """
        Calculate experience level match score.
        
        Args:
            resume_years: Years of experience from resume
            job_level: Experience level required (junior, mid, senior)
            
        Returns:
            Score from 0-100
        """
        # Experience level thresholds
        level_ranges = {
            'entry': (0, 2),
            'junior': (0, 3),
            'mid': (2, 6),
            'middle': (2, 6),
            'senior': (5, 15),
            'lead': (7, 20),
            'principal': (10, 25),
            'staff': (8, 20)
        }
        
        # If no specific level mentioned, use years directly
        if not job_level or job_level not in level_ranges:
            # Score based on having reasonable experience
            if resume_years < 1:
                return 40.0
            elif resume_years <= 3:
                return 70.0
            elif resume_years <= 7:
                return 90.0
            else:
                return 100.0
        
        min_years, max_years = level_ranges[job_level]
        
        # Perfect match: within range
        if min_years <= resume_years <= max_years:
            return 100.0
        
        # Overqualified: more experience than max
        elif resume_years > max_years:
            # Slightly penalize being overqualified
            excess = resume_years - max_years
            penalty = min(excess * 3, 20)  # Max 20 point penalty
            return max(80.0, 100.0 - penalty)
        
        # Underqualified: less experience than min
        else:
            # Calculate how close they are
            if min_years == 0:
                return 80.0  # If min is 0, they're close
            
            percentage = (resume_years / min_years) * 100
            return min(percentage, 80.0)  # Cap at 80 if underqualified
    
    async def _calculate_semantic_score(
        self,
        resume_data: Dict[str, Any],
        job_data: Dict[str, Any]
    ) -> float:
        """
        Calculate semantic similarity using embeddings.
        
        Args:
            resume_data: Resume information
            job_data: Job requirements
            
        Returns:
            Score from 0-100
        """
        try:
            # Create resume summary text
            resume_text = self._create_resume_summary(resume_data)
            
            # Create job requirements text
            job_text = (
                f"{job_data.get('title', '')} "
                f"{job_data.get('description', '')} "
                f"{job_data.get('requirements', '')}"
            )[:1000]  # Limit length
            
            # Get embeddings
            resume_embedding = await self._get_embedding(resume_text)
            job_embedding = await self._get_embedding(job_text)
            
            # Calculate cosine similarity
            similarity = self._cosine_similarity(resume_embedding, job_embedding)
            
            # Convert to 0-100 scale
            # Cosine similarity is -1 to 1, but usually 0 to 1 for text
            # Scale 0.5 (neutral) to 50, 1.0 (perfect) to 100
            score = (similarity * 100)
            
            return max(0.0, min(100.0, score))
            
        except Exception as e:
            logger.warning(f"Semantic scoring failed: {str(e)}")
            return 50.0  # Neutral score on error
    
    def _create_resume_summary(self, resume_data: Dict[str, Any]) -> str:
        """Create a text summary of resume for embedding."""
        parts = []
        
        # Skills
        if resume_data.get('skills'):
            parts.append(f"Skills: {', '.join(resume_data['skills'][:20])}")
        
        # Latest experience
        if resume_data.get('experience'):
            latest = resume_data['experience'][0]
            parts.append(
                f"Current role: {latest.get('title', '')} at {latest.get('company', '')}"
            )
        
        # Summary
        if resume_data.get('summary'):
            parts.append(resume_data['summary'])
        
        return " ".join(parts)[:500]  # Limit length
    
    async def _get_embedding(self, text: str) -> List[float]:
        """Get embedding vector for text."""
        try:
            response = await self.client.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Embedding generation failed: {str(e)}")
            # Return zero vector on error
            return [0.0] * 1536
    
    @staticmethod
    def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        import math
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    @staticmethod
    def _extract_skills_from_text(text: str) -> List[str]:
        """
        Extract potential skills from job description text.
        Simple keyword extraction for common tech skills.
        """
        # Common tech skills (lowercase)
        common_skills = [
            'python', 'java', 'javascript', 'typescript', 'go', 'rust', 'c++', 'c#',
            'react', 'vue', 'angular', 'node', 'fastapi', 'django', 'flask',
            'postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch',
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform',
            'git', 'ci/cd', 'jenkins', 'gitlab', 'github',
            'machine learning', 'deep learning', 'ai', 'nlp',
            'rest api', 'graphql', 'microservices', 'agile', 'scrum'
        ]
        
        text_lower = text.lower()
        found_skills = []
        
        for skill in common_skills:
            if skill in text_lower:
                found_skills.append(skill)
        
        return found_skills


# Global instance
scoring_service = ScoringService()
