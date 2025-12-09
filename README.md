# ✉️ AI Email Agent  
A full-stack Email Assistant using **Flask**, **Django**, and **Groq LLaMA 3.1**.  
The system can:

- Categorize emails  
- Extract actionable tasks  
- Generate draft replies with AI  
- Allow user instructions for personalized responses  
- Save AI-generated drafts  
- Manage customizable prompt templates  
- Browse inbox and run agent actions interactively  

---

## 🚀 Features

### ✔ AI-Powered Email Processing
Uses **Groq LLaMA 3.1 (70B or 8B)** to:
- Categorize incoming emails  
- Extract JSON-formatted tasks  
- Draft intelligent email replies  
- Combine user instructions with prompt templates  

### ✔ Django Frontend
Provides a clean UI for:
- Viewing inbox emails  
- Running the AI processing agent  
- Editing prompt templates  
- Saving and reviewing generated drafts  

### ✔ Flask Backend API
Handles:
- Prompt storage (SQLite)  
- Local inbox (mock data)  
- AI model calls via Groq  
- Draft storage  
- Email processing pipeline (categorize + action extraction)

---

## 🧩 Project Structure

```
email-agent/
│
├── backend-flask/
│   ├── app.py              # Flask API server
│   ├── llm.py              # Groq LLaMA 3.1 integration
│   ├── db.py               # SQLite database helpers
│   ├── data/
│   │   └── mock_inbox.json # Fake inbox used for development
│   ├── seed_prompts.py     # Seed default prompt templates
│   └── .env                # Groq API key + config (not committed)
│
└── frontend-django/
    ├── manage.py
    ├── frontend_django/
    └── emails/
        ├── views.py        # Inbox, prompts, drafts, agent
        ├── urls.py
        └── templates/
            └── emails/
                ├── base.html
                ├── inbox.html
                ├── prompts.html
                ├── drafts.html
                └── agent.html
```

---

## ⚙️ Requirements

### Backend (Flask)

```
Flask
Flask-CORS
python-dotenv
requests
groq
```

### Frontend (Django)

```
Django>=5.0
requests
```

---

## 🔧 Setup Instructions

### 1️⃣ Clone the repository
```bash
git clone https://github.com/USERNAME/email-agent.git
cd email-agent
```

---

## 2️⃣ Setup Backend

### Create & activate virtual environment
```bash
cd backend-flask
python -m venv venv
venv\Scripts\activate     # Windows
# OR
source venv/bin/activate # macOS/Linux
```

### Install dependencies
```bash
pip install -r requirements.txt
```

### Create `.env`
```env
GROQ_API_KEY=your_groq_key_here
GROQ_MODEL=llama-3.1-70b-versatile
FLASK_PORT=5000
```

### Initialize database
```bash
python seed_prompts.py
```

### Run Flask backend
```bash
python app.py
```

---

## 3️⃣ Setup Django Frontend

### Create & activate virtual environment
```bash
cd ../frontend-django
python -m venv venv
venv\Scripts\activate
# OR
source venv/bin/activate
```

### Install dependencies
```bash
pip install -r requirements.txt
```

### Apply migrations
```bash
python manage.py migrate
```

### Run Django server
```bash
python manage.py runserver
```

---

## 🧪 Usage Workflow

### 1. Open the frontend  
Visit:

```
http://127.0.0.1:8000/
```

### 2. Browse Inbox  
Click on any email to view details and run analysis:

- **Run Agent (categorize + extract)**  
- **Open Agent Chat → chat with AI**  

### 3. Generate Replies  
In Agent Chat:

- Choose prompt template  
- Add instruction (optional)  
- Run Agent  
- Save Draft  

### 4. Review Drafts  
Navigate to the **Drafts** page to see all AI-generated emails.

---

## 🤖 AI Model Integration  
The backend uses:

### ✔ Groq LLaMA 3.1 (Recommended)
- `llama-3.1-70b-versatile`  
- `llama-3.1-8b-instant` (faster)

In `llm.py`, `call_llm()` safely handles:
- Model calls  
- API errors  
- Network failures  
- Returning clean text to frontend  

---

## 📌 Roadmap

These may be added later:

- Gmail / Outlook OAuth integration  
- Real email fetching  
- Automated email replies  
- Semantic search over inbox  
- Multi-agent workflows  
- Streaming responses  
- Dark mode UI theme  

---

## 🛡 Security Notes

- Never commit `.env` or API keys  
- Add these to your `.gitignore`:

```
*.env
venv/
__pycache__/
*.sqlite
```

---

## 🧩 License
MIT License
