import os
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Load Google API key securely from .env file
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("⚠️ ERROR: GEMINI_API_KEY is missing. Make sure to set it in a .env file.")

GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

# Initialize FastAPI App
import logging
from fastapi import FastAPI

logging.basicConfig(level=logging.DEBUG)
app = FastAPI()

@app.get("/")
def home():
    logging.debug("Home endpoint hit!")
    return {"message": "Backend is running!"}

# CORS Middleware (Allows frontend to access the backend)
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (temporary for debugging)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define Request Model
class RequestData(BaseModel):
    answers: dict

@app.get("/")
async def home():
    return {"message": "FastAPI with Gemini API is running!"}

@app.post("/analyze")
async def analyze_data(request: RequestData):
    try:
        print("Received data:", request.answers)  # Debugging

        # Ensure data is not empty
        if not request.answers:
            raise HTTPException(status_code=400, detail="No answers provided!")

        # Construct user query
        user_input = (
            "Based on the user's responses, suggest the best statistical method in one short paragraph. "
            "Then, provide an R code snippet separately without explanation. The response should follow this format strictly:\n\n"
            "**Justification:** [one-paragraph explanation]\n\n"
            "**R Code:**\n```r\n[R code here]\n```"
            "\n\nUser responses:\n" + str(request.answers)
        )

        payload = {
            "contents": [{"parts": [{"text": user_input}]}],
        }

        headers = {
            "Content-Type": "application/json"
        }

        print("Sending request to Gemini API:", payload)  # Debugging

        response = requests.post(GEMINI_API_URL, json=payload, headers=headers)
        result = response.json()

        print("Gemini API Response:", result)  # Debugging

        # Handle API errors
        if "error" in result:
            raise HTTPException(status_code=500, detail=f"Gemini API Error: {result['error']['message']}")

        # Extract response content
        ai_response = result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")

        if not ai_response:
            raise HTTPException(status_code=500, detail="No response received from Gemini API.")

        # Split response into justification and R code
        justification = ""
        r_code = ""

        if "**Justification:**" in ai_response and "**R Code:**" in ai_response:
            parts = ai_response.split("**R Code:**")
            justification = parts[0].replace("**Justification:**", "").strip()
            r_code_section = parts[1].strip()

            # Extract only the R code block
            if "```r" in r_code_section:
                r_code_start = r_code_section.find("```r") + 4
                r_code_end = r_code_section.find("```", r_code_start)
                if r_code_end != -1:
                    r_code = r_code_section[r_code_start:r_code_end].strip()

        # Fallback if extraction fails
        if not justification:
            justification = "Could not extract justification from the response."
        if not r_code:
            r_code = "# Error: Could not extract R code. Try re-running the request."

        return {
            "recommendation": justification,
            "explanation": justification,  # Keeping it simple
            "r_code": f"```r\n{r_code}\n```"
        }

    except Exception as e:
        print("ERROR:", str(e))
        raise HTTPException(status_code=500, detail=str(e))
