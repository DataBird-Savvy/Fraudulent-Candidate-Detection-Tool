from typing import Dict, List, Any, Optional
from langchain.prompts import PromptTemplate
from src.structured_data import FraudReport
from langchain.output_parsers import PydanticOutputParser
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os
from logger import logger
from exception import ResumeFraudException


load_dotenv()


class FraudReportGenerator:
    """
    Uses Groq LLM to generate a structured fraud detection report
    combining fraud analysis, plagiarism checks, and education validation.
    """

    def __init__(self):
        try:
            logger.info("Initializing FraudReportGenerator...")

            self.llm = ChatGroq(
                model="openai/gpt-oss-20b",
                groq_api_key=os.getenv("GROQ_API_KEY"),
                temperature=0
            )

            
            self.parser = PydanticOutputParser(pydantic_object=FraudReport)

            format_instructions = self.parser.get_format_instructions()

            template = """
            You are an HR fraud detection assistant. Generate a structured fraud report for a candidate.

            Fraud Analysis:
            {analysis}

            Plagiarism Results (Resume vs Other Resumes):
            {plagiarism_cv}

            Resume vs Job Description Similarity:
            {plagiarism_jd}

            Education Analysis:
            {education_analysis}

            Return the output strictly as JSON:
            {format_instructions}
            """

            self.prompt = PromptTemplate(
                input_variables=["analysis", "plagiarism_cv", "plagiarism_jd", "education_analysis"],
                partial_variables={"format_instructions": format_instructions},
                template=template,
            )
            
            self.chain = self.prompt | self.llm | self.parser
            logger.info("FraudReportGenerator initialized successfully.")

        except Exception as e:
            logger.exception("Failed to initialize FraudReportGenerator.")
            raise ResumeFraudException("Report generation error", error_detail=e)

    def generate_report(
        self,
        analysis: Dict[str, Any],
        plagiarism_cv: List[Dict],
        plagiarism_jd: Dict[str, Any],
        education_analysis: Optional[Dict[str, Any]] = None,
    ) -> FraudReport:
        """Generate an AI-written structured fraud detection report for HR."""
        try:
            logger.info("Starting fraud report generation...")

           

            logger.info(
                f"analysis: {analysis}\n"
                f"plagiarism_cv: {plagiarism_cv}\n"
                f"plagiarism_jd: {plagiarism_jd}\n"
                f"education_analysis: {education_analysis or {}}"
            )

            
            report_structured = self.chain.invoke({
                "analysis": str(analysis),
                "plagiarism_cv": plagiarism_cv,
                "plagiarism_jd": str(plagiarism_jd),
                "education_analysis": str(education_analysis or {}),
            })

            logger.info(f"Fraud report generated successfully. {report_structured}")

            return report_structured

        except Exception as e:
            logger.exception("Failed to generate fraud report.")
            raise ResumeFraudException("Report generation error", error_detail=e)
