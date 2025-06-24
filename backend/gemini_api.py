import os
from google import genai
from google.genai import types

def build_gemini_prompt(essay, rubric, extra_instructions):
    prompt = f"""
You are a highly skilled and fair essay evaluator for high school and college-level writing. Your job is to:

1. Analyze the given student essay thoroughly.
2. Score it using the provided rubric and grading system.
3. Provide detailed, specific feedback that quotes exact sentences/phrases from the essay and gives targeted advice.
4. Follow any extra grading instructions provided.

Essay:
{essay}

Rubric:
{rubric}

Additional Instructions:
{extra_instructions if extra_instructions.strip() else 'none'}

IMPORTANT: Your response must include:
1. Overall Grade: Use the appropriate scoring system based on the rubric
2. Detailed Specific Feedback: Quote specific sentences/phrases from the essay and provide targeted feedback for each. Structure your feedback in this exact format:

**INTRODUCTION ANALYSIS**
[Quote specific sentences from the introduction and provide feedback]

**BODY PARAGRAPHS ANALYSIS**
[Quote specific sentences from each body paragraph and provide feedback]

**CONCLUSION ANALYSIS**
[Quote specific sentences from the conclusion and provide feedback]

**OVERALL STRENGTHS**
[Quote specific examples of what was done well]

**AREAS FOR IMPROVEMENT**
[Quote specific examples and provide concrete suggestions]

**SPECIFIC RECOMMENDATIONS**
[Provide actionable advice with references to exact parts of the essay]

Be thorough, specific, and constructive in your feedback. Always quote the exact text you're referring to when giving feedback. Return your feedback in markdown format.

CRITICAL: Keep your response concise and to the point. Avoid unnecessary verbosity and lengthy explanations. Focus on the most important feedback points and be direct in your analysis.
"""
    return prompt

def get_gemini_response(prompt):
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables")
    client = genai.Client(api_key=api_key)
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=prompt),
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(
            thinking_budget=-1,
        ),
        response_mime_type="application/json",
        response_schema=genai.types.Schema(
            type=genai.types.Type.OBJECT,
            required=["overall_grade", "detailed_specific_feedback"],
            properties={
                "overall_grade": genai.types.Schema(
                    type=genai.types.Type.STRING,
                    description="The overall grade/score for the essay based on the rubric"
                ),
                "detailed_specific_feedback": genai.types.Schema(
                    type=genai.types.Type.STRING,
                    description="Detailed feedback that quotes specific parts of the essay and provides targeted advice"
                ),
            },
        ),
    )
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=contents,
        config=generate_content_config,
    )
    return response.text 