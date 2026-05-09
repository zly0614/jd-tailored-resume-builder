# Jianli Creator

Jianli Creator is a local resume-generation project for job applications.

You maintain one master profile as a knowledge base. For each new application, you only paste a target JD and the system generates a tailored LaTeX resume. Each round of user feedback is stored in `memory.md` and reused in later generations.

## Features

- Store a full candidate profile in `JSON`
- Parse job descriptions from plain text
- Rank relevant work and project experience before generation
- Use an OpenAI-compatible model when available
- Fall back to heuristic generation when `OPENAI_API_KEY` is missing
- Save user feedback into `memory.md`
- Reuse feedback as preference memory in later generations
- Provide a local Web UI for profile input, JD input, output preview, download, and feedback

## Project Structure

```text
resume_builder/
  __init__.py
  __main__.py
  cli.py
  jd_parser.py
  latex_renderer.py
  llm.py
  memory.py
  models.py
  profile_loader.py
  ranking.py
  service.py
  web.py
  templates/
    index.html
data/
  master_profile.sample.json
  sample_jd.txt
outputs/
tests/
  test_generation.py
memory.md
```

## CLI Usage

Generate a resume:

```powershell
conda run -n test python -m resume_builder generate `
  --profile data/master_profile.sample.json `
  --jd-file data/sample_jd.txt `
  --out outputs/resume.tex
```

Append feedback manually:

```powershell
conda run -n test python -m resume_builder feedback `
  --memory-file memory.md `
  --target-role "AI Product Manager" `
  --feedback "Emphasize measurable impact and knowledge-base work."
```

## Web UI

Start the local server:

```powershell
conda run -n test python -m resume_builder serve --host 127.0.0.1 --port 8000
```

Open:

`http://127.0.0.1:8000`

The page supports:

- pasting profile JSON
- pasting a JD
- choosing `llm` or `heuristic` mode
- previewing generated LaTeX
- downloading the `.tex` file
- sending feedback into `memory.md`

## Model Configuration

Optional environment variables:

- `OPENAI_API_KEY`
- `OPENAI_MODEL` default: `gpt-4.1-mini`
- `OPENAI_BASE_URL` default: `https://api.openai.com/v1`

## Tests

```powershell
conda run -n test python -m unittest discover -s tests
```
