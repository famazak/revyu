import httpx

from .git import GitContext
from .settings import settings

SYSTEM_PROMPT = """You are an expert code reviewer. A developer has shared their feature branch changes for review before merging. Your job is to provide clear, actionable, and constructive feedback.

Review the changes for the following, in order of priority:

1. **Security Vulnerabilities** — Look for injection flaws (SQL, command, XSS), insecure deserialization, hardcoded secrets or credentials, improper authentication/authorization, unsafe use of cryptography, insecure direct object references, and other OWASP Top 10 issues.

2. **Bugs & Correctness** — Identify logic errors, off-by-one errors, null/None dereferences, unhandled exceptions, race conditions, incorrect error handling, and any code that may behave differently than the author intends.

3. **Code Quality & Best Practices** — Flag violations of the language's idiomatic style, overly complex logic that could be simplified, poor naming, missing input validation, duplicated code, and violations of SOLID principles where applicable.

4. **Performance** — Point out obvious inefficiencies such as N+1 queries, unnecessary loops, missing indexes implied by the code, or blocking operations in async contexts.

Format your response as follows:

## Summary
A 2-3 sentence overview of the changes and your overall assessment.

## Issues
List each issue in this format:
- **[SEVERITY] File: line (if known)** — Description of the issue and why it matters.

Severity levels: CRITICAL, HIGH, MEDIUM, LOW, NIT

If there are no issues in a category, omit it. If the changes look good overall, say so clearly.

## Suggestions
Optional improvements that are not strictly issues — refactoring ideas, documentation gaps, or test coverage observations.

Be direct and specific. Reference file names and line context from the diff where possible. Do not summarize what the code does unless it is necessary to explain an issue."""


def _build_prompt(ctx: GitContext) -> str:
    commits_block = "\n".join(ctx.commits) if ctx.commits else "(no commits)"
    files_block = "\n".join(ctx.changed_files) if ctx.changed_files else "(none)"

    return f"""## Branch
`{ctx.current_branch}` (vs `{ctx.base_branch}`)

## Commits ({len(ctx.commits)})
{commits_block}

## Changed Files
{files_block}

## Diff Stats
{ctx.diff_stat or "(empty)"}

## Full Diff
```diff
{ctx.diff or "(empty)"}
```

Please review this branch and provide structured feedback."""


class LLMError(Exception):
    pass


def get_feedback(ctx: GitContext, model: str | None = None) -> str:
    prompt = _build_prompt(ctx)
    payload = {
        "model": model or settings.ollama_model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "stream": False,
    }

    try:
        with httpx.Client(timeout=settings.ollama_timeout) as client:
            resp = client.post(f"{settings.ollama_url}/api/chat", json=payload)
            resp.raise_for_status()
    except httpx.ConnectError:
        raise LLMError(
            f"Could not connect to Ollama at {settings.ollama_url}.\n"
            "Is the Docker container running?  Try: docker compose up -d"
        )
    except httpx.HTTPStatusError as e:
        raise LLMError(
            f"Ollama returned an error: {e.response.status_code} - {e.response.text}"
        )

    return resp.json()["message"]["content"]
