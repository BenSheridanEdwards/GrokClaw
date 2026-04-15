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
CV_FILENAME = "BenSheridanEdwards-CV-2026.pdf"
# LLM output for --safe: three blocks in order (submission, ai_journey, excitement), separated only by this line.
SAFE_ANSWER_FIELD_SEPARATOR = "===FIELD==="

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


def _read_answer_editor(title: str, prompt: str) -> str:
    """Open $EDITOR with a temp file so the user can write/paste without buffer limits.

    Falls back to terminal input if no editor is available.
    """
    import subprocess
    import tempfile

    editor = os.environ.get("EDITOR") or os.environ.get("VISUAL")
    if not editor:
        for candidate in ("code --wait", "nano", "vi"):
            name = candidate.split()[0]
            if any((Path(d) / name).is_file() for d in os.environ.get("PATH", "").split(":")):
                editor = candidate
                break

    if not editor:
        return _read_answer_stdin()

    header = f"# {title}\n# {prompt}\n# Write your answer below this line. Save and close when done.\n\n"
    with tempfile.NamedTemporaryFile(suffix=".md", mode="w", delete=False) as f:
        f.write(header)
        tmp_path = f.name

    try:
        subprocess.run(editor.split() + [tmp_path], check=True)
        content = Path(tmp_path).read_text(encoding="utf-8")
        # Strip comment header lines
        lines = [l for l in content.splitlines() if not l.startswith("# ")]
        return "\n".join(lines).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("  Editor failed, falling back to terminal input.")
        return _read_answer_stdin()
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def _read_answer_stdin() -> str:
    """Read a multi-line answer from stdin. End with two blank lines or Ctrl-D."""
    lines: list[str] = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        lines.append(line)
        if len(lines) >= 2 and lines[-1] == "" and lines[-2] == "":
            lines = lines[:-2]
            break
    return "\n".join(lines).strip()


def run_interview(interview_path: Path) -> str:
    """Interactive Q&A; writes markdown with `# Field - …` sections matching INTERVIEW.md.example."""
    print("\n=== Tinkerer Interview ===")
    print("Answer 4 questions. Your answers are grouped into form fields for --safe generation.")
    print("Each question opens in your editor — write your answer, save, and close.\n")
    answers: list[str] = []
    for i, (title, prompt) in enumerate(INTERVIEW_QUESTIONS, 1):
        print(f"--- Question {i}/{len(INTERVIEW_QUESTIONS)} ---")
        print(f"  {title}")
        print(f"  ({prompt})")
        answer = _read_answer_editor(title, prompt)
        answers.append(answer.strip() if answer else "")
        if answer:
            print(f"  ✓ Saved ({len(answer)} chars)\n")
        else:
            print("  ⚠ Skipped\n")

    a1, a2, a3, a4 = answers

    def _part(label: str, body: str) -> str:
        text = body.strip() if body else "(no answer)"
        return f"**{label}**\n\n{text}"

    submission_body = "\n\n".join(
        [
            _part("Tell me about GrokClaw", a1),
            _part("Why Challenge 1?", a2),
            _part("What would you do with another week?", a3),
            _part("What excites you most about AI right now?", a4),
        ]
    )
    journey_body = a1.strip() if a1.strip() else "(no answer)"
    excitement_body = a4.strip() if a4.strip() else "(no answer)"

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    content = f"""# Tinkerer Interview

Recorded on {now}

# Field - Submission

{submission_body}

# Field - Where are you on your AI journey?

{journey_body}

# Field - What keeps you excited about the future?

{excitement_body}
"""
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


# Keys produced by parse_sensitive_data (markdown **Label** → lowercased dict key)
REQUIRED_SENSITIVE_FIELDS = (
    ("email", "Email"),
    ("phone", "Phone"),
    ("location", "Location"),
)


