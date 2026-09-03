import os
import json

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

_client = None

def get_client():
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is missing. Check your .env file.")
        _client = genai.Client(api_key=api_key)
    return _client

def get_mime_type(image_path):
    ext = os.path.splitext(image_path)[1].lower()
    if ext == ".png":
        return "image/png"
    elif ext == ".webp":
        return "image/webp"
    return "image/jpeg"

def analyze_complaint_image(image_path):
    client = get_client()
    mime_type = get_mime_type(image_path)

    with open(image_path, "rb") as image_file:
        image_data = image_file.read()

    prompt = """
You are an AI system for a Smart City Complaint Management System.

Analyze the uploaded image and identify whether it contains a
civic infrastructure problem.

Possible issue categories are:

- pothole
- damaged_road
- garbage
- overflowing_bin
- broken_streetlight
- water_leakage
- damaged_traffic_sign
- fallen_tree
- damaged_crosswalk
- other
- no_issue

Return ONLY valid JSON in this format:

{
    "issue": "pothole",
    "severity": "HIGH",
    "department": "Roads Department",
    "description": "A large pothole is visible on the road.",
    "confidence": 0.95
}

Severity must be one of:
LOW, MEDIUM, HIGH

Confidence must be a number between 0 and 1.

If there is no clear civic problem, use:
"issue": "no_issue"
"""


    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=[
            types.Part.from_bytes(
                data=image_data,
                mime_type=mime_type
            ),
            prompt
        ]
    )


    response_text = response.text.strip()

    # Remove markdown code fences if Gemini returns them
    if response_text.startswith("```"):
        response_text = response_text.replace("```json", "")
        response_text = response_text.replace("```", "")
        response_text = response_text.strip()

    try:
        return json.loads(response_text)

    except json.JSONDecodeError:

        return {
            "issue": "unknown",
            "severity": "LOW",
            "department": "Manual Review",
            "description": response_text,
            "confidence": 0
        }