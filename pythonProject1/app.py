import os
from urllib.parse import urlencode

from fastapi import FastAPI, Request
from pydantic import BaseModel, ValidationError, Field
from langchain.prompts import PromptTemplate
import requests
import json
import re
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import HTMLResponse, FileResponse

# FastAPI instance
app = FastAPI(debug=True)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (for production, limit this to specific origins)
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

DEPARTMENT_MAPPING = {
    "Dentistry": "Dentist",
    "Cardiology": "Cardio",
    # Add more mappings as necessary
}

# 1. Get the directory of the current file (app.py)
current_dir = os.path.dirname(os.path.realpath(__file__))

# 2. Define the relative path to the 'static' folder
static_dir = os.path.join(current_dir, 'doctor_finder', 'static')

# 3. Serve static files under a specific path, e.g., '/static'
app.mount("/static", StaticFiles(directory=static_dir, html=True), name="static")

# Google Gemini API URL with API Key
api_key = 'AIzaSyBRlo43ajDPGPc_GxTLoyjnjOSNi2A0ycI'
url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={api_key}'


# Pydantic model for structuring the response
from typing import Optional
from pydantic import BaseModel, Field

class DoctorResponse(BaseModel):
    department: str = Field(alias="Department")
    urgent_case: bool = Field(alias="Urgent Case")
    city: Optional[str] = Field(alias="City", default=None)  # Accepts None
    doc_name: Optional[str] = Field(alias="Doctor Name", default=None)  # Accepts None


# LangChain prompt template to ask the LLM to process symptoms and return structured data
template = """
You are a medical assistant. A user has provided the following symptoms:
{symptoms}
You need to extract and return the following information:
1. Department: Based on the symptoms, which medical department should the patient visit?
2. Urgent Case: Is it urgent? Answer with Yes or No.
3. City: If the user mentioned a city, extract it. If the user mentioned a locality, guess the city and extract it.
4. Doctor Name: If the user mentioned a doctor's name, extract it.

Please return this information as a JSON object.
"""

# Initialize LangChain prompt template
prompt_template = PromptTemplate(
    input_variables=["symptoms"],
    template=template,
)


# Function to call the Google Gemini API
def call_gemini_api(prompt):
    prompt_data = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ]
    }

    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.post(url, headers=headers, data=json.dumps(prompt_data))

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Request failed with status code {response.status_code}: {response.text}")


@app.post("/process/")
async def process_data(request: Request):
    form_data = await request.form()
    symptoms = form_data.get("symptoms")

    # Generate prompt using LangChain's template
    formatted_prompt = prompt_template.format(symptoms=symptoms)

    # Call the Google Gemini API
    api_response = call_gemini_api(formatted_prompt)

    print(api_response)

    # Extracting 'text' from the response
    candidates = api_response.get('candidates', [])
    if candidates and 'content' in candidates[0] and 'parts' in candidates[0]['content']:
        generated_text = candidates[0]['content']['parts'][0].get('text', '')
    else:
        return {"error": "Invalid response structure from API."}

    # Strip the backticks and extract valid JSON content using regex
    try:
        # Use regex to extract the JSON part only (everything between the ```json and ``` markers)
        json_match = re.search(r'```json(.*?)```', generated_text, re.DOTALL)
        if not json_match:
            return {"error": "No valid JSON found in the response."}

        # Extract and clean up the JSON content
        json_content = json_match.group(1).strip()

        # Parse the cleaned JSON
        response_data = json.loads(json_content)

        # Use Pydantic to validate and return structured data
        doctor_response = DoctorResponse(**response_data)

        # Extract necessary parameters for NPI Registry API
        department = doctor_response.department
        
        if department in DEPARTMENT_MAPPING:
            department = DEPARTMENT_MAPPING[department]

        city = doctor_response.city
        first_name = doctor_response.doc_name

        # Prepare the NPI Registry API call
        params = {
            "taxonomy_description": department.lower() if department else "",
            "city": city if city else "",
            "first_name": first_name if first_name else "",
            "version": "2.1"
        }
        filtered_params = {k: v for k, v in params.items() if v}
        npi_registry_url = "https://npiregistry.cms.hhs.gov/api/?" + urlencode(filtered_params)
        print(npi_registry_url)
        npi_response = requests.get(npi_registry_url)


        # Append NPI Registry data to the existing response
        response = {
            "department": department,
            "urgent_case": doctor_response.urgent_case,
            "city": city,
            "doc_name": first_name,
            "npi_registry_data": npi_response.json() if npi_response.status_code == 200 else None
        }

        return response

    except (ValidationError, json.JSONDecodeError) as e:
        return {"error": f"Failed to parse response: {str(e)}"}


@app.post("/calculate-distance/")
async def calculate_distance(request: Request):
    data = await request.json()
    origins = data.get("origins")
    destinations = data.get("destinations")

    if not origins or not destinations:
        return {"error": "Origins and destinations are required."}

    # Call the Distance Matrix API
    distance_matrix_url = f"https://maps.googleapis.com/maps/api/distancematrix/json?units=imperial&origins={origins}&destinations={destinations}&key=AIzaSyBIK25j33Bmu8bGaP0j5Cntk6P6dtYUa-0"
    try:
        response = requests.get(distance_matrix_url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


@app.get("/", response_class=FileResponse)
async def root():
    return FileResponse("doctor_finder/static/index.html")