def validate_sensitive_data(sensitive: dict, source_name: str = "sensitive-data.md") -> None:
    """Require non-empty email, phone, and location before --safe / --submit."""
    missing_labels: list[str] = []
    for key, _label in REQUIRED_SENSITIVE_FIELDS:
        if not sensitive.get(key, "").strip():
            missing_labels.append(_label)
    if not missing_labels:
        return
    example_lines = "\n".join(
        f"- **{label}**: <your value>" for _key, label in REQUIRED_SENSITIVE_FIELDS
    )
    print(
        f"Error: {source_name} must set non-empty values for: {', '.join(missing_labels)}.\n"
        "Use list items under ## Contact with these exact labels (see sensitive-data.md.example):\n"
        f"{example_lines}",
        file=sys.stderr,
    )
    sys.exit(1)


def extract_name(builder: str) -> str:
    """First `- **Name**: value` list item (key matched case-insensitively)."""
    for line in builder.splitlines():
        stripped = line.strip()
        if not stripped.startswith("- **") or "**:" not in stripped:
            continue
        try:
            key_start = stripped.index("**") + 2
            key_end = stripped.index("**:", key_start)
            key = stripped[key_start:key_end].strip().lower()
            if key == "name":
                return stripped[key_end + 3:].strip()
        except ValueError:
            continue
    return ""


def validate_builder_name(builder: str) -> None:
    if extract_name(builder):
        return
    print(
        "Error: BUILDER.md must include a non-empty name under ## Identity, for example:\n"
        "  - **Name**: Your Name\n"
        "See tinkerer/BUILDER.md.example.",
        file=sys.stderr,
    )
    sys.exit(1)


def generate_safe_answers(builder: str, interview: str, sensitive: dict) -> dict:
    api_key = os.environ.get("XAI_API_KEY", "")
    if not api_key:
        print("Error: XAI_API_KEY not set in .env", file=sys.stderr)
        sys.exit(1)

    prompt = f"""You are Tinkerer, an AI agent applying to the Stationed AI Tinkerer role on behalf of Ben.

Below is Ben's profile (BUILDER.md) and his pre-written answers for each form field.
Your job is to TRANSFER his answers into the form — not rewrite them.
Make only minor edits for flow, clarity, or formatting. Keep Ben's voice exactly as-is.
Preserve bullet-point lists using - dashes as-is — they read well in form textareas.
Remove bold sub-headings like "**1. Describe what you built**" — just flow the content naturally.
Preserve paragraph breaks between sub-sections — do NOT collapse everything into one giant paragraph.
Write in first person as Ben.

BUILDER.md:
{builder}

Ben's answers (organised by form field):
{interview}

If the interview uses "# Field - …" section headers, take content from those sections.
If it only uses legacy "## …" question headings (older saved interviews), map in order: combine all four
answers into SUBMISSION; use the first answer for AI_JOURNEY and the fourth for EXCITEMENT.

Output exactly three text blocks in this order, with no other text before or after:

1. SUBMISSION — use the content under "# Field - Submission" from Ben's answers.
   Combine the sub-sections into one cohesive block. Minor edits only.

2. AI_JOURNEY — use the content under "# Field - Where are you on your AI journey?"
   Combine the sub-sections into one cohesive block. Minor edits only.

3. EXCITEMENT — use the content under "# Field - What keeps you excited about the future?"
   Combine the sub-sections into one cohesive block. Minor edits only.

Separate consecutive blocks with EXACTLY one line containing only {SAFE_ANSWER_FIELD_SEPARATOR} (nothing else on that line).
Do not use ---, markdown headers, or any other separator between blocks.
Output ONLY the three blocks. No labels, no preamble."""

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

    parts = [p.strip() for p in text.split(SAFE_ANSWER_FIELD_SEPARATOR)]
    if len(parts) < 3:
        print(
            f"Warning: Expected 3 blocks separated by {SAFE_ANSWER_FIELD_SEPARATOR!r}, "
            f"got {len(parts)} segment(s). Some answers may be empty.",
            file=sys.stderr,
        )

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


