from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from langchain.output_parsers import StructuredOutputParser, ResponseSchema
from logger import logger
from exception import ResumeFraudException
import os
from dotenv import load_dotenv

load_dotenv()


class AIEducationValidator:
    def __init__(self, parsed_data):
        # Accept dict or object with .dict()
        self.parsed_data = parsed_data.dict() if hasattr(parsed_data, "dict") else parsed_data
        self.education_list = self.parsed_data.get("education", [])

        # Init Groq LLM
        self.llm = ChatGroq(
            model="llama-3.1-8b-instant",
            temperature=0,
            groq_api_key=os.getenv("GROQ_API_KEY")
        )

        
        self.response_schemas = [
            ResponseSchema(name="suspicious", description="True if fraud detected, otherwise false"),
            ResponseSchema(name="reasons", description="List of reasons why education is suspicious")
        ]

        self.output_parser = StructuredOutputParser.from_response_schemas(self.response_schemas)

        # Prompt with format instructions
        self.prompt = PromptTemplate(
            input_variables=["education"],
            template="""
You are an expert in detecting fraudulent resumes. Analyze the following education history:

{education}

Check for:
1. Unrealistic degree progression.
2. Suspicious institutions.
3. Overlapping or illogical dates.
4. Degrees completed in unusually short time.

Return your answer in this format:
{format_instructions}
            """,
            partial_variables={"format_instructions": self.output_parser.get_format_instructions()}
        )

        logger.info("AIEducationValidator initialized with structured output parser.")

    def validate(self):
        """Validate education using AI + structured output parsing"""
        try:
            logger.info("Sending education data to LLM for fraud analysis.")
            response = self.llm.invoke(
                self.prompt.format(education=self.education_list)
            )

            logger.debug(f"Raw LLM response: {response.content}")

            # Parse AI output into structured Python dict
            result = self.output_parser.parse(response.content)

            suspicious = result.get("suspicious", False)
            reasons = result.get("reasons", [])

            
            return {"suspicious": suspicious, "reasons": reasons}

        except ResumeFraudException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in AIEducationValidator: {e}")
            raise ResumeFraudException("AI-based education validation failed.")


# Example usage
if __name__ == "__main__":
    sample_resume = {
        "education": [
            {"degree": "Master", "institution": "XYZ Primary School", "start_date": "2022", "end_date": "2023"},
            {"degree": "Bachelor", "institution": "Fake Tech University", "start_date": "2021", "end_date": "2022"}
        ]
    }

    try:
        validator = AIEducationValidator(sample_resume)
        result = validator.validate()
        print("Validation result:", result)
    except ResumeFraudException as e:
        print("Fraud Detected:", str(e))
