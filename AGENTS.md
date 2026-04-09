# Repository Guidelines

## Project Structure & Module Organization
- `app.py`: Streamlit UI and user workflow (setup, query preview, run, results, history).
- `main.py`: orchestration layer that connects agent modules.
- `agent/`: core pipeline modules:
  - `query_builder.py`, `llm_runner.py`, `parser.py`, `scorer.py`, `report.py`
- `integrations/`: optional external connectors (Google Search Console, Sheets).
- `utils/`: shared models, config loading, storage helpers.
- `data/results/`: local JSON audit history and artifacts.
- `README.md`: setup and sample input references.

## Build, Test, and Development Commands
- `python3 -m venv .venv && source .venv/bin/activate`: create and activate local environment.
- `pip install -r requirements.txt`: install dependencies.
- `streamlit run app.py`: run the application locally.
- `python3 -m compileall app.py main.py agent integrations utils`: fast syntax/import sanity check.

## Coding Style & Naming Conventions
- Language: Python 3 with 4-space indentation and type hints for public functions.
- Use `snake_case` for functions/variables/files, `PascalCase` for dataclasses/enums.
- Keep modules focused: one clear responsibility per file.
- Prefer small pure functions in `agent/` and shared helpers in `utils/`.
- Keep user-facing copy concise and marketing-friendly.

## Testing Guidelines
- Current baseline: compile-time checks via `python3 -m compileall`.
- Add tests under a future `tests/` directory using `pytest`.
- Test file naming: `test_<module>.py` (example: `test_parser.py`).
- Focus test coverage on scoring logic, parser extraction, and query generation determinism.

## Commit & Pull Request Guidelines
- Commit format: imperative, scoped subject line (example: `parser: improve competitor alias matching`).
- Keep commits focused; avoid mixing refactors with feature changes.
- PRs should include:
  - what changed and why,
  - impacted files/modules,
  - local validation steps and outputs,
  - UI screenshots for `app.py` changes.

## Security & Configuration Tips
- Never commit secrets. Use `.env` for `OPENROUTER_API_KEY` and local integration keys.
- Keep OAuth files (`integrations/credentials.json`, `integrations/token.json`) out of version control.
- Treat audit outputs in `data/results/` as potentially sensitive marketing data.
