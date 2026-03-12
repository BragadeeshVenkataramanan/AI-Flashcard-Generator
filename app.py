from flask import Flask, render_template, request, send_file, jsonify, Response
import os
from io import BytesIO, StringIO
import csv
import random

# Providers
import ollama
import google.generativeai as genai

# ---------- Config ----------
GEMINI_API_KEY = "AIzaSyCJFDxtkwi43ds7j0qoG7E_slu6LoNQTa0"
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

app = Flask(__name__)
app.config["MAX_FLASHCARDS"] = int(os.getenv("MAX_FLASHCARDS", "30"))
app.config["DEFAULT_OLLAMA_MODEL"] = os.getenv("DEFAULT_OLLAMA_MODEL", "mistral")
app.config["DEFAULT_GEMINI_MODEL"] = os.getenv("DEFAULT_GEMINI_MODEL", "models/gemini-pro")


# ---------- Helpers ----------
def build_prompt(topic: str, count: int, style: str) -> str:
    style_hint = {
        "standard": "standard Q/A",
        "definition": "concise definition-based",
        "truefalse": "True/False with a brief explanation in the answer",
        "mcq": "multiple-choice (one correct option) with the correct choice explained in the answer",
    }.get(style, "standard Q/A")

    return f"""You are a flashcard writer.
Write {count} {style_hint} flashcards about: "{topic}".
Format STRICTLY:
Q: <question text>
A: <answer text>
(Repeat for each card.)
"""


def parse_flashcards(raw):
    import re
    raw = re.sub(r"\d+\.\s*Q:", "\nQ:", raw)
    raw = re.sub(r"\s*A:", "\nA:", raw)

    cards = []
    q, a = None, None
    for line in raw.splitlines():
        s = line.strip()
        if s.lower().startswith("q:"):
            if q and a:
                cards.append({"question": q, "answer": a})
            q, a = s[2:].strip(), None
        elif s.lower().startswith("a:"):
            a = s[2:].strip()
    if q and a:
        cards.append({"question": q, "answer": a})

    return cards


def generate_with_ollama(topic: str, count: int, style: str):
    prompt = build_prompt(topic, count, style)
    resp = ollama.chat(
        model=app.config["DEFAULT_OLLAMA_MODEL"],
        messages=[{"role": "user", "content": prompt}],
    )
    raw = resp.get("message", {}).get("content", "")
    items = parse_flashcards(raw)
    return items[:count]


def generate_with_gemini(topic, count, style):
    prompt = build_prompt(topic, count, style)
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        raw = str(response.text or "")
        return parse_flashcards(raw)
    except Exception as e:
        return [{"question": "Gemini Error", "answer": str(e)}]


# ---------- Routes ----------
@app.route("/", methods=["GET", "POST"])
def index():
    cards = []
    error = None

    if request.method == "POST":
        topic = request.form.get("topic", "").strip()
        provider = request.form.get("provider", "ollama")
        style = request.form.get("style", "standard")
        try:
            count = int(request.form.get("count", "5"))
        except ValueError:
            count = 5
        count = max(1, min(count, app.config["MAX_FLASHCARDS"]))

        if not topic:
            error = "Please enter a topic."
        else:
            try:
                if provider == "gemini":
                    cards = generate_with_gemini(topic, count, style)
                else:
                    cards = generate_with_ollama(topic, count, style)
            except Exception as e:
                error = str(e)

    return render_template("index.html", cards=cards, error=error)


# ---------- QUIZ DATA ----------
@app.get("/quiz_data")
def quiz_data():

    cards = request.args.get("cards")

    import json
    cards = json.loads(cards)

    quiz = []

    for c in cards[:10]:

        correct = c["answer"]

        wrong = [x["answer"] for x in cards if x["answer"] != correct]

        random.shuffle(wrong)

        options = wrong[:3] + [correct]

        random.shuffle(options)

        quiz.append({
            "question": c["question"],
            "options": options,
            "answer": correct
        })

    return jsonify(quiz)


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
