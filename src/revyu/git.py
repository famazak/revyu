import subprocess
from dataclasses import dataclass, field


class GitError(Exception):
    pass


@dataclass
class GitContext:
    current_branch: str
    base_branch: str
    commits: list[str] = field(default_factory=list)
    diff_stat: str = ""
    diff: str = ""
    changed_files: list[str] = field(default_factory=list)


def _run(args: list[str], cwd: str | None = None) -> str:
    """Wrapper function to run a git command, returning stdout"""
    try:
        result = subprocess.run(args, capture_output=True, text=True, cwd=cwd)
    except FileNotFoundError:
        raise GitError("git is not installed or on the PATH")

    if result.returncode != 0:
        raise GitError(result.stderr.strip() or f"Command failed: {' '.join(args)}")

    return result.stdout.strip()


def collect(
    base_branch: str | None = None,
    max_commits: int = 20,
    max_diff_chars: int = 8000,
    repo_path: str | None = None,
) -> GitContext:
    cwd = repo_path  # None repo_path has subprocess use CWD
    current_branch = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd)
    if current_branch == "HEAD":
        raise GitError("Detached HEAD state detected, checkout a branch first")

    if base_branch is None:
        base_branch = _detect_base_branch(current_branch, cwd)

    if current_branch == base_branch:
        raise GitError(
            f"Current branch {current_branch} is the same as the base branch, checkout a feature branch first"
        )

    log = _run(
        [
            "git",
            "log",
            f"{base_branch}..{current_branch}",
            f"--max-count={max_commits}",
            "--pretty=format:- %s (%h)",
        ],
        cwd,
    )

    commits = [line for line in log.splitlines() if line.strip()]

    diff_stat = _run(
        ["git", "diff", "--stat", f"{base_branch}...{current_branch}"], cwd
    )

    full_diff = _run(
        ["git", "diff", f"{base_branch}...{current_branch}"], cwd
    )

    if len(full_diff) > max_diff_chars:
        raise GitError("Git diff is too large")  # TODO: better error message here

    changed = _run(
        ["git", "diff", "--name-only", f"{base_branch}...{current_branch}"], cwd
    )

    changed_files = [f for f in changed.splitlines() if f.strip()]

    return GitContext(
        current_branch=current_branch,
        base_branch=base_branch,
        commits=commits,
        diff_stat=diff_stat,
        diff=full_diff,
        changed_files=changed_files,
    )


def _detect_base_branch(current_branch: str, cwd: str | None) -> str:
    candidates = ["main", "master", "develop", "development"]
    try:
        remote_branches_raw = _run(
            ["git", "branch", "-r", "--format=%(refname:short)"], cwd
        )
        remote_branches = [
            b.split("/", 1)[-1]
            for b in remote_branches_raw.splitlines()
            if b.strip() and "HEAD" not in b
        ]
        candidates += remote_branches
    except GitError:
        pass

    for candidate in candidates:
        if candidate == current_branch:
            continue
        try:
            _run(["git", "rev-parse", "--verify", candidate], cwd)
            return candidate
        except GitError:
            continue

    raise GitError("Could not auto-detect a base branch. Pass one with --base-branch")
