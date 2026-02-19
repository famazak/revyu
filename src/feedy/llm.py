import httpx

from .git import GitContext
from .settings import settings

SYSTEM_PROMPT = """"""


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
