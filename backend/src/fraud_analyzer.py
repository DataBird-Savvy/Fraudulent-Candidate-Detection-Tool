from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import StructuredOutputParser, ResponseSchema
import os
from logger import logger
from exception import ResumeFraudException
from dotenv import load_dotenv
load_dotenv()
import sys

class FraudAnalyzerAI:
    def __init__(self, parsed_data):
        
        self.parsed_data = parsed_data.dict() if hasattr(parsed_data, "dict") else parsed_data

        
        self.llm = ChatGroq(
            temperature=0,
            groq_api_key=os.getenv("GROQ_API_KEY"),
            model="llama-3.1-8b-instant"
        )

        
        self.response_schemas = [
            ResponseSchema(name="status", description="Either 'valid' or 'suspicious'"),
            ResponseSchema(name="reasoning", description="Short explanation of the validation result"),
            ResponseSchema(name="flags", description="List of suspicious issues found in the experience")
        ]
        self.output_parser = StructuredOutputParser.from_response_schemas(self.response_schemas)

        self.prompt = ChatPromptTemplate.from_template("""
        You are a fraud detection assistant.
        Analyze the following job experiences for suspicious patterns:
        {experiences}

        Check for:
        1. Unrealistic career jumps (e.g., Intern → Manager in 6 months).
        2. Very short tenures (< 3 months).
        3. Overlapping jobs (if visible).

        Respond strictly in this JSON format:
        {format_instructions}
        """).partial(format_instructions=self.output_parser.get_format_instructions())

    def ai_experience_check(self):
        """Use Groq LLM to validate career progression."""
        experiences = self.parsed_data.get("experience", [])
        
        if not experiences:
            return {
                "status": "no_experience",
                "message": "Candidate has not listed any prior job experience. Likely a fresher.",
                "flags": []
            }

        try:
            logger.info("Sending experience data to Groq LLM for fraud analysis.")
            chain = self.prompt | self.llm | self.output_parser
            result = chain.invoke({"experiences": experiences})

            
            return result

        except ResumeFraudException:
            raise ResumeFraudException(
            "AI-based experience validation failed.", 
            error_detail=sys
)
