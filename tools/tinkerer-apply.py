#!/usr/bin/env python3
"""Tinkerer — one-shot application agent for Stationed AI Tinkerer role."""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

APPLICATION_URL = "https://jadan.zo.space/ai-tinkerer/apply"
GITHUB_LINK = "https://github.com/BenSheridanEdwards/GrokClaw#tinkerer"
CHALLENGE = "1. Let Your Agent Apply"

TRIAL_DATA = {
    "name": "Test Tinkerer Agent",
    "email": "test@example.com",
    "phone": "+1 (555) 000-0000",
    "location": "Test City, Testland",
    "github": "https://github.com/test/example#tinkerer",
    "challenge": "1. Let Your Agent Apply",
    "submission": "This is a trial run to verify the browser-use pipeline works end-to-end. No real data is being submitted.",
    "ai_journey": "Trial mode — testing that the agent can fill every field on the form correctly.",
    "excitement": "Trial mode — verifying form automation before submitting with real answers.",
}

INTERVIEW_QUESTIONS = [
    ("Tell me about GrokClaw", "What is it, what did you build, what's interesting about it?"),
    ("Why Challenge 1?", "Why 'Let Your Agent Apply' specifically?"),
    ("What would you do with another week?", "Where would you take this?"),
    ("What excites you most about AI right now?", "The thing that keeps you up at night — in a good way."),
]


def parse_args():
    parser = argparse.ArgumentParser(description="Tinkerer application agent")
    parser.add_argument("--workspace", default=".", help="GrokClaw repo root")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--safe", action="store_true", help="Generate answers, no browser")
    group.add_argument(
        "--trial",
        action="store_true",
        help="Headed browser on the live form; built-in test placeholders; stop before Submit",
    )
    group.add_argument("--submit", action="store_true", help="Fill form with real data, prompt before submitting")
    return parser.parse_args()


def load_file(path: Path, name: str, example_hint: str = "") -> str:
    if not path.is_file():
        hint = f" Copy {example_hint} to get started." if example_hint else ""
        print(f"Error: {name} not found at {path}.{hint}", file=sys.stderr)
        sys.exit(1)
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        print(f"Error: {name} is empty at {path}.", file=sys.stderr)
        sys.exit(1)
    return text


def run_interview(interview_path: Path) -> str:
    print("\n=== Tinkerer Interview ===")
    print("Answer 4 questions. Your raw answers will be saved and reused.\n")
    sections = []
    for title, prompt in INTERVIEW_QUESTIONS:
        print(f"## {title}")
        print(f"({prompt})")
        print("Type your answer (press Enter twice to finish):\n")
        lines = []
        while True:
            try:
                line = input()
            except EOFError:
                break
            if line == "" and lines and lines[-1] == "":
                break
            lines.append(line)
        answer = "\n".join(lines).strip()
        sections.append(f"## {title}\n\n{answer}")
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    content = f"# Tinkerer Interview\n\nRecorded on {now}\n\n" + "\n\n".join(sections) + "\n"
    interview_path.write_text(content, encoding="utf-8")
    print(f"\nInterview saved to {interview_path}\n")
    return content


def parse_sensitive_data(text: str) -> dict:
    data = {}
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("- **") and "**:" in line:
            key_start = line.index("**") + 2
            key_end = line.index("**:", key_start)
            key = line[key_start:key_end].strip().lower()
            val = line[key_end + 3:].strip()
            if val:
                data[key] = val
    return data


def extract_name(builder: str) -> str:
    for line in builder.splitlines():
        if line.strip().startswith("- **Name**:"):
            return line.split(":", 1)[1].strip()
    return ""


