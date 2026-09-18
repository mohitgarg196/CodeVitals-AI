import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai.errors import ServerError

from .analyzer import AnalysisReport


load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


MODEL_NAME = "gemini-3.6-flash"
MAX_ATTEMPTS = 3


SYSTEM_PROMPT = """
You are SecureOpt, a senior software security
and performance engineer.

Analyze the provided software repository.

Identify:

1. Security vulnerabilities
2. Performance bottlenecks
3. Database inefficiencies
4. Important engineering optimization opportunities

Focus on concrete, evidence-based findings.

Do not report speculative issues without sufficient
evidence from the provided code.

For each finding provide:

- category
- severity
- file
- line
- title
- description
- recommendation
"""


def analyze_with_llm(repository: str):

    prompt = f"""
Analyze the following software repository.

Return only findings that have reasonable evidence
in the provided source code.

Repository:

{repository}
"""

    for attempt in range(MAX_ATTEMPTS):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=[
                    SYSTEM_PROMPT,
                    prompt,
                ],
                config={
                    "response_mime_type": "application/json",
                    "response_schema": AnalysisReport,
                },
            )
            break
        except ServerError:
            if attempt == MAX_ATTEMPTS - 1:
                raise
            time.sleep(2 ** attempt)

    return response.parsed, response