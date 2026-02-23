"""CLI entrypoint — registered as the `gen-feedback` command."""

from typing import Annotated

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from .git import GitError, collect
from .llm import LLMError, get_feedback
from .settings import settings

app = typer.Typer(
    name="revyu",
    help="AI-powered git branch feedback from your local LLM.",
    add_completion=False,
)
console = Console()
err_console = Console(stderr=True, style="bold red")


@app.command()
def main(
    base_branch: Annotated[
        str | None,
        typer.Option(
            "--base-branch",
            "-b",
            help="Branch to diff against. Auto-detected if omitted.",
        ),
    ] = None,
    model: Annotated[
        str | None,
        typer.Option(
            "--model",
            "-m",
            help=f"Ollama model to use (default: {settings.ollama_model}).",
        ),
    ] = None,
    no_diff: Annotated[
        bool,
        typer.Option(
            "--no-diff", help="Skip the full diff — use only commits and file list."
        ),
    ] = False,
    repo: Annotated[
        str | None,
        typer.Option(
            "--repo", help="Path to the git repo (defaults to current directory)."
        ),
    ] = None,
) -> None:
    """
    Analyze the current git branch and print AI-powered feedback.

    Run from inside any git repository:

        gen-feedback

    Or point it at a specific repo and base branch:

        gen-feedback --repo ~/projects/myapp --base-branch develop
    """

    # ── 1. Collect git context ───────────────────────────────────────
    console.print()
    with console.status("[bold cyan]Reading git context…[/bold cyan]", spinner="dots"):
        try:
            ctx = collect(
                base_branch=base_branch,
                max_commits=settings.max_commits,
                max_diff_chars=0 if no_diff else settings.max_diff_chars,
                repo_path=repo,
            )
        except GitError as e:
            err_console.print(f"\n✗ Git error: {e}")
            raise typer.Exit(code=1)

    # Print a quick summary of what we found
    console.print(
        Panel(
            f"[bold]{ctx.current_branch}[/bold] → [dim]{ctx.base_branch}[/dim]\n"
            f"{len(ctx.commits)} commit(s) · {len(ctx.changed_files)} file(s) changed",
            title="[cyan]Branch Context[/cyan]",
            expand=False,
        )
    )

    if not ctx.commits and not ctx.changed_files:
        console.print(
            "[yellow]⚠ No commits or changes found versus the base branch.[/yellow]"
        )
        raise typer.Exit(code=0)

    # ── 2. Call the LLM ─────────────────────────────────────────────
    effective_model = model or settings.ollama_model
    console.print(
        f"\n[bold cyan]Asking [green]{effective_model}[/green] for feedback…[/bold cyan]\n"
    )

    with console.status("[bold cyan]Thinking…[/bold cyan]", spinner="dots"):
        try:
            feedback = get_feedback(ctx, model=effective_model)
        except LLMError as e:
            err_console.print(f"\n✗ LLM error: {e}")
            raise typer.Exit(code=1)

    # ── 3. Render the response ───────────────────────────────────────
    console.print(
        Panel(
            Markdown(feedback),
            title=f"[green]Feedback from {effective_model}[/green]",
            border_style="green",
            padding=(1, 2),
        )
    )
    console.print()


if __name__ == "__main__":
    app()