def parse_safe_trial(text: str) -> dict:
    """Extract the three free-text field values from a safe-trial.md file."""
    sections = {
        "submission": "",
        "ai_journey": "",
        "excitement": "",
    }
    # Map markdown headers to dict keys
    header_map = {
        "### Submission": "submission",
        "### Where are you currently on your AI journey?": "ai_journey",
        "### What keeps you excited about the future?": "excitement",
    }
    current_key = None
    lines: list[str] = []

    for line in text.splitlines():
        if line.strip() in header_map:
            if current_key and lines:
                sections[current_key] = "\n".join(lines).strip()
            current_key = header_map[line.strip()]
            lines = []
        elif current_key is not None:
            lines.append(line)

    if current_key and lines:
        sections[current_key] = "\n".join(lines).strip()

    return sections


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
        run_browser(fields=TRIAL_DATA, is_trial=True, workspace=workspace)
        return

    builder = load_file(builder_path, "BUILDER.md", "tinkerer/BUILDER.md.example")
    validate_builder_name(builder)
    sensitive_text = load_file(sensitive_path, "sensitive-data.md", "sensitive-data.md.example")
    sensitive = parse_sensitive_data(sensitive_text)
    validate_sensitive_data(sensitive)

    if args.safe:
        alt_interview_path = tinkerer_dir / "INTERVIEW.md"
        if alt_interview_path.is_file():
            interview = alt_interview_path.read_text(encoding="utf-8")
            print(f"Using INTERVIEW.md at {alt_interview_path}")
        elif interview_path.is_file():
            interview = interview_path.read_text(encoding="utf-8")
            print(f"Using existing interview at {interview_path}")
        else:
            interview = run_interview(interview_path)

        print("Generating answers via xAI Grok...")
        answers = generate_safe_answers(builder, interview, sensitive)
        write_safe_trial(answers, safe_trial_path)
        return

    if args.submit:
        if safe_trial_path.is_file():
            safe_trial_text = safe_trial_path.read_text(encoding="utf-8")
            print(f"Using safe trial at {safe_trial_path}")
            free_text = parse_safe_trial(safe_trial_text)
        else:
            print("Error: Run --safe first to generate safe-trial.md", file=sys.stderr)
            sys.exit(1)

        fields = {
            "name": extract_name(builder),
            "email": sensitive.get("email", ""),
            "phone": sensitive.get("phone", ""),
            "location": sensitive.get("location", ""),
            "github": GITHUB_LINK,
            "challenge": CHALLENGE,
            **free_text,
        }
        run_browser(
            fields=fields,
            workspace=workspace,
        )


