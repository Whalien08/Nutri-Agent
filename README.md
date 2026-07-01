# 🥗 NutriAgent AI — IBM Watsonx.ai Powered Nutrition Advisor

An AI-powered nutrition web application built with **Python Flask** and **IBM Watsonx.ai Granite models**. Features a full chat interface, BMI calculator, personalized meal planner, family nutrition planner, and a nutrition dashboard — all with Indian food preferences baked in.

---

## ✨ Features

| Feature | Description |
|---|---|
| 💬 **AI Chat** | Real-time conversation with IBM Watsonx.ai Granite model |
| 📊 **Nutrition Dashboard** | Calorie targets, macro breakdown, food calorie reference |
| 🤖 **AI Meal Analyzer** | Describe a meal; AI estimates calories & macros |
| ⚖️ **BMI Calculator** | BMI + TDEE + calorie targets with visual gauge |
| 📅 **Meal Planner** | Sample & AI-generated personalized meal plans |
| 👨‍👩‍👧 **Family Planner** | Add family members and get AI family nutrition plan |
| 👤 **Profile** | Save your health profile; AI personalises all responses |
| 🌙 **Dark Mode** | Full dark/light theme toggle |
| 📱 **Mobile Responsive** | Optimised for phones and tablets |

---

## 🗂️ Project Structure

```
nutrition-agent/
├── app.py                  ← Flask backend + AGENT_INSTRUCTIONS
├── requirements.txt        ← Python dependencies
├── .env.example            ← Environment variable template
├── .env                    ← Your secrets (never commit this!)
├── templates/
│   └── index.html          ← Single-page HTML frontend
└── static/
    ├── css/
    │   └── style.css       ← All styles (light + dark theme)
    └── js/
        └── app.js          ← All frontend logic
```

