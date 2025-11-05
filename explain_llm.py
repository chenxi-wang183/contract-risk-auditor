# explain_llm.py
from openai import OpenAI

def enhance_explanation(api_key, clause_text, risk_text, suggestion_text):
    """
    Produces a concise lawyer-style explanation (B-1).
    """
    client = OpenAI(api_key=api_key)

    prompt = f"""
You are a commercial contracts lawyer. Rewrite the risk explanation and recommendation
below into a concise, formal, and neutral internal legal memo tone. Do not add new facts.

Clause:
\"\"\"{clause_text}\"\"\"

Risk Identified:
{risk_text}

Suggested Revision:
{suggestion_text}

Rewrite in **4–6 sentences**, clear and precise, no emotional language.
Return only the rewritten paragraph.
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1
    )

    return response.choices[0].message.content.strip()