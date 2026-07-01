"""
╔══════════════════════════════════════════════════════════════════════════════╗
║            NutriAgent AI — IBM Watsonx.ai Powered Nutrition Agent           ║
║                      Flask Backend  |  app.py                               ║
╚══════════════════════════════════════════════════════════════════════════════╝

AGENT_INSTRUCTIONS
==================
Customize every aspect of the agent behavior below.  No other file needs
to be touched for personality / diet changes.

  AGENT_PERSONA          – Name, role, and short description shown to the model
  AGENT_TONE             – Communication style (friendly, clinical, motivational…)
  AGENT_DIET_FOCUS       – Default diet specialisation (Indian vegetarian, keto…)
  AGENT_LANGUAGE_STYLE   – Language register (simple, technical, bilingual…)
  AGENT_SAFETY_RULES     – Hard guardrails the model must always follow
  AGENT_INDIAN_FOOD      – Deep Indian food knowledge injected into every prompt
  AGENT_RESPONSE_FORMAT  – How answers should be structured
  AGENT_GREETING         – First message shown in the chat UI
  MODEL_ID               – Watsonx.ai Granite model to use
  GENERATION_PARAMS      – LLM generation hyper-parameters
"""

import os
import json
import re
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
from dotenv import load_dotenv

# ─── IBM Watsonx.ai SDK ───────────────────────────────────────────────────────
try:
    from ibm_watsonx_ai.foundation_models import ModelInference
    WATSONX_AVAILABLE = True
except ImportError:
    WATSONX_AVAILABLE = False

# ─── Load environment ─────────────────────────────────────────────────────────
load_dotenv()

# ══════════════════════════════════════════════════════════════════════════════
#                         AGENT INSTRUCTIONS
#  Edit the values below to fully customise the agent without touching any
#  other part of the code.
# ══════════════════════════════════════════════════════════════════════════════

AGENT_PERSONA = """
You are NutriAgent AI, an expert nutritionist and dietitian powered by IBM Watsonx.ai.
You specialize in personalized nutrition planning, healthy meal suggestions, calorie analysis,
and family diet recommendations. You have deep knowledge of both modern nutritional science
and traditional dietary systems, especially Indian cuisine.
"""

AGENT_TONE = """
Be warm, encouraging, and supportive. Use a friendly yet professional tone.
Celebrate small wins, motivate healthy habits, and never make the user feel guilty.
Use clear, jargon-free language. Occasionally use light positivity like "Great choice!" 
or "You're on the right track!" to keep the user motivated.
"""

AGENT_DIET_FOCUS = """
Primary focus: Indian vegetarian and balanced omnivore diets.
Secondary expertise: Mediterranean, DASH, diabetic-friendly, weight-loss, and muscle-gain diets.
Always consider cultural food preferences and local ingredient availability (India-centric).
Prioritize whole foods, seasonal produce, and traditional cooking methods.
"""

AGENT_LANGUAGE_STYLE = """
Use simple, conversational English. Structure responses with clear headings and bullet points.
For Indian users, feel free to reference food names in both English and Hindi/regional names
(e.g., "Moong Dal / Split Green Gram").
Keep responses concise but complete — aim for 150–400 words per reply.
"""

AGENT_SAFETY_RULES = """
CRITICAL SAFETY RULES — ALWAYS FOLLOW:
1. NEVER provide specific medical diagnoses or replace professional medical advice.
2. NEVER recommend extreme calorie restriction below 1200 kcal/day for adults without noting medical supervision is required.
3. ALWAYS recommend consulting a doctor or registered dietitian for medical conditions (diabetes, hypertension, kidney disease, eating disorders, pregnancy).
4. NEVER suggest unsafe supplements, unproven detox protocols, or fad diets without evidence.
5. For children under 12, ALWAYS recommend pediatrician consultation before diet changes.
6. If a user expresses signs of an eating disorder, respond with empathy and encourage professional help.
7. Disclose that you are an AI assistant, not a licensed professional, when discussing medical conditions.
"""

