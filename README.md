# Loyalty Competitor Analysis Service

This FastAPI service generates competitor analysis for loyalty programs using OpenAI's GPT-4 model.

## Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/fsilva7456/loyalty-competitor-analysis.git
   cd loyalty-competitor-analysis
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up your OpenAI API key:
   ```bash
   export OPENAI_API_KEY='your-api-key-here'  # On Windows: set OPENAI_API_KEY=your-api-key-here
   ```

## Running the Service

1. Start the server:
   ```bash
   uvicorn main:app --reload
   ```

2. The service will be available at `http://localhost:8000`

## API Documentation

- API documentation is available at `http://localhost:8000/docs`
- OpenAPI specification is available at `http://localhost:8000/openapi.json`

### Generate Analysis Endpoint

`POST /generate`

Example request:
```json
{
  "company_name": "Example Corp",
  "previous_data": {},
  "current_prompt_data": {
    "existing_generated_output": "Previous analysis...",
    "user_feedback": "Focus more on digital loyalty features"
  },
  "other_input_data": {}
}
```

Example response:
```json
{
  "generated_output": "Competitive Analysis for Example Corp...\n\n1. Market Position...\n2. Key Competitors...\n3. Loyalty Program Comparison...",
  "structured_data": {
    "top_competitors": [
      {
        "name": "Competitor A",
        "strengths": [
          "Strong brand recognition",
          "Large customer base"
        ],
        "weaknesses": [
          "Limited digital presence",
          "Outdated loyalty program"
        ],
        "loyalty_program_features": [
          "Points system",
          "Tier-based rewards"
        ]
      }
    ]
  }
}
```

## Key Features

- Uses OpenAI's GPT-4 model for analysis
- Provides both narrative analysis and structured competitor data
- Supports user feedback for refining analysis
- Input validation using Pydantic
- Error handling and API monitoring

## Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key (required)

## Notes

- The service uses GPT-4 by default. You can modify the `model` parameter in `generate_competitor_analysis()` to use a different model.
- The response includes both a detailed text analysis and structured JSON data about competitors.
- The system prompt is designed to provide consistent, structured analysis focusing on loyalty programs.
