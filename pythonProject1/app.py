import os
from urllib.parse import urlencode

from fastapi import FastAPI, Request
from pydantic import BaseModel, ValidationError, Field
from langchain.prompts import PromptTemplate
import requests
import json
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
    service: str = Field(alias="Service")
    specialty: str = Field(alias="Specialty")
    city: Optional[str] = Field(alias="City", default=None)  # Accepts None
    provider_name: Optional[str] = Field(alias="Provider Name", default=None)  # Accepts None


# LangChain prompt template to ask the LLM to process symptoms and return structured data
template = """
You are a medical assistant. A user has provided the following symptoms:

{symptoms}

The possible services are:
[
"MARRIAGE & FAMILY THERAPIST",
"BRIDGES TO HEALTH WAIVER",
"AUDIOLOGIST/HEARING AID",
"CLINICAL PSYCHOLOGIST",
"WAIVER SERVICES",
"MENTAL HEALTH COUNSELORS",
"OPTOMETRIST",
"NURSE MIDWIFE",
"HOSPITAL - INPATIENT",
"SPEECH LANGUAGE PATHOLOGIST",
"LONG TERM HOME HEALTH CARE",
"CERTIFIED HOME HEALTH AGENCY",
"LABORATORY DIRECTOR",
"PERSONAL CARE SERVICES",
"ADULT DAY HEALTH CARE",
"LONG TERM CARE - ORDERED AMB (NO LAB)",
"NURSING HOME",
"SOCIAL CARE NETWORK SERVICE",
"PHYSICIAN GROUP PRACTICE",
"NURSE PRACTITIONER",
"OCCUPATIONAL THERAPIST",
"RESIDENTIAL TREATMENT FACILITY",
"NURSING SERVICES",
"OUTPATIENT CLINIC",
"COMMUNITY SUPPORT (OPWDD)",
"CERTIFIED DIABETES EDUCATOR",
"ASSISTED LIVING PROGRAM",
"CHILD (FOSTER) CARE AGENCIES",
"SUPERVISING PHARMACIST",
"REGISTERED NURSE",
"DOULA (PERINATAL)",
"AMBULANCE",
"PODIATRIST",
"MENTAL HEALTH REHABILITATION",
"OPTICIAN",
"PERSONAL EMERGENCY RESPONSE SERVICE",
"LABORATORY",
"HOSPITAL PHARMACY",
"HOSPICE PROVIDERS",
"NON-MEDICAL TRANSPORTATION",
"LABORATORY CLINIC BASED",
"PHYSICAL THERAPIST",
"OPTICAL ESTABLISHMENT",
"MULTI TYPE GROUP PRACTICE",
"INTERMEDIATE CARE FACILITY (OPWDD)",
"TO BE DETERMINED",
"NATIONAL DIABETES PREVENTION PROGRAM",
"MEDICAL EQUIPMENT SUPPLIERS & DEALER",
"OUTPATIENT",
"PHARMACY",
"OPWDD STATE-OPERATED CLINIC",
"CLINIC PHARMACY",
"LABORATORY HOSPITAL BASED",
"OXYGEN AND RELATED EQUIPMENT DEALER",
"CLINICAL SOCIAL WORKER",
"CASE MANAGEMENT SERVICES",
"SERVICE BUREAU",
"DENTISTS",
"PHYSICIAN ASSISTANT",
"HOME HEALTH CARE",
"HEARING AID",
"CHIROPRACTIC SERVICES",
"DENTAL GROUP PRACTICE",
"EARLY INTERVENTION OR SCHOOL SUPPORTIVE",
"DIETITIANS / NUTRITIONISTS",
"LICENSED BEHAVIOR ANALYST",
"PHYSICIAN",
"AUDIOLOGIST",
"EYE PROSTHESIS FITTER",
"LICENSED PRACTICAL NURSE",
"CERTIFIED ASTHMA EDUCATOR"
]

The possible specialties are:
[PLASTIC SURGERY, DENTAL PUBLIC HEALTH, SPEECH THERAPY, FORENSIC PATHOLOGY, MATERNAL & FETAL MEDICINE, DERMATOPATHOLOGY, PUBLIC HEALTH, GEN PREVENTIVE MEDICINE, METHADONE TREATMENT, OSTEOPATHIC MANIPUL MEDS, FAMILY PRACTICE, NEONATAL PERINATAL MEDS, OBSTETRICS & GYNECOLOGY, RHEUMATOLOGY, EMERGENCY MEDICINE, ORAL SURGEON, PSYCHIATRY (NOT CHILD), ORTHOPEDIC SURGERY, GENERAL SURGERY, GASTROENTEROLOGY, CHILD NEUROLOGY, MEDICALLY FRAGILE CHILDREN AND ADULTS, PRIMARY CARE, ORAL SURGERY, HEMODIALYSIS, ENDODONTIST, INFECTIOUS DISEASES, UROLOGY, PEDIATRICS, PEDIATRIC NEPHROLOGY, PROSTHODONTIST, NEUROLOGY (NOT CHILD), CHEMICAL DEPENDENCY TRMT, CHEMICAL DEPENDENCY REHAB, CERTIFIED DIABETES EDUCATOR, PHYSICAL THERAPY, NEUROLOGICAL SURGERY, MENTAL HLTH SVCS ADULT, PEDIATRIC CARDIOLOGY, MEDICAL MICROBIOLOGY, ONCOLOGY THERAPY, DERMATOLOGY, NUCLEAR MEDICINE, PEDIATRIC PULMONOLOGY, GENERAL DENTISTRY, GYNECOLOGIC ONCOLOGY, AMBULATORY SURGERY, CHEMICAL PATHOLOGY, HEMATOLOGY, CLINICAL PATHOLOGY, NATIONAL DIABETES PREVENTION PROGRAM, ANATOMIC PATHOLOGY, PHYSICAL MEDICINE & REHAB, DIAGNOSTIC RADIOLOGY, ALLERGY & IMMUNOLOGY, MENTAL HLTH SVCS CHILD, COLON & RECTAL SURGERY, PEDIATRIC ENDOCRINOLOGY, CARDIOVASCULAR DISEASE, AIDS DAY HEALTH CARE SERVICES, REPRODUCTIVE ENDOCRINE, ANESTHESIOLOGY, ORTHODONTURE, ENDOCRINOLOGY, CHILD PSYCHIATRY, PULMONARY DISEASES, OCCUPATIONAL THERAPY, ONCOLOGY, FISCAL INTERMEDIARY CDPC, DIAGNOSTIC ROENTGENOLOGY, OCCUPATIONAL MEDICINE, DENTAL CONSCIOUS SEDATION, NEUROPATHOLOGY, PEDIATRIC HEMA/ONCOLOGY, PEDIATRIC SURGERY, DENTAL ANESTHESIOLOGIST, OPHTHALMOLOGY, SCHOOL SUPP HLTH SVC PROG, PSYCHIATRY & NEUROLOGY, MEDICAL GENETICS, PEDIATRIC CRITICAL CARE, GASTROENTOLOGY, PERIODONTIST, MENTAL HLTH SVCS, NEPHROLOGY, THERAPEUTIC RADIOLOGY, CERTIFIED ASTHMA EDUCATOR, EARLY INTERVENTION, PEDODONTIST, THORACIC SURGERY, ANATOMIC & CLINICAL PATH, INTERNAL MEDICINE, OTOLARYNGOLOGY]

You need to extract and return the following information:
1. Service: Based on the symptoms, which area of service does the patient need?
2. Specialty: Will the patient need a specialist to address their symptoms? If so which Specialty?
3. City: If the user mentioned a city, extract it. If the user mentioned a locality, guess the city and extract it. Otherwise default to Buffalo.
4. Provider Name: If the user mentioned a facility or Doctor's name, extract it.
5. Medicaid Coverage: (Select from FFS MCO of OPRA only if specified)

Please return ONLY this information as a JSON object.
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
    ai_response = call_gemini_api(formatted_prompt)

    # Extracting 'text' from the response
    candidates = ai_response.get('candidates', [])
    if candidates and 'content' in candidates[0] and 'parts' in candidates[0]['content']:
        generated_text = candidates[0]['content']['parts'][0].get('text', '')
    else:
        return {"error": "Invalid response structure from API."}

    # Strip the backticks and extract valid JSON content
    try:
        # Remove the backticks and any non-JSON characters
        generated_text = generated_text.replace("```json", "").replace("```", "").strip()

        # print(generated_text)
        # Parse the cleaned JSON
        generated_data = json.loads(generated_text)

        # Use Pydantic to validate and return structured data
        doctor_response = DoctorResponse(**generated_data)

        # Prepare the Registry API call
        params = {
            "$$app_token" : "WejkcY9YZD6Rl4kDF4br66uXx",
            # "profession_or_service": doctor_response.service.upper() if doctor_response.service else "",
            "provider_specialty": doctor_response.specialty.upper() if doctor_response.specialty else "",
            "city": doctor_response.city.upper() if doctor_response.city else "",
            "state": "NY",
            "mmis_name": doctor_response.provider_name.upper() if doctor_response.provider_name else "",
        }
        filtered_params = {k: v for k, v in params.items() if v}
        provider_registry_url = "https://health.data.ny.gov/resource/keti-qx5t.json?" + urlencode(filtered_params)
        if doctor_response.service: # need to do this bc many are just in as PHYSICIAN
            provider_registry_url += f"&$where=profession_or_service in('PHYSICIAN','{doctor_response.service.upper()}')"
        registry_response = requests.get(provider_registry_url)

        print(filtered_params)
        print(len(registry_response.content))

        # Append Registry data to the existing response
        response = {
            "service": doctor_response.service,
            "specialty": doctor_response.specialty,
            "city": doctor_response.city,
            "provider_name": doctor_response.provider_name,
            "registry_data": registry_response.json() if registry_response.status_code == 200 else None
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