from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import tempfile
import os
from typing import Optional


from src.fraud_analyzer import FraudAnalyzerAI
from src.resume_parser import ResumeParserLLM
from src.plagiarism_detector import PlagiarismDetector
from src.education_analyzer import AIEducationValidator
from src.fraud_reporter import FraudReportGenerator
from exception import ResumeFraudException

from logger import logger
from dotenv import load_dotenv
load_dotenv()



groq_api_key = os.getenv("GROQ_API_KEY")  

app = FastAPI()

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    logger.info("Root endpoint accessed.")
    return {"message": "Fraud Detection API Running"}


@app.post("/analyze")
async def analyze_resume(file: UploadFile = File(...), jd: Optional[str] = Form(None)):
    try:
        logger.info(f"Received file: {file.filename}")

        with tempfile.NamedTemporaryFile(delete=False, suffix=file.filename) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        parser = ResumeParserLLM(groq_api_key)
        parsed_data = parser.parse_resume(tmp_path)

        analyzer = FraudAnalyzerAI(parsed_data)
        analysis = analyzer.ai_experience_check()

        validator = AIEducationValidator(parsed_data)
        Education_analysis = validator.validate()

        plagiarism_detector = PlagiarismDetector()
        plagiarism_result_withJD = (
            plagiarism_detector.check_with_jd(tmp_path, jd) if jd else {"message": "No job description provided."}
        )
        plagiarism_result_withcv = plagiarism_detector.check_resume_chunks(tmp_path)

        reporter = FraudReportGenerator()
        report= reporter.generate_report(
            analysis, plagiarism_result_withcv, plagiarism_result_withJD, Education_analysis
        )

        logger.info(f"Fraud report generated successfully.{report}")
        return report

    except ResumeFraudException as e:
        logger.error(str(e))
        raise HTTPException(status_code=400, detail=str(e))