---

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.9 or higher
- An **IBM Cloud** account ([Sign up free](https://cloud.ibm.com/registration))
- An **IBM Watsonx.ai** project

### 2. Clone / Copy the Project

```bash
cd nutrition-agent
```

### 3. Create & Activate Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Set Up Environment Variables

```bash
# Copy the example file
cp .env.example .env
```

Open `.env` and fill in your credentials:

```env
IBM_API_KEY=your_ibm_cloud_api_key_here
IBM_PROJECT_ID=your_watsonx_project_id_here
IBM_WATSONX_URL=https://us-south.ml.cloud.ibm.com
FLASK_SECRET_KEY=change_this_to_a_random_string
```

#### How to get IBM Watsonx.ai credentials:

1. Log in to [IBM Cloud](https://cloud.ibm.com)
2. Create an **IBM Watsonx.ai** service instance
3. Go to **Manage → Access (IAM) → API Keys** → Create API key → copy it to `IBM_API_KEY`
4. Open [Watsonx.ai Studio](https://dataplatform.cloud.ibm.com/), create a project
5. Copy the **Project ID** from the project settings to `IBM_PROJECT_ID`
6. Set `IBM_WATSONX_URL` to the region URL (default: `https://us-south.ml.cloud.ibm.com`)

### 6. Run the App

```bash
python app.py
```

Open your browser at **http://localhost:5000** 🎉

---

## ⚙️ Customising the Agent (AGENT_INSTRUCTIONS)

Everything about how the AI behaves is controlled by the `AGENT_INSTRUCTIONS` block at the top of [`app.py`](app.py). **No other file needs to change.**

```python
# ── Personality & Role
AGENT_PERSONA = "You are NutriAgent AI …"

# ── Tone (friendly, clinical, motivational…)
AGENT_TONE = "Be warm, encouraging …"

# ── Diet specialisation
AGENT_DIET_FOCUS = "Primary focus: Indian vegetarian …"

# ── Language & response style
AGENT_LANGUAGE_STYLE = "Use simple English …"
AGENT_RESPONSE_FORMAT = "Use **bold** headings …"

# ── Safety guardrails (never remove)
AGENT_SAFETY_RULES = "NEVER provide medical diagnoses …"

# ── Indian food knowledge base (add/edit freely)
AGENT_INDIAN_FOOD = "Grains: Rice, Jowar …"

# ── First message shown to user
AGENT_GREETING = "👋 Hello! I'm NutriAgent AI …"

# ── Model selection
MODEL_ID = "ibm/granite-3-3-8b-instruct"

# ── LLM hyper-parameters
GENERATION_PARAMS = { "temperature": 0.7, "max_new_tokens": 1024, … }
```

### Switching Models

| Model | Use Case |
|---|---|
| `ibm/granite-3-3-8b-instruct` | Best quality (default) |
| `ibm/granite-3-2b-instruct` | Faster, lower cost |
| `ibm/granite-13b-instruct-v2` | Maximum quality |

Change `MODEL_ID` in `app.py` to switch.

---

## 🌐 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Main web app |
| `POST` | `/api/chat` | Chat with AI |
| `POST` | `/api/bmi` | BMI + TDEE calculation |
| `POST` | `/api/meal-plan` | Sample meal plan |
| `POST` | `/api/analyze-meal` | AI meal nutrition analysis |
| `POST` | `/api/family-plan` | AI family nutrition plan |
| `GET` | `/api/food-calories` | Food calorie reference |
| `GET` | `/api/tips` | Nutrition tips |
| `GET` | `/api/health` | Health check |

### Example: Chat API

```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Give me a high-protein breakfast", "messages": [], "user_context": {"diet_type": "vegetarian"}}'
```

---

## ☁️ Deployment

### Option A — Gunicorn (Linux / Cloud)

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Option B — IBM Code Engine

```bash
# 1. Install IBM Cloud CLI + Code Engine plugin
ibmcloud plugin install code-engine

# 2. Create and deploy
ibmcloud ce application create \
  --name nutriagent \
  --image icr.io/your-namespace/nutriagent:latest \
  --port 5000 \
  --env IBM_API_KEY=$IBM_API_KEY \
  --env IBM_PROJECT_ID=$IBM_PROJECT_ID \
  --env IBM_WATSONX_URL=$IBM_WATSONX_URL
```

### Option C — Docker

```dockerfile
# Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "app:app"]
```

```bash
docker build -t nutriagent .
docker run -p 5000:5000 --env-file .env nutriagent
```

### Option D — Heroku

```bash
# Procfile
echo "web: gunicorn app:app" > Procfile

heroku create nutriagent-ai
heroku config:set IBM_API_KEY=... IBM_PROJECT_ID=... IBM_WATSONX_URL=...
git push heroku main
```

---

## 🔒 Security Notes

- **Never commit `.env`** to version control. It is already listed in `.gitignore`.
- Rotate your IBM API key periodically.
- In production, set `FLASK_DEBUG=False`.
- For public deployments, add rate limiting (e.g., `flask-limiter`).

---

## 🐛 Troubleshooting

| Problem | Fix |
|---|---|
| `ibm-watsonx-ai package not installed` | Run `pip install ibm-watsonx-ai` |
| `IBM_API_KEY and IBM_PROJECT_ID must be set` | Check your `.env` file |
| `401 Unauthorized` | API key is invalid or expired — regenerate in IBM Cloud |
| `404 model not found` | Check `MODEL_ID` in `app.py` matches an available Granite model |
| Port 5000 in use | Change `FLASK_PORT=5001` in `.env` |
| Slow responses | Switch to `ibm/granite-3-2b-instruct` for speed |

---

## 📦 Dependencies

```
flask==3.0.3           ← Web framework
flask-cors==4.0.1      ← Cross-origin support
python-dotenv==1.0.1   ← .env loading
ibm-watsonx-ai==1.1.2  ← IBM Watsonx.ai SDK
requests==2.32.3       ← HTTP client
gunicorn==22.0.0       ← Production WSGI server
```

Frontend uses CDN-hosted:
- [Bootstrap 5.3](https://getbootstrap.com/)
- [Bootstrap Icons 1.11](https://icons.getbootstrap.com/)

---

## 📄 License

MIT License. Feel free to use and modify for personal or commercial projects.

---

*Built with ❤️ using IBM Watsonx.ai Granite Models*
