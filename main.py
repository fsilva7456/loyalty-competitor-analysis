import os
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from openai import OpenAI
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Loyalty Competitor Analysis Service")

# Add CORS middleware with specific patterns for Vercel deployments
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://loyalty-frontend-alpha.vercel.app",  # Production URL
        "http://localhost:5173",  # Local development
        "http://localhost:3000"   # Alternative local port
    ],
    allow_origin_regex=r"https://loyalty-frontend-alpha-[a-z0-9\-]+\.vercel\.app",  # Preview deployments
    allow_credentials=False,  # Set to False since we don't need credentials
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept"],
    expose_headers=["Content-Length"],
    max_age=3600  # Cache preflight requests for 1 hour
)

# Add logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Incoming request: {request.method} {request.url}")
    logger.info(f"Headers: {request.headers}")
    logger.info(f"Origin: {request.headers.get('origin', 'No origin header')}")
    
    # Log the request body for debugging
    body = await request.body()
    if body:
        logger.info(f"Request body: {body.decode()}")
    
    response = await call_next(request)
    
    logger.info(f"Response status: {response.status_code}")
    return response

# Error handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Error processing request: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)}
    )

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class TopCompetitor(BaseModel):
    name: str
    strengths: List[str]
    weaknesses: List[str]
    loyalty_program_features: List[str]

class PreviousData(BaseModel):
    pass

class CurrentPromptData(BaseModel):
    existing_generated_output: str
    user_feedback: str

class CompetitorAnalysisRequest(BaseModel):
    company_name: str
    previous_data: Optional[Dict] = {}
    current_prompt_data: Optional[CurrentPromptData] = None
    other_input_data: Optional[Dict] = {}

class CompetitorAnalysisResponse(BaseModel):
    generated_output: str
    structured_data: Dict

def construct_system_prompt() -> str:
    return """
You are an expert in competitive analysis for loyalty programs. Analyze the provided company 
and its competitors, focusing on their loyalty programs, market positioning, and competitive advantages.

You should:
1. Identify key competitors in the market
2. Analyze their loyalty program features
3. Evaluate strengths and weaknesses
4. Provide actionable insights

Provide your response in two parts:
1. A detailed analysis in natural language
2. A structured JSON object containing key competitors with this exact schema:
{
    "top_competitors": [
        {
            "name": "Competitor Name",
            "strengths": ["strength1", "strength2"],
            "weaknesses": ["weakness1", "weakness2"],
            "loyalty_program_features": ["feature1", "feature2"]
        }
    ]
}

Separate the two parts with [JSON_START] and [JSON_END] markers.
"""

def construct_user_prompt(company_name: str, feedback: str = "") -> str:
    prompt = f"Please analyze the competitors and loyalty programs for {company_name}."
    
    if feedback:
        prompt += f"\n\nIncorporate this feedback in your analysis: {feedback}"
    
    return prompt

def extract_json_from_text(text: str) -> dict:
    try:
        start_marker = "[JSON_START]"
        end_marker = "[JSON_END]"
        json_str = text[text.find(start_marker) + len(start_marker):text.find(end_marker)].strip()
        return json.loads(json_str)
    except Exception as e:
        logger.error(f"Error extracting JSON: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse structured data from response: {str(e)}"
        )

def generate_competitor_analysis(
    company_name: str,
    feedback: str = ""
) -> tuple[str, dict]:
    """Generate competitor analysis using OpenAI's API"""
    try:
        # Create completion using OpenAI
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": construct_system_prompt()},
                {"role": "user", "content": construct_user_prompt(company_name, feedback)}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        # Extract the response text
        full_response = response.choices[0].message.content
        
        # Split into analysis and structured data
        analysis = full_response[:full_response.find("[JSON_START]")].strip()
        structured_data = extract_json_from_text(full_response)
        
        return analysis, structured_data
    except Exception as e:
        logger.error(f"Error generating analysis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate", response_model=CompetitorAnalysisResponse)
async def generate_analysis(request: CompetitorAnalysisRequest):
    logger.info(f"Received analysis request for company: {request.company_name}")
    
    # Extract user feedback if available
    feedback = request.current_prompt_data.user_feedback if request.current_prompt_data else ""
    
    # Generate analysis
    generated_text, structured_data = generate_competitor_analysis(
        request.company_name,
        feedback
    )
    
    # Prepare response
    response = CompetitorAnalysisResponse(
        generated_output=generated_text,
        structured_data=structured_data
    )
    
    logger.info("Successfully generated analysis")
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