AGENT_INDIAN_FOOD = """
INDIAN FOOD KNOWLEDGE BASE:
- Grains: Rice (Basmati, Brown, Parboiled), Wheat (Chapati/Roti), Jowar, Bajra, Ragi, Quinoa
- Lentils & Legumes: Moong Dal, Masoor Dal, Toor Dal, Chana Dal, Rajma, Chole, Urad Dal
- Vegetables: Spinach (Palak), Fenugreek (Methi), Drumstick (Moringa), Bitter Gourd (Karela), Ridge Gourd, Bottle Gourd (Lauki)
- Dairy: Paneer, Curd/Dahi, Buttermilk (Chaas), Ghee (clarified butter — use in moderation)
- Spices with health benefits: Turmeric (anti-inflammatory), Cumin (digestion), Fenugreek (blood sugar), Ginger (immunity), Cardamom (metabolism)
- Healthy Indian meals: Idli-Sambar, Poha, Upma, Dal-Roti, Khichdi, Rajma-Rice, Paneer Bhurji with whole wheat roti
- Regional specialties: South Indian (fermented foods, coconut), North Indian (dairy, wheat), East Indian (fish, mustard), West Indian (millets, groundnuts)
- Festive & fasting foods: Sabudana Khichdi, Kuttu Atta Roti, Makhana (fox nuts), Singhara
- Street food makeovers: Healthy Chaat with sprouts, baked Samosa, Dahi Puri with low-fat curd
"""

AGENT_RESPONSE_FORMAT = """
Structure your responses as follows:
- Use **bold** for section headings
- Use bullet points (•) for lists
- Include specific food items with approximate calories when relevant
- For meal plans, use a clear Day/Meal structure
- End with a motivating tip or reminder
- Keep total response under 500 words unless a detailed meal plan is requested
"""

AGENT_GREETING = (
    "👋 Hello! I'm **NutriAgent AI**, your personal nutrition expert powered by IBM Watsonx.ai. "
    "I can help you with personalized meal plans, calorie tracking, healthy recipes, BMI analysis, "
    "and family nutrition guidance — with a special focus on Indian dietary preferences. "
    "What would you like help with today?"
)

# ─── Model Configuration ──────────────────────────────────────────────────────
MODEL_ID = "meta-llama/llama-3-3-70b-instruct"  # Best available in Sydney (au-syd) region
# Other available models in au-syd:
#   "ibm/granite-3-1-8b-base"            -- IBM Granite base (faster)
#   "meta-llama/llama-3-1-8b"            -- Llama 3.1 8B (lightweight)
#   "meta-llama/llama-3-1-70b-gptq"      -- Llama 3.1 70B GPTQ (quantized)

GENERATION_PARAMS = {
    "max_new_tokens": 1024,
    "min_new_tokens": 50,
    "temperature": 0.7,          # 0.3 = more factual, 0.9 = more creative
    "top_p": 0.9,
    "top_k": 50,
    "repetition_penalty": 1.1,
    "stop_sequences": ["Human:", "User:", "\n\nHuman"],
}

# ══════════════════════════════════════════════════════════════════════════════
#                         END OF AGENT INSTRUCTIONS
# ══════════════════════════════════════════════════════════════════════════════

# ─── Flask App ────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "nutriagent-secret-2024")
CORS(app)

# ─── Build System Prompt ──────────────────────────────────────────────────────
SYSTEM_PROMPT = f"""
{AGENT_PERSONA.strip()}

COMMUNICATION STYLE:
{AGENT_TONE.strip()}

DIET SPECIALIZATION:
{AGENT_DIET_FOCUS.strip()}

LANGUAGE & FORMAT:
{AGENT_LANGUAGE_STYLE.strip()}
{AGENT_RESPONSE_FORMAT.strip()}

INDIAN FOOD KNOWLEDGE:
{AGENT_INDIAN_FOOD.strip()}

{AGENT_SAFETY_RULES.strip()}
""".strip()


# ─── Watsonx.ai Client ────────────────────────────────────────────────────────

# Valid IBM Cloud SaaS region URLs — the SDK identifies Cloud vs CPD by this URL.
# If the URL does NOT contain "ml.cloud.ibm.com" the SDK assumes Cloud Pak for
# Data (on-premise) and requires a `version` key — causing the error you saw.
_REGION_URLS = {
    "us-south": "https://us-south.ml.cloud.ibm.com",
    "eu-de":    "https://eu-de.ml.cloud.ibm.com",
    "eu-gb":    "https://eu-gb.ml.cloud.ibm.com",
    "jp-tok":   "https://jp-tok.ml.cloud.ibm.com",
    "au-syd":   "https://au-syd.ml.cloud.ibm.com",
}

