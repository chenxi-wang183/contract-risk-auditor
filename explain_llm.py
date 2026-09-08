
# explain_llm.py
from openai import OpenAI
 
 
def enhance_explanation(api_key, clause_text, risk_text, suggestion_text,
                        api_base=None, model="gpt-4o-mini"):
    """Rewrite a rule-engine finding in internal-memo tone.
 
    api_base lets this run against any OpenAI-compatible endpoint (Zhipu, Gemini,
    OpenAI). If the call fails, the original rule-engine text is returned unchanged
    so one bad request never takes down a whole document review.
    """
    prompt = f"""
You are a commercial contracts lawyer. Rewrite the risk explanation and recommendation
below into a concise, formal, and neutral internal legal memo tone. Do not add new facts.
 
Clause:
\"\"\"{clause_text}\"\"\"
 
Risk Identified:
{risk_text}
 
Suggested Revision:
{suggestion_text}
 
Rewrite in 4-6 sentences, clear and precise, no emotional language.
Return only the rewritten paragraph.
"""
 
    try:
        client = OpenAI(api_key=api_key, base_url=api_base) if api_base else OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            timeout=60,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return risk_text
 