def run_browser(fields: dict, is_trial: bool = False, safe_trial: str = "", builder: str = "", interview: str = "", workspace: Path = Path(".")):
    """Launch browser-use agent to fill the Stationed application form."""
    try:
        import asyncio
        from browser_use import Agent, Browser
        from browser_use.llm.openai.like import ChatOpenAILike
    except ImportError:
        print(
            "Error: browser-use is not installed (could not import browser_use).\n\n"
            "Install using the official documentation so you can review dependencies first:\n"
            "  https://github.com/browser-use/browser-use#readme\n\n"
            "Typical approach: create a virtual environment, then install with pip per the README "
            "(avoid piping remote install scripts into your shell).\n"
            "GrokClaw's launcher uses ~/.browser-use-env when present — see tools/run-tinkerer-apply.sh.",
            file=sys.stderr,
        )
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
    if any(fields.get(k) for k in ("submission", "ai_journey", "excitement")):
        free_text_json = json.dumps(
            {
                "submission": fields.get("submission") or "",
                "ai_journey": fields.get("ai_journey") or "",
                "excitement": fields.get("excitement") or "",
            },
            indent=2,
            ensure_ascii=False,
        )
        free_text_source = f"""
FREE-TEXT FIELDS — parse the JSON object below with a JSON parser (or equivalent). Each value is one string; after decoding, newlines inside that string are real line breaks, not the two characters backslash and n.
Map keys to textareas: submission → Submission; ai_journey → "Where are you currently on your AI journey?"; excitement → "What keeps you excited about the future?".
Paste each decoded string into its textarea in ONE action — full multi-line text, formatting preserved. Do not re-type the JSON.

{free_text_json}"""
    elif safe_trial:
        free_text_source = f"\nFREE-TEXT FIELDS (use the pre-generated answers):\n\n{safe_trial}"
    else:
        free_text_source = f"""
FREE-TEXT FIELDS (synthesize from the profile and interview below):

Profile:
{builder}

Interview:
{interview}"""

    cv_path = (workspace / "tinkerer" / CV_FILENAME).resolve()
    cv_present = cv_path.is_file()
    if is_trial and not cv_present:
        print(
            f"Note: CV not found at {cv_path} — trial will skip the CV upload step. "
            f"Add tinkerer/{CV_FILENAME} before --submit.\n"
        )
    if not cv_present and not is_trial:
        print(
            f"Error: CV PDF not found at {cv_path}\n"
            f"Place your resume in the repo as tinkerer/{CV_FILENAME} (gitignored; not in fresh checkouts), "
            "then run --submit again.",
            file=sys.stderr,
        )
        sys.exit(1)

    if cv_present:
        cv_instructions = (
            f"- Upload the CV file from this path (use available_file_paths): {cv_path}"
        )
    else:
        cv_instructions = (
            "- Do NOT upload a CV — the PDF is missing on disk (trial mode only). "
            f"Skip the resume/CV field or leave it empty. For a real run, add tinkerer/{CV_FILENAME} before --submit."
        )

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
- For each textarea, paste the COMPLETE text in one go — do not overwrite or clear between paragraphs
{cv_instructions}
- Do NOT click Submit. Stop after filling all fields.
- At the end, output a structured summary of every field and what was entered
"""

    available_paths = [str(cv_path)] if cv_present else []

    async def _run():
        browser = Browser(headless=False, keep_alive=True)
        try:
            agent = Agent(task=fill_task, llm=llm, browser=browser, available_file_paths=available_paths)
            history = await agent.run()
            mode_label = "trial" if is_trial else "submit"
            print(f"\n{'=' * 60}")
            print(f"Tinkerer ({mode_label}) — Form Filled")
            print(f"{'=' * 60}")
            print(history.final_result())
            print(f"{'=' * 60}\n")

            if is_trial:
                print("Trial complete — form filled with test data. No submission.")
                if not cv_present:
                    print(
                        f"Note: CV upload was skipped — file not found at {cv_path}. "
                        f"Add tinkerer/{CV_FILENAME} before running --submit."
                    )
                try:
                    input("Press Enter to close the browser...")
                except EOFError:
                    pass
            else:
                print("Review the form in the browser. Take your time.")
                print("Type 'submit' to submit, or 'close' to close without submitting.")
                while True:
                    try:
                        answer = input("> ").strip().lower()
                    except (EOFError, KeyboardInterrupt):
                        print("\nKeeping browser open. Ctrl+C again to force quit.")
                        try:
                            import time
                            while True:
                                time.sleep(60)
                        except KeyboardInterrupt:
                            break
                        break
                    if answer == "submit":
                        print("\nSubmitting...")
                        submit_agent = Agent(
                            task="The form is already filled. Do NOT fill any fields. Just find and click the 'Submit Application' button, then confirm the submission was successful. Report the result.",
                            llm=llm,
                            browser_session=browser,
                        )
                        submit_history = await submit_agent.run(max_steps=5)
                        print(f"\n{'=' * 60}")
                        print("Tinkerer — Submitted")
                        print(f"{'=' * 60}")
                        print(submit_history.final_result())
                        print(f"{'=' * 60}\n")
                        try:
                            input("Press Enter to close the browser...")
                        except (EOFError, KeyboardInterrupt):
                            pass
                        break
                    elif answer == "close":
                        print("Not submitted. Run --submit again when ready.")
                        break
                    else:
                        print("Type 'submit' or 'close'.")
        finally:
            await browser.stop()

    try:
        asyncio.run(_run())
    except Exception as e:
        print(f"Error: Browser agent failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