def get_watsonx_model():
    """Initialise and return IBM Watsonx.ai ModelInference client."""
    if not WATSONX_AVAILABLE:
        raise RuntimeError("ibm-watsonx-ai package not installed.")

    api_key    = os.getenv("IBM_API_KEY", "").strip()
    project_id = os.getenv("IBM_PROJECT_ID", "").strip()
    url        = os.getenv("IBM_WATSONX_URL", "https://au-syd.ml.cloud.ibm.com").strip()

    if not api_key:
        raise RuntimeError("IBM_API_KEY is missing or empty in .env")
    if not project_id:
        raise RuntimeError("IBM_PROJECT_ID is missing or empty in .env")

    # Ensure URL is IBM Cloud SaaS format (not CPD).
    # CPD URLs look like https://cpd-xxxx.apps.xxx.com — they lack "ml.cloud.ibm.com"
    if "ml.cloud.ibm.com" not in url:
        raise RuntimeError(
            f"IBM_WATSONX_URL looks like a Cloud Pak for Data URL: '{url}'\n"
            f"For IBM Cloud (SaaS) use one of: {list(_REGION_URLS.values())}"
        )

    # Pass credentials as a plain dict — works with ibm-watsonx-ai 1.x and 1.5+
    # The SDK checks for "url" containing "ml.cloud.ibm.com" to detect IBM Cloud SaaS.
    credentials = {
        "url":     url,
        "apikey":  api_key,
    }
    model = ModelInference(
        model_id=MODEL_ID,
        credentials=credentials,
        project_id=project_id,
        params=GENERATION_PARAMS,
    )
    return model


def build_conversation_prompt(messages: list, user_context: dict) -> str:
    """
    Convert chat history + optional user context into a single prompt string
    compatible with Granite instruct models.
    """
    context_block = ""
    if user_context:
        parts = []
        if user_context.get("name"):
            parts.append(f"User's name: {user_context['name']}")
        if user_context.get("age"):
            parts.append(f"Age: {user_context['age']} years")
        if user_context.get("weight"):
            parts.append(f"Weight: {user_context['weight']} kg")
        if user_context.get("height"):
            parts.append(f"Height: {user_context['height']} cm")
        if user_context.get("goal"):
            parts.append(f"Health goal: {user_context['goal']}")
        if user_context.get("diet_type"):
            parts.append(f"Diet preference: {user_context['diet_type']}")
        if user_context.get("allergies"):
            parts.append(f"Allergies/restrictions: {user_context['allergies']}")
        if user_context.get("medical"):
            parts.append(f"Medical conditions: {user_context['medical']}")
        if parts:
            context_block = "USER PROFILE:\n" + "\n".join(parts) + "\n\n"

    prompt = f"<|system|>\n{SYSTEM_PROMPT}\n\n{context_block}<|end|>\n"
    for msg in messages[-12:]:          # keep last 12 turns to stay within context window
        role    = msg.get("role", "user")
        content = msg.get("content", "")
        if role == "user":
            prompt += f"<|user|>\n{content}\n<|end|>\n"
        else:
            prompt += f"<|assistant|>\n{content}\n<|end|>\n"
    prompt += "<|assistant|>\n"
    return prompt


def call_watsonx(messages: list, user_context: dict) -> str:
    """Call Watsonx.ai and return the generated text."""
    import warnings
    try:
        model  = get_watsonx_model()
        prompt = build_conversation_prompt(messages, user_context)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            result = model.generate_text(prompt=prompt)
        return result.strip() if isinstance(result, str) else result
    except Exception as exc:
        return f"⚠️ I'm having trouble connecting to the AI service right now. Error: {str(exc)}"


# ─── Nutrition Helpers ────────────────────────────────────────────────────────
def calculate_bmi(weight_kg: float, height_cm: float) -> dict:
    """Return BMI value, category, and ideal weight range."""
    if height_cm <= 0 or weight_kg <= 0:
        return {"error": "Invalid values"}
    h_m   = height_cm / 100
    bmi   = round(weight_kg / (h_m ** 2), 1)
    ideal_low  = round(18.5 * (h_m ** 2), 1)
    ideal_high = round(24.9 * (h_m ** 2), 1)
    if bmi < 18.5:
        category, color = "Underweight", "#f59e0b"
    elif bmi < 25:
        category, color = "Normal weight", "#10b981"
    elif bmi < 30:
        category, color = "Overweight", "#f97316"
    else:
        category, color = "Obese", "#ef4444"
    return {
        "bmi": bmi,
        "category": category,
        "color": color,
        "ideal_low": ideal_low,
        "ideal_high": ideal_high,
    }


