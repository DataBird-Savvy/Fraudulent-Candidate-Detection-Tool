import pdfplumber
import docx2txt

from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate

from langchain.output_parsers import PydanticOutputParser
from logger import logger
from exception import ResumeFraudException
from src.structured_data import ResumeData



class ResumeParserLLM:
    def __init__(self, groq_api_key: str, model: str = "llama-3.3-70b-versatile"):
        try:
            self.llm = ChatGroq(groq_api_key=groq_api_key, model=model, temperature=0)
            logger.info("ChatGroq model initialized successfully.")

           
            self.parser = PydanticOutputParser(pydantic_object=ResumeData)

            template = """
            You are a Resume Parser AI.
            Extract the following details from the resume text.

            {format_instructions}

            Resume Text:
            {resume_text}
            """
            self.prompt = PromptTemplate(
                template=template,
                input_variables=["resume_text"],
                partial_variables={"format_instructions": self.parser.get_format_instructions()}
            )

            
            self.chain = self.prompt|self.llm|self.parser
            logger.info("LLMChain and PromptTemplate with OutputParser set up successfully.")

        except Exception as e:
            logger.error(f"Failed to initialize ResumeParserLLM: {e}")
            raise ResumeFraudException("LLM initialization failed.") from e
        
    

    def _extract_text(self, file_path: str) -> str:
        try:
            logger.info(f"Extracting text from file: {file_path}")
            if file_path.endswith(".pdf"):
                text = ""
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text() or ""
                        text += page_text + "\n"
                return text

            elif file_path.endswith(".docx"):
                return docx2txt.process(file_path)

            elif file_path.endswith(".txt"):
                with open(file_path, "r", encoding="utf-8") as f:
                    return f.read()

            else:
                logger.error(f"Unsupported file format: {file_path}")
                raise ResumeFraudException("Unsupported file format. Use PDF, DOCX, or TXT.")

        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {e}")
            raise ResumeFraudException(f"Failed to extract text from {file_path}") from e
        
    

    def parse_resume(self, file_path: str) -> ResumeData:
        try:
            text = self._extract_text(file_path)
            logger.info(f"Text extracted successfully from {file_path}. Parsing resume...")

            # Invoke the chain directly; it will return a ResumeData object already
            resume_data = self.chain.invoke({"resume_text": text})

            # If using invoke, sometimes you get a dict with key 'output'
            if isinstance(resume_data, dict) and "output" in resume_data:
                resume_data = resume_data["output"]

            logger.info(f"Resume parsed successfully for {file_path}")
            return resume_data

        except Exception as e:
            logger.warning(f"LLM returned invalid JSON. Falling back to raw response: {e}")
            return ResumeData(
                name="",
                email="",
                phone="",
                skills=[],
                education=[],
                experience=[]
            )

