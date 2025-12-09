# app.py
import json
import os

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

from db import init_db, get_connection
from llm import call_llm

load_dotenv()

app = Flask(__name__)
CORS(app)  # allow all origins for dev

# Ensure DB exists when app starts
init_db()

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")
MOCK_INBOX_PATH = os.path.join(DATA_DIR, "mock_inbox.json")


def safe_json_loads(s, fallback=None):
    try:
        return json.loads(s)
    except Exception:
        return fallback


# ---------- HEALTH CHECK ----------

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "env_has_api_key": bool(os.getenv("OPENAI_API_KEY"))})


# ---------- INBOX ----------

@app.route("/api/inbox", methods=["GET"])
def get_inbox():
    if not os.path.exists(MOCK_INBOX_PATH):
        return jsonify({"error": "mock_inbox.json not found"}), 500
    return send_from_directory(DATA_DIR, "mock_inbox.json")


# ---------- PROMPTS ----------

@app.route("/api/prompts", methods=["GET"])
def get_prompts():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, type, content, created_at FROM prompts ORDER BY created_at DESC")
    rows = cur.fetchall()
    conn.close()

    prompts = [dict(row) for row in rows]
    return jsonify(prompts)


@app.route("/api/prompts", methods=["POST"])
def create_prompt():
    data = request.get_json(force=True, silent=True) or {}
    name = data.get("name")
    ptype = data.get("type") or ""
    content = data.get("content")

    if not name or not content:
        return jsonify({"error": "name and content required"}), 400

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO prompts(name, type, content) VALUES (?, ?, ?)",
        (name, ptype, content),
    )
    conn.commit()
    new_id = cur.lastrowid
    cur.execute("SELECT id, name, type, content, created_at FROM prompts WHERE id = ?", (new_id,))
    row = cur.fetchone()
    conn.close()

    return jsonify(dict(row)), 201


# ---------- PROCESS EMAIL ----------

@app.route("/api/process", methods=["POST"])
def process_email():
    data = request.get_json(force=True, silent=True) or {}
    email = data.get("email")
    if not email or not email.get("body"):
        return jsonify({"error": "email.body is required"}), 400

    body_text = email["body"]

    # fetch templates
    conn = get_connection()
    cur = conn.cursor()

    # categorization prompt
    cur.execute("SELECT content FROM prompts WHERE type = ? ORDER BY created_at DESC LIMIT 1", ("categorize",))
    row_cat = cur.fetchone()
    if row_cat:
        cat_template = row_cat["content"]
    else:
        cat_template = (
            "Categorize the email into one of these labels: Important, To-Do, Newsletter, Spam, Social.\n"
            "Return only the label (one word).\n\nEmail:\n{email_body}"
        )

    # action extraction prompt
    cur.execute("SELECT content FROM prompts WHERE type = ? ORDER BY created_at DESC LIMIT 1", ("extract_actions",))
    row_act = cur.fetchone()
    if row_act:
        act_template = row_act["content"]
    else:
        act_template = (
            "Extract actionable tasks from the email. "
            "Return a JSON array of objects with keys 'task', 'deadline', and 'assignee'. "
            "If there are no actions, return an empty JSON array [].\n\nEmail:\n{email_body}"
        )

    conn.close()

    cat_prompt = cat_template.replace("{email_body}", body_text)
    actions_prompt = act_template.replace("{email_body}", body_text)

    # Call LLMs (now always return a string, even on error)
    cat_resp = call_llm([{"role": "user", "content": cat_prompt}], max_tokens=60)
    actions_resp = call_llm([{"role": "user", "content": actions_prompt}], max_tokens=400)

    # Try to parse actions as JSON only if it looks like JSON
    parsed_actions = safe_json_loads(actions_resp, None)

    # Save in DB (best-effort; errors here shouldn’t break the response)
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO emails(external_id, sender, subject, timestamp, body, category, actions_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                email.get("id"),
                email.get("sender"),
                email.get("subject"),
                email.get("timestamp"),
                body_text,
                (cat_resp or "").strip(),
                json.dumps(parsed_actions) if parsed_actions is not None else actions_resp,
            ),
        )
        conn.commit()
        conn.close()
    except Exception as db_err:
        print("Warning: failed to persist processed email:", db_err)

    return jsonify({
        "category": (cat_resp or "").strip(),
        "actions_raw": actions_resp,
        "actions_json": parsed_actions,
    })


# ---------- AGENT (chat-like) ----------

@app.route("/api/agent", methods=["POST"])
def agent():
    data = request.get_json(force=True, silent=True) or {}
    email = data.get("email")
    prompt_template = data.get("promptTemplate")
    user_instruction = data.get("userInstruction") or "Please perform the task."

    if not email or not email.get("body"):
        return jsonify({"error": "email.body is required"}), 400

    base_template = (
        prompt_template
        or "You are an assistant that helps draft responses and summarize emails. Keep replies short and professional."
    )

    combined = (
        f"{base_template}\n\n"
        f"Email:\n{email['body']}\n\n"
        f"User instruction:\n{user_instruction}"
    )

    reply = call_llm([{"role": "user", "content": combined}], max_tokens=800)

    return jsonify({"reply": reply})


# ---------- DRAFTS ----------

@app.route("/api/drafts", methods=["GET"])
def list_drafts():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, subject, body, meta_json, created_at FROM drafts ORDER BY created_at DESC"
    )
    rows = cur.fetchall()
    conn.close()

    drafts = []
    for row in rows:
        d = dict(row)
        d["meta"] = safe_json_loads(d.get("meta_json"), None)
        drafts.append(d)

    return jsonify(drafts)


@app.route("/api/drafts", methods=["POST"])
def save_draft():
    data = request.get_json(force=True, silent=True) or {}
    subject = data.get("subject")
    body = data.get("body")
    meta = data.get("meta")

    if not body:
        return jsonify({"error": "draft body is required"}), 400

    meta_json = json.dumps(meta) if meta is not None else None

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO drafts(subject, body, meta_json) VALUES (?, ?, ?)",
        (subject, body, meta_json),
    )
    conn.commit()
    new_id = cur.lastrowid
    cur.execute(
        "SELECT id, subject, body, meta_json, created_at FROM drafts WHERE id = ?",
        (new_id,),
    )
    row = cur.fetchone()
    conn.close()

    draft = dict(row)
    draft["meta"] = safe_json_loads(draft.get("meta_json"), None)
    return jsonify(draft), 201


# ---------- MAIN ----------

if __name__ == "__main__":
    port = int(os.getenv("FLASK_PORT", "5000"))
    print(f"Starting Flask backend on port {port}")
    app.run(host="0.0.0.0", port=port, debug=True)