def calculate_tdee(weight_kg: float, height_cm: float, age: int,
                   gender: str, activity: str) -> dict:
    """Calculate BMR (Mifflin-St Jeor) and TDEE."""
    if gender.lower() in ("male", "m"):
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    else:
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161
    activity_map = {
        "sedentary":     1.2,
        "light":         1.375,
        "moderate":      1.55,
        "active":        1.725,
        "very_active":   1.9,
    }
    factor = activity_map.get(activity.lower(), 1.55)
    tdee   = round(bmr * factor)
    return {
        "bmr":  round(bmr),
        "tdee": tdee,
        "weight_loss":   tdee - 500,
        "weight_gain":   tdee + 500,
        "maintenance":   tdee,
    }


SAMPLE_MEAL_PLANS = {
    "vegetarian": {
        "breakfast": ["Oats porridge with banana & almonds (~320 kcal)",
                      "Masala Dosa with Sambar (~280 kcal)",
                      "Vegetable Poha with peanuts (~250 kcal)"],
        "lunch":     ["Dal Tadka + Brown Rice + Salad (~450 kcal)",
                      "Rajma Chawal + Raita (~480 kcal)",
                      "Palak Paneer + 2 Whole Wheat Roti (~420 kcal)"],
        "dinner":    ["Moong Dal Khichdi + Dahi (~380 kcal)",
                      "Mixed Veg Curry + 2 Roti (~360 kcal)",
                      "Tofu Stir-fry + Quinoa (~400 kcal)"],
        "snacks":    ["Masala Chana (~150 kcal)",
                      "Fruit Chaat (~120 kcal)",
                      "Makhana (Fox Nuts) handful (~100 kcal)"],
    },
    "non_vegetarian": {
        "breakfast": ["Egg Bhurji + 2 Whole Wheat Toast (~350 kcal)",
                      "Chicken Poha (~300 kcal)",
                      "Omelette + Brown Bread (~320 kcal)"],
        "lunch":     ["Chicken Curry + Brown Rice + Salad (~520 kcal)",
                      "Fish Curry + 2 Roti + Dal (~490 kcal)",
                      "Egg Curry + Rice + Raita (~480 kcal)"],
        "dinner":    ["Grilled Chicken + Salad + Roti (~450 kcal)",
                      "Fish Tikka + Dal + Vegetables (~430 kcal)",
                      "Chicken Soup + Whole Wheat Bread (~380 kcal)"],
        "snacks":    ["Boiled Egg (~78 kcal)",
                      "Chicken Sandwich (~200 kcal)",
                      "Mixed Nuts (~180 kcal)"],
    },
}

NUTRITION_TIPS = [
    "💧 Drink 8–10 glasses of water daily. Hydration boosts metabolism by up to 30%.",
    "🌅 Eat breakfast within 1 hour of waking to kickstart your metabolism.",
    "🥗 Fill half your plate with colorful vegetables at every meal.",
    "🕐 Eat every 3–4 hours to maintain stable blood sugar levels.",
    "🌙 Avoid heavy meals 2–3 hours before bedtime for better digestion.",
    "🧂 Reduce processed foods and hidden sodium — cook at home more often.",
    "🫘 Include a protein source at every meal to stay fuller longer.",
    "🏃 Pair good nutrition with at least 30 minutes of physical activity daily.",
    "📊 Track your meals for 2 weeks — awareness alone improves eating habits.",
    "🥜 Healthy fats (nuts, seeds, avocado, ghee in moderation) are essential — don't fear them.",
]

FOOD_CALORIES = {
    "1 medium apple": 95, "1 banana": 105, "1 cup rice (cooked)": 206,
    "1 whole wheat roti": 120, "1 cup dal (cooked)": 180, "100g chicken breast": 165,
    "1 cup whole milk": 149, "100g paneer": 265, "1 egg": 78,
    "1 cup oats": 307, "1 tbsp ghee": 112, "1 cup curd (dahi)": 100,
    "1 medium potato (boiled)": 130, "1 cup spinach (raw)": 7,
    "100g salmon": 208, "1 cup lentils (cooked)": 230,
    "1 tbsp peanut butter": 94, "1 cup brown rice (cooked)": 216,
    "100g tofu": 76, "1 cup moong sprouts": 31,
}


# ─── Flask Routes ─────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html", greeting=AGENT_GREETING)


@app.route("/api/chat", methods=["POST"])
def chat():
    data         = request.get_json(force=True)
    user_message = data.get("message", "").strip()
    messages     = data.get("messages", [])
    user_context = data.get("user_context", {})

    if not user_message:
        return jsonify({"error": "Empty message"}), 400

    messages.append({"role": "user", "content": user_message})
    reply = call_watsonx(messages, user_context)
    messages.append({"role": "assistant", "content": reply})

    return jsonify({
        "reply":    reply,
        "messages": messages,
        "timestamp": datetime.now().strftime("%H:%M"),
    })


