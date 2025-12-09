# seed_prompts.py
# Seed default prompt templates into the SQLite DB for the Flask backend.

from db import init_db, get_connection


DEFAULT_PROMPTS = [
    {
        "name": "Default Categorization Prompt",
        "type": "categorize",
        "content": """Categorize the email into exactly one of these labels:
- Important
- To-Do
- Newsletter
- Spam
- Social

Rules:
- "Important": time-sensitive or high-impact information for the user.
- "To-Do": email clearly asks the user to perform a task (reply, prepare something, attend something, fix something, etc.).
- "Newsletter": bulk / marketing / digest / automated content.
- "Spam": phishing, scams, irrelevant promotions.
- "Social": informal messages from friends, social events, meetups.

Return only the label word (Important, To-Do, Newsletter, Spam, or Social).
Do not include any explanations or extra text.

Email:
{email_body}""",
    },
    {
        "name": "Default Action Extraction Prompt",
        "type": "extract_actions",
        "content": """You are an assistant that extracts clear, actionable tasks from an email.

For the given email, identify all tasks that the user (or others) is expected to do.

Return a JSON array of objects with this exact structure:
[
  {
    "task": "short description of the action",
    "deadline": "YYYY-MM-DD if mentioned, otherwise empty string",
    "assignee": "who should do it (user, sender, or a named person) or empty string"
  }
]

Guidelines:
- If there are no clear actions, return an empty JSON array: [].
- If a deadline is relative (e.g., "by Friday"), approximate it if possible from the context; otherwise use an empty string.
- Be concise but specific in the "task" field.

Email:
{email_body}""",
    },
    {
        "name": "Default Draft Reply Prompt",
        "type": "draft_reply",
        "content": """You are an assistant that drafts professional email replies.

Given the original email and a brief user instruction (what the user wants to achieve), draft a concise, polite reply.

Write in the first person ("I"), and:
- Acknowledge the sender.
- Address each request or question clearly.
- Keep tone professional and friendly.
- Keep the length moderate (5–10 sentences).

Return only the email body text. Do not include subject, greetings like "Subject:", or any JSON.

Original email:
{email_body}

User instruction:
{user_instruction}""",
    },
]


def seed_prompts():
    # ensure DB and tables exist
    init_db()

    conn = get_connection()
    cur = conn.cursor()

    for prompt in DEFAULT_PROMPTS:
        ptype = prompt["type"]

        # Check if a prompt for this type already exists
        cur.execute("SELECT id FROM prompts WHERE type = ? LIMIT 1", (ptype,))
        row = cur.fetchone()

        if row:
            print(f"Prompt with type '{ptype}' already exists (id={row['id']}), skipping.")
        else:
            cur.execute(
                "INSERT INTO prompts(name, type, content) VALUES (?, ?, ?)",
                (prompt["name"], prompt["type"], prompt["content"]),
            )
            print(f"Inserted default prompt for type '{ptype}'.")

    conn.commit()
    conn.close()
    print("Seeding complete.")


if __name__ == "__main__":
    seed_prompts()
