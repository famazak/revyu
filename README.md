# Feedy

AI-powered local code reviews for your feature branches. Feedy is a CLI tool that analyzes your git branch diff and provides structured, actionable feedback using a locally hosted LLM via [Ollama](https://ollama.com) — no code ever leaves your machine.

## Features

- **Local-first** — All analysis happens on your machine using Ollama. Your code stays private.
- **Auto-detection** — Automatically detects the base branch (`main`, `master`, `develop`, etc.) so you can just run `feedy` and go.
- **Structured feedback** — Issues are categorized by severity (CRITICAL, HIGH, MEDIUM, LOW, NIT) across security, correctness, code quality, and performance.
- **Rich terminal output** — Feedback is rendered as styled Markdown panels in your terminal.
- **Configurable** — Control the model, diff size limits, commit count, and more via environment variables or a `.env` file.

## Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3.13+ |
| Package manager | [uv](https://docs.astral.sh/uv/) |
| Build backend | [Hatchling](https://hatch.pypa.io/) |
| CLI framework | [Typer](https://typer.tiangolo.com/) |
| Terminal rendering | [Rich](https://rich.readthedocs.io/) |
| HTTP client | [httpx](https://www.python-httpx.org/) |
| Configuration | [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) |
| LLM backend | [Ollama](https://ollama.com) |
| Containerization | Docker + Docker Compose |

## Prerequisites

- **Python 3.13+**
- **Git**
- **Ollama** — running locally or via Docker (the included `docker-compose.yml` handles this for you)

## Install from PyPI

```bash
# With uv (recommended)
uv tool install feedy

# Or with pip
pip install feedy
```

Then run it from any git repository on a feature branch:

```bash
feedy
```

## Usage with Docker (no Python required)

If you don't have Python installed, you can run Feedy entirely via Docker. There are two approaches depending on whether you already have Ollama running.

### Option A: You already have Ollama running

If Ollama is running on your host machine (e.g. via `brew install ollama` or the [Ollama desktop app](https://ollama.com/download)), you can run Feedy directly from your project's root directory:

```bash
docker run --rm \
  -v "$(pwd):/repo:ro" \
  -e FEEDY_OLLAMA_URL=http://host.docker.internal:11434 \
  ghcr.io/<your-org>/feedy:latest
```

`host.docker.internal` allows the container to reach Ollama on your host machine. Pass any CLI flags after the image name:

```bash
docker run --rm \
  -v "$(pwd):/repo:ro" \
  -e FEEDY_OLLAMA_URL=http://host.docker.internal:11434 \
  ghcr.io/<your-org>/feedy:latest \
  --base-branch develop --model codellama
```

To simplify repeated use, add a shell alias to your profile (`~/.bashrc`, `~/.zshrc`, etc.):

```bash
alias feedy='docker run --rm -v "$(pwd):/repo:ro" -e FEEDY_OLLAMA_URL=http://host.docker.internal:11434 ghcr.io/<your-org>/feedy:latest'
```

Then just run:

```bash
cd ~/projects/myapp
feedy
feedy --base-branch develop
feedy --model codellama --no-diff
```

### Option B: Run everything with Docker Compose

If you don't have Ollama installed at all, the included `docker-compose.yml` runs both Ollama and Feedy together:

```bash
# Clone feedy (only needed once, for the docker-compose.yml)
git clone https://github.com/<your-org>/feedy.git ~/feedy

# Start the Ollama service
docker compose -f ~/feedy/docker-compose.yml up -d

# Run feedy against your project
GEN_FEEDBACK_REPO_PATH=/path/to/your/repo \
  docker compose -f ~/feedy/docker-compose.yml run --rm feedy
```

The `feedy` service is under the `tools` profile, so it only runs on demand via `docker compose run` — it won't start with a bare `docker compose up`.

You can also override configuration:

```bash
FEEDY_OLLAMA_MODEL=codellama GEN_FEEDBACK_REPO_PATH=~/projects/myapp \
  docker compose -f ~/feedy/docker-compose.yml run --rm feedy --base-branch develop
```

## CLI Usage

```
feedy [OPTIONS]
```

| Option | Short | Description |
|---|---|---|
| `--base-branch` | `-b` | Branch to diff against. Auto-detected if omitted. |
| `--model` | `-m` | Ollama model to use (default: `llama3.2`). |
| `--no-diff` | | Skip the full diff — use only commits and file list. |
| `--repo` | | Path to the git repo (defaults to current directory). |
| `--help` | | Show help and exit. |

### Examples

```bash
# Review the current branch (auto-detects base branch)
feedy

# Review against a specific base branch
feedy --base-branch develop

# Use a different model
feedy --model codellama

# Review a repo in another directory
feedy --repo ~/projects/myapp

# Skip the full diff for very large branches
feedy --no-diff
```

## Configuration

Feedy is configured via environment variables (prefixed with `FEEDY_`) or a `.env` file in the working directory.

| Variable | Default | Description |
|---|---|---|
| `FEEDY_OLLAMA_URL` | `http://localhost:11434` | Ollama server URL. |
| `FEEDY_OLLAMA_MODEL` | `llama3.2` | Default Ollama model. |
| `FEEDY_OLLAMA_TIMEOUT` | `120.0` | Request timeout in seconds. |
| `FEEDY_MAX_COMMITS` | `20` | Maximum number of commits to include in the review. |
| `FEEDY_MAX_DIFF_CHARS` | `8000` | Maximum diff size in characters. Fails if exceeded. |

Example `.env` file:

```env
FEEDY_OLLAMA_URL=http://localhost:11434
FEEDY_OLLAMA_MODEL=codellama
FEEDY_OLLAMA_TIMEOUT=180
FEEDY_MAX_COMMITS=30
FEEDY_MAX_DIFF_CHARS=12000
```

## Development Setup

### Clone and install

```bash
git clone https://github.com/<your-org>/feedy.git
cd feedy

# Install dependencies (creates a virtual environment automatically)
uv sync

# Run feedy locally
uv run feedy
```

### Running tests

```bash
uv run pytest
```

### Project structure

```
src/feedy/
  cli.py        # CLI entrypoint (Typer app)
  git.py        # Git operations — branch detection, diff collection
  llm.py        # Ollama integration — prompt building, API calls
  settings.py   # Configuration via Pydantic Settings
```

## Contributing

1. Create a feature branch from `main`.
2. Make your changes.
3. Run tests: `uv run pytest`
4. Open a pull request.

## Publishing to PyPI

### Manual publish

```bash
# Build source and wheel distributions
uv build

# Publish (requires a PyPI API token)
uv publish --token $PYPI_TOKEN
```

### Automated publish with GitHub Actions

Create `.github/workflows/publish.yml`:

```yaml
name: Publish to PyPI

on:
  push:
    tags:
      - "v*"

jobs:
  publish:
    runs-on: ubuntu-latest
    environment:
      name: pypi
    permissions:
      id-token: write
      contents: read
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - run: uv python install 3.13
      - run: uv build
      - run: uv publish
```

To use this workflow:

1. Create a `pypi` environment in your GitHub repo settings (**Settings > Environments**).
2. Add a [trusted publisher](https://docs.pypi.org/trusted-publishers/adding-a-publisher/) to your PyPI project matching the repository and workflow name.
3. Create and push a release tag:

**Typical workflow:**

Tags should be created on the `main` branch **after** merging your feature branch. Here's the recommended process:

```bash
# 1. Merge your feature branch via pull request on GitHub
# 2. Switch to main and pull the latest changes
git checkout main
git pull origin main

# 3. Bump the version in pyproject.toml (e.g., from 0.0.9 to 0.1.0)
# Edit pyproject.toml manually or use a tool

# 4. Commit the version bump
git add pyproject.toml
git commit -m "Bump version to 0.1.0"
git push origin main

# 5. Create and push the tag (use the same version as in pyproject.toml)
git tag v0.1.0
git push origin v0.1.0
```

The tag push triggers the GitHub Actions workflow, which builds and publishes to PyPI automatically.

## Publishing Docker to GitHub Container Registry

### Manual publish

```bash
# Build the image
docker build -t feedy .

# Tag for GHCR
docker tag feedy ghcr.io/<your-org>/feedy:latest
docker tag feedy ghcr.io/<your-org>/feedy:0.1.0

# Authenticate with GHCR
echo $GITHUB_TOKEN | docker login ghcr.io -u <your-username> --password-stdin

# Push
docker push ghcr.io/<your-org>/feedy:latest
docker push ghcr.io/<your-org>/feedy:0.1.0
```

### Automated publish with GitHub Actions

Create `.github/workflows/docker.yml`:

```yaml
name: Publish Docker to GHCR

on:
  push:
    tags:
      - "v*"

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    steps:
      - uses: actions/checkout@v4

      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - uses: docker/metadata-action@v5
        id: meta
        with:
          images: ghcr.io/${{ github.repository }}
          tags: |
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=raw,value=latest

      - uses: docker/build-push-action@v6
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
```

This workflow triggers on version tags, builds the Docker image, and pushes it to `ghcr.io/<your-org>/feedy` with semantic version tags.

## License

TBD
