# emails/views.py
import json
import requests
from django.conf import settings
from django.shortcuts import render, redirect
from django.http import Http404

FLASK_API_BASE = settings.FLASK_API_BASE


def inbox_view(request):
    # Load inbox from Flask
    inbox_resp = requests.get(f"{FLASK_API_BASE}/api/inbox")
    inbox_resp.raise_for_status()
    emails = inbox_resp.json()

    email_id = request.GET.get("email_id")
    selected_email = None
    if email_id:
        selected_email = next(
            (e for e in emails if str(e.get("id")) == str(email_id)),
            None,
        )

    process_result = None
    actions_json_pretty = None
    error_message = None

    if request.method == "POST" and "process_email" in request.POST and selected_email:
        try:
            resp = requests.post(
                f"{FLASK_API_BASE}/api/process",
                json={"email": selected_email},
                timeout=60,
            )
            data = resp.json()
            if resp.status_code != 200:
                error_message = data.get("error", f"Backend error {resp.status_code}")
            else:
                process_result = data
                if data.get("actions_json") is not None:
                    actions_json_pretty = json.dumps(data["actions_json"], indent=2)
        except requests.RequestException as e:
            error_message = f"Failed to contact backend: {e}"

    context = {
        "emails": emails,
        "selected_email": selected_email,
        "process_result": process_result,
        "actions_json_pretty": actions_json_pretty,
        "error_message": error_message,
    }
    return render(request, "emails/inbox.html", context)


def prompts_view(request):
    error_message = None
    try:
        resp = requests.get(f"{FLASK_API_BASE}/api/prompts", timeout=30)
        resp.raise_for_status()
        prompts = resp.json()
    except requests.RequestException as e:
        prompts = []
        error_message = f"Failed to load prompts from backend: {e}"

    if request.method == "POST":
        name = request.POST.get("name")
        ptype = request.POST.get("type")
        content = request.POST.get("content")
        if name and content:
            try:
                requests.post(
                    f"{FLASK_API_BASE}/api/prompts",
                    json={"name": name, "type": ptype, "content": content},
                    timeout=60,
                )
                return redirect("prompts")
            except requests.RequestException as e:
                error_message = f"Failed to save prompt: {e}"
        else:
            error_message = "Name and content are required."

    return render(
        request,
        "emails/prompts.html",
        {"prompts": prompts, "error_message": error_message},
    )


def drafts_view(request):
    error_message = None
    try:
        resp = requests.get(f"{FLASK_API_BASE}/api/drafts", timeout=30)
        resp.raise_for_status()
        drafts = resp.json()
    except requests.RequestException as e:
        drafts = []
        error_message = f"Failed to load drafts from backend: {e}"

    return render(
        request,
        "emails/drafts.html",
        {"drafts": drafts, "error_message": error_message},
    )


def agent_view(request, email_id):
    # Load inbox to find email
    try:
        inbox_resp = requests.get(f"{FLASK_API_BASE}/api/inbox", timeout=30)
        inbox_resp.raise_for_status()
        emails = inbox_resp.json()
    except requests.RequestException as e:
        raise Http404(f"Could not load inbox from backend: {e}")

    email = next((e for e in emails if str(e.get("id")) == str(email_id)), None)
    if not email:
        raise Http404("Email not found")

    # Load prompts for the dropdown
    try:
        p_resp = requests.get(f"{FLASK_API_BASE}/api/prompts", timeout=30)
        p_resp.raise_for_status()
        prompts = p_resp.json()
    except requests.RequestException:
        prompts = []

    agent_reply = None
    selected_prompt_content = ""
    user_instruction = ""
    error_message = None
    success_message = None

    if request.method == "POST":
        selected_prompt_content = request.POST.get("prompt_content") or ""
        user_instruction = request.POST.get("instruction") or "Summarize this email."

        # We run the agent for BOTH buttons (run_agent & save_draft)
        try:
            agent_resp = requests.post(
                f"{FLASK_API_BASE}/api/agent",
                json={
                    "email": email,
                    "promptTemplate": selected_prompt_content,
                    "userInstruction": user_instruction,
                },
                timeout=90,
            )
            data = agent_resp.json()

            if agent_resp.status_code != 200 or "error" in data:
                error_message = data.get(
                    "error",
                    f"Backend error {agent_resp.status_code}",
                )
            else:
                agent_reply = data.get("reply")

                # If they clicked "Run & Save as Draft", save via backend
                if "save_draft" in request.POST and agent_reply:
                    d_resp = requests.post(
                        f"{FLASK_API_BASE}/api/drafts",
                        json={
                            "subject": f"Re: {email.get('subject', 'draft')}",
                            "body": agent_reply,
                            "meta": {"fromEmailId": email.get("id")},
                        },
                        timeout=60,
                    )
                    if d_resp.status_code == 201:
                        success_message = "Draft saved successfully."
                    else:
                        error_message = (
                            f"Draft save failed: {d_resp.status_code} {d_resp.text}"
                        )

        except requests.RequestException as e:
            error_message = f"Failed to contact backend: {e}"

    context = {
        "email": email,
        "prompts": prompts,
        "agent_reply": agent_reply,
        "selected_prompt_content": selected_prompt_content,
        "user_instruction": user_instruction,
        "error_message": error_message,
        "success_message": success_message,
    }
    return render(request, "emails/agent.html", context)
