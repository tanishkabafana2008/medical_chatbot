import pandas as pd
import markdown

from openai import OpenAI

from config import Config
from medical_search import search_medical_data

client = OpenAI(api_key=Config.OPENAI_API_KEY)

SYSTEM_PROMPT = """
You are MediBot AI, an educational medical information assistant.

Rules:
1. Provide clear, evidence-based health information.
2. Never claim to diagnose diseases.
3. Never prescribe medications or dosages.
4. If symptoms could indicate an emergency (such as severe chest pain,
   difficulty breathing, stroke symptoms, severe allergic reactions),
   advise the user to seek immediate emergency medical care.
5. Use the provided medical database context when it's relevant.
6. Explain things in simple language and use bullet points where helpful.
7. End every response with:

⚠️ Disclaimer:
This information is for educational purposes only and is not a substitute
for professional medical advice, diagnosis, or treatment.
"""

_df = pd.read_csv("dataset.csv")


def search_dataset(question):
    """Simple keyword fallback: look for a disease name mentioned in the question."""
    question_lower = question.lower()

    for _, row in _df.iterrows():
        disease = str(row["Disease"]).lower()
        if disease in question_lower:
            return row

    return None


def _build_context(question):
    # Prefer the semantic (embeddings) search if it's available, since it
    # handles paraphrased questions much better than exact keyword matching.
    semantic_context = search_medical_data(question)
    if semantic_context:
        return semantic_context

    row = search_dataset(question)
    if row is not None:
        return f"""Disease: {row['Disease']}

Symptoms:
{row['Symptoms']}

Causes:
{row['Causes']}

Prevention:
{row['Prevention']}

Treatment:
{row['Treatment']}
"""

    return None


def _format_fallback_answer(question, context=None):
    if context is not None:
        return _format_database_fallback(context)

    return (
        "I’m unable to reach the AI service right now, but I can still share reliable guidance based on the hospital assistant’s education resources.\n\n"
        "- Provide a clear description of your symptoms or the condition you are asking about.\n"
        "- If you experience warning signs such as chest pain, difficulty breathing, severe headache, or sudden weakness, seek emergency care immediately.\n"
        "- Take medicines only as prescribed by your healthcare provider and do not self-adjust doses.\n"
        "- For non-urgent questions, contact your doctor or visit your nearest healthcare center for an accurate diagnosis.\n\n"
        "⚠️ Disclaimer: This information is educational only and is not a substitute for professional medical advice, diagnosis, or treatment."
    )


def _format_database_fallback(context):
    if isinstance(context, str):
        return (
            "I could not reach the AI service, but here is relevant medical information from the hospital reference data:\n\n"
            f"{context}\n\n"
            "⚠️ Disclaimer: This information is educational only and is not a substitute for professional medical advice, diagnosis, or treatment."
        )

    symptoms = [item.strip() for item in str(context['Symptoms']).split(',') if item.strip()]
    causes = [item.strip() for item in str(context['Causes']).split(',') if item.strip()]
    prevention = [item.strip() for item in str(context['Prevention']).split(',') if item.strip()]
    treatment = [item.strip() for item in str(context['Treatment']).split(',') if item.strip()]

    answer = [
        f"I could not reach the AI service, but here is the best available information on {context['Disease']}:",
        "",
        f"**Condition:** {context['Disease']}",
        "",
        "**Common symptoms:**"
    ]

    answer.extend([f"- {item}" for item in symptoms])
    answer.append("")
    answer.append("**Common causes:**")
    answer.extend([f"- {item}" for item in causes])
    answer.append("")
    answer.append("**Prevention advice:**")
    answer.extend([f"- {item}" for item in prevention])
    answer.append("")
    answer.append("**Typical care or treatment:**")
    answer.extend([f"- {item}" for item in treatment])
    answer.append("")
    answer.append(
        "⚠️ Disclaimer: This information is educational only and is not a substitute for professional medical advice, diagnosis, or treatment."
    )

    return "\n".join(answer)


def _is_quota_error(exception):
    text = str(exception).lower()
    return (
        "insufficient_quota" in text
        or "quota" in text
        or "429" in text
        or "rate limit" in text
    )


def get_medical_response(user_message, history=None):
    if history is None:
        history = []

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    context = _build_context(user_message)
    if context:
        messages.append({
            "role": "system",
            "content": "Relevant medical database entry:\n" + context
        })

    messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    try:
        response = client.responses.create(
            model="gpt-5",
            input=messages
        )
        answer = response.output_text
    except Exception as e:
        if _is_quota_error(e):
            return markdown.markdown(_format_fallback_answer(user_message, _build_context(user_message)))

        return f"Sorry, I couldn't process that request right now ({e})."

    return markdown.markdown(answer)