@app.route("/api/bmi", methods=["POST"])
def bmi_endpoint():
    data   = request.get_json(force=True)
    weight = float(data.get("weight", 0))
    height = float(data.get("height", 0))
    age    = int(data.get("age", 25))
    gender = data.get("gender", "male")
    activity = data.get("activity", "moderate")

    bmi_data  = calculate_bmi(weight, height)
    tdee_data = calculate_tdee(weight, height, age, gender, activity)
    tip_index = (age + int(weight)) % len(NUTRITION_TIPS)

    return jsonify({
        **bmi_data,
        **tdee_data,
        "tip": NUTRITION_TIPS[tip_index],
    })


@app.route("/api/meal-plan", methods=["POST"])
def meal_plan():
    data      = request.get_json(force=True)
    diet_type = data.get("diet_type", "vegetarian").lower()
    goal      = data.get("goal", "maintenance")
    calories  = int(data.get("calories", 2000))

    plan_key = "non_vegetarian" if diet_type in ("non_vegetarian", "non-vegetarian", "omnivore") else "vegetarian"
    plan     = SAMPLE_MEAL_PLANS.get(plan_key, SAMPLE_MEAL_PLANS["vegetarian"])

    tips = [
        f"Target: ~{calories} kcal/day for {goal}",
        "Drink water before each meal",
        "Chew slowly — 20 minutes for satiety signals to reach brain",
        "Prep meals on Sunday to stay consistent all week",
    ]

    return jsonify({
        "plan":   plan,
        "tips":   tips,
        "goal":   goal,
        "diet_type": diet_type,
    })


@app.route("/api/food-calories", methods=["GET"])
def food_calories():
    return jsonify({"foods": FOOD_CALORIES})


@app.route("/api/tips", methods=["GET"])
def get_tips():
    return jsonify({"tips": NUTRITION_TIPS})


@app.route("/api/analyze-meal", methods=["POST"])
def analyze_meal():
    """Use AI to analyze a described meal and estimate nutrition."""
    data         = request.get_json(force=True)
    meal_desc    = data.get("meal", "").strip()
    user_context = data.get("user_context", {})

    if not meal_desc:
        return jsonify({"error": "No meal provided"}), 400

    analysis_prompt = (
        f"Analyze the nutritional content of this meal: '{meal_desc}'\n\n"
        "Provide:\n"
        "1. Estimated total calories\n"
        "2. Macronutrient breakdown (protein, carbs, fats)\n"
        "3. Key micronutrients present\n"
        "4. Health score (1–10) with brief reasoning\n"
        "5. One suggestion to make it healthier\n\n"
        "Format your answer clearly with these 5 sections."
    )
    messages = [{"role": "user", "content": analysis_prompt}]
    analysis = call_watsonx(messages, user_context)
    return jsonify({"analysis": analysis, "meal": meal_desc})


@app.route("/api/family-plan", methods=["POST"])
def family_plan():
    """Generate AI family nutrition recommendations."""
    data    = request.get_json(force=True)
    members = data.get("members", [])

    if not members:
        return jsonify({"error": "No family members provided"}), 400

    member_desc = "\n".join(
        f"- {m.get('name','Member')}, Age {m.get('age','?')}, "
        f"Goal: {m.get('goal','healthy eating')}, "
        f"Diet: {m.get('diet','regular')}"
        for m in members
    )
    prompt = (
        f"Create a family-friendly weekly nutrition plan for the following family members:\n\n"
        f"{member_desc}\n\n"
        "Provide:\n"
        "1. Common family meals that satisfy everyone's needs\n"
        "2. Personalized adjustments per member\n"
        "3. Grocery list highlights\n"
        "4. Practical family cooking tips\n"
        "Focus on Indian/South Asian food culture where possible."
    )
    messages  = [{"role": "user", "content": prompt}]
    plan_text = call_watsonx(messages, {})
    return jsonify({"plan": plan_text, "members": members})


@app.route("/api/health")
def health_check():
    return jsonify({
        "status":    "ok",
        "model":     MODEL_ID,
        "watsonx":   WATSONX_AVAILABLE,
        "timestamp": datetime.now().isoformat(),
    })


# ─── Entry Point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port  = int(os.getenv("FLASK_PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    print(f"\n🚀 NutriAgent AI starting on http://localhost:{port}")
    print(f"   Model : {MODEL_ID}")
    print(f"   Debug : {debug}\n")
    app.run(host="0.0.0.0", port=port, debug=debug)