def generate_safe_answers(builder: str, interview: str, sensitive: dict) -> dict:
    api_key = os.environ.get("XAI_API_KEY", "")
    if not api_key:
        print("Error: XAI_API_KEY not set in .env", file=sys.stderr)
        sys.exit(1)

    prompt = f"""You are Tinkerer, an AI agent applying to the Stationed AI Tinkerer role on behalf of Ben.

Below is Ben's profile (BUILDER.md) and his raw interview answers (tinkerer-interview.md).
Generate the form field answers. Be authentic to Ben's voice — not robotic, not over-polished.
Write in first person as Ben.

BUILDER.md:
{builder}

Interview answers:
{interview}

Generate exactly three text blocks, separated by "---FIELD---":

1. SUBMISSION: Synthesize the interview answers into a cohesive response that covers:
   what was built, why Challenge 1, what you'd do with another week, and what excites about AI.
   A few paragraphs, conversational but substantive.

2. AI_JOURNEY: Based on the profile, describe where Ben is on his AI journey —
   what he's building, experimenting with, comfort level. A couple paragraphs.

3. EXCITEMENT: Based on the profile's philosophy section, what keeps Ben excited
   about the future of AI. A couple paragraphs.

Output ONLY the three blocks separated by ---FIELD--- markers. No other text."""

    body = json.dumps({
        "model": "grok-4-1-fast-non-reasoning",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
    }).encode()

    req = urllib.request.Request(
        "https://api.x.ai/v1/chat/completions",
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.load(resp)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"Error: xAI API returned {e.code}: {body}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Error: Could not reach xAI API: {e.reason}", file=sys.stderr)
        sys.exit(1)

    try:
        text = result["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError) as e:
        print(f"Error: Unexpected API response structure: {e}", file=sys.stderr)
        print(f"Response: {json.dumps(result, indent=2)[:500]}", file=sys.stderr)
        sys.exit(1)

    parts = [p.strip() for p in text.split("---FIELD---")]
    if len(parts) < 3:
        print(f"Warning: Expected 3 fields from LLM, got {len(parts)}. Some answers may be empty.", file=sys.stderr)

    return {
        "name": extract_name(builder),
        "email": sensitive.get("email", ""),
        "phone": sensitive.get("phone", ""),
        "location": sensitive.get("location", ""),
        "github": GITHUB_LINK,
        "challenge": CHALLENGE,
        "submission": parts[0] if len(parts) > 0 else "",
        "ai_journey": parts[1] if len(parts) > 1 else "",
        "excitement": parts[2] if len(parts) > 2 else "",
    }


def write_safe_trial(answers: dict, output_path: Path):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    md = f"""# Tinkerer Application — Safe Trial

Generated on {now}

## Form Fields

### Name
{answers['name']}

### Email Address
{answers['email']}

### Phone Number
{answers['phone']}

### Location
{answers['location']}

### GitHub / Projects
{answers['github']}

### Which challenge are you submitting?
{answers['challenge']}

### Submission
{answers['submission']}

### Where are you currently on your AI journey?
{answers['ai_journey']}

### What keeps you excited about the future?
{answers['excitement']}
"""
    output_path.write_text(md, encoding="utf-8")
    print(f"Safe trial written to {output_path}")


def main():
    args = parse_args()
    workspace = Path(args.workspace).resolve()
    tinkerer_dir = workspace / "tinkerer"

    builder_path = tinkerer_dir / "BUILDER.md"
    sensitive_path = tinkerer_dir / "sensitive-data.md"
    interview_path = tinkerer_dir / "tinkerer-interview.md"
    safe_trial_path = tinkerer_dir / "safe-trial.md"

    if args.trial:
        print("Trial mode — filling form with test data...")
        run_browser(fields=TRIAL_DATA, is_trial=True)
        return

    builder = load_file(builder_path, "BUILDER.md")
    sensitive_text = load_file(sensitive_path, "sensitive-data.md", "sensitive-data.md.example")
    sensitive = parse_sensitive_data(sensitive_text)

    if args.safe:
        if not interview_path.is_file():
            interview = run_interview(interview_path)
        else:
            interview = interview_path.read_text(encoding="utf-8")
            print(f"Using existing interview at {interview_path}")

        print("Generating answers via xAI Grok...")
        answers = generate_safe_answers(builder, interview, sensitive)
        write_safe_trial(answers, safe_trial_path)
        return

    if args.submit:
        if not interview_path.is_file():
            print("Error: Run --safe first to complete the interview.", file=sys.stderr)
            sys.exit(1)
        interview = interview_path.read_text(encoding="utf-8")
        safe_trial = ""
        if safe_trial_path.is_file():
            safe_trial = safe_trial_path.read_text(encoding="utf-8")

        fields = {
            "name": extract_name(builder),
            "email": sensitive.get("email", ""),
            "phone": sensitive.get("phone", ""),
            "location": sensitive.get("location", ""),
            "github": GITHUB_LINK,
            "challenge": CHALLENGE,
        }
        run_browser(
            fields=fields,
            safe_trial=safe_trial,
            builder=builder,
            interview=interview,
        )


def run_browser(fields: dict, is_trial: bool = False, safe_trial: str = "", builder: str = "", interview: str = ""):
    """Launch browser-use agent to fill the Stationed application form."""
    try:
        import asyncio
        from browser_use import Agent, Browser
        from browser_use.llm.openai.like import ChatOpenAILike
    except ImportError:
        print("Error: browser-use not installed. Install with: curl -fsSL https://browser-use.com/cli/install.sh | bash", file=sys.stderr)
        sys.exit(1)

    api_key = os.environ.get("XAI_API_KEY", "")
    if not api_key:
        print("Error: XAI_API_KEY not set in .env", file=sys.stderr)
        sys.exit(1)

    llm = ChatOpenAILike(
        model=os.environ.get("BROWSER_USE_MODEL", "grok-3-fast"),
        base_url="https://api.x.ai/v1",
        api_key=api_key,
    )

    free_text_source = ""
    if fields.get("submission"):
        free_text_source = f"""
- Submission: {fields['submission']}
- AI Journey: {fields['ai_journey']}
- Excitement: {fields['excitement']}"""
    elif safe_trial:
        free_text_source = f"\nFREE-TEXT FIELDS (use the pre-generated answers):\n\n{safe_trial}"
    else:
        free_text_source = f"""
FREE-TEXT FIELDS (synthesize from the profile and interview below):

Profile:
{builder}

Interview:
{interview}"""

    fill_task = f"""You are Tinkerer, an AI agent applying to the Stationed AI Tinkerer role.

Navigate to {APPLICATION_URL} and find the application form.

Fill in every field using the information below. Be precise — use exact values for factual fields
and the pre-generated text for free-text fields.

FACTUAL FIELDS:
- Name: {fields.get('name', '')}
- Email Address: {fields.get('email', '')}
- Phone Number: {fields.get('phone', '')}
- Location: {fields.get('location', '')}
- GitHub / Projects: {fields.get('github', GITHUB_LINK)}
- Which challenge: select "{fields.get('challenge', CHALLENGE)}" from the dropdown
{free_text_source}

INSTRUCTIONS:
- Fill every field from top to bottom
- For the dropdown, select "{fields.get('challenge', CHALLENGE)}"
- Do not upload a file — the GitHub link is sufficient
- Do NOT click Submit. Stop after filling all fields.
- At the end, output a structured summary of every field and what was entered
"""

    async def _run():
        browser = Browser(headless=False)
        try:
            agent = Agent(task=fill_task, llm=llm, browser=browser)
            history = await agent.run()
            mode_label = "trial" if is_trial else "submit"
            print(f"\n{'=' * 60}")
            print(f"Tinkerer ({mode_label}) — Form Filled")
            print(f"{'=' * 60}")
            print(history.final_result())
            print(f"{'=' * 60}\n")

            if is_trial:
                print("Trial complete — form filled with test data. No submission.")
            else:
                print("Review the form in the browser.")
                try:
                    answer = input("Submit this application? [y/N] ").strip().lower()
                except EOFError:
                    answer = ""
                if answer == "y":
                    print("\nSubmitting...")
                    submit_agent = Agent(
                        task="Click the Submit Application button on the form and confirm the success screen. Report the result.",
                        llm=llm,
                        browser=browser,
                    )
                    submit_history = await submit_agent.run()
                    print(f"\n{'=' * 60}")
                    print("Tinkerer — Submitted")
                    print(f"{'=' * 60}")
                    print(submit_history.final_result())
                    print(f"{'=' * 60}\n")
                else:
                    print("Not submitted. Run --submit again when ready.")
        finally:
            await browser.close()

    try:
        asyncio.run(_run())
    except Exception as e:
        print(f"Error: Browser agent failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
