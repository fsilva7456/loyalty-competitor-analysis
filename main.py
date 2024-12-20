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

# Add CORS middleware with Vercel domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins temporarily
    allow_credentials=False,  # Set to False since we don't need credentials
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept", "Origin"],
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

# Options endpoint to handle preflight requests explicitly
@app.options("/generate")
async def options_generate():
    return {}

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

@app.post("/generate", response_model=CompetitorAnalysisResponse)
async def generate_analysis(request: CompetitorAnalysisRequest):
    logger.info(f"Received analysis request for company: {request.company_name}")
    
    # Extract user feedback if available
    feedback = request.current_prompt_data.user_feedback if request.current_prompt_data else ""
    
    # Generate analysis using OpenAI
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": """You are an expert in competitive analysis for loyalty programs. Analyze the competitors 
                    and provide insights about their loyalty programs, focusing on strengths, weaknesses, and key features."""
                },
                {
                    "role": "user",
                    "content": f"Analyze competitors and loyalty programs for {request.company_name}." +
                              (f"\n\nConsider this feedback: {feedback}" if feedback else "")
                }
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        # Extract the response text
        full_response = response.choices[0].message.content
        
        # Mock structured data for now
        structured_data = {
            "top_competitors": [
                {
                    "name": "Competitor A",
                    "strengths": ["Market leadership", "Digital integration"],
                    "weaknesses": ["Complex redemption", "Limited personalization"],
                    "loyalty_program_features": ["Points system", "Mobile app"]
                }
            ]
        }
        
        return CompetitorAnalysisResponse(
            generated_output=full_response,
            structured_data=structured_data
        )
        
    except Exception as e:
        logger.error(f"Error generating analysis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
