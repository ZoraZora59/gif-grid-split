# Repository Guidelines

## Project Structure & Module Organization
- `core/`: grid detection, slicing, GIF assembly (`detector.py`, `slicer.py`, `gif_maker.py`); keep heavy lifting and reusable logic here.
- `web/`: Flask app entry (`app.py`), UI (`templates/index.html`), and assets (`static/js/app.js`, `static/css/style.css`); uploads live under `web/uploads/`.
- `cli/`: command-line flows (`run.py`, `slice_spritesheet.py`, `make_gif.py`, `auto_detect.py`) mirroring web behavior.
- `examples/`: sample sprite sheets (e.g., `examples/柯南攻击图片.jpg`) for quick smoke tests.
- `docs/`: deployment notes; `Dockerfile` for container builds; `requirements.txt` for pinned Python deps.

## Setup, Build, and Development Commands
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# Web dev server
python web/app.py
# Production-style
gunicorn -w 4 -b 0.0.0.0:5000 web.app:app
# CLI samples
python cli/slice_spritesheet.py -i examples/柯南攻击图片.jpg --auto
python cli/make_gif.py -i frames -o demo.gif
```
- Set `ZENMUX_API_KEY` (and optional `ZENMUX_BASE_URL`, `ZENMUX_GEMINI_MODEL`) in your shell; never commit secrets.

## Coding Style & Naming Conventions
- Python 3.8+: 4-space indentation, snake_case for functions/variables, concise docstrings; keep user-facing copy bilingual where it already is.
- Frontend: vanilla JS and CSS in `web/static`; match existing class names and neon/cyber aesthetic; prefer small helpers over new frameworks.
- Keep core logic testable (pure functions in `core/`), and minimize side effects in CLI/web glue code.

## Testing Guidelines
- No formal suite yet; add `pytest` cases when touching `core/` algorithms (edge detection, grid guesses, GIF assembly) and keep fixtures small.
- Minimum manual smoke before opening a PR: run the web server locally, upload the sample sheet, confirm preview + download; run the two CLI commands above.

## Commit & Pull Request Guidelines
- Follow the existing style: `feat: ...`, `fix: ...` (often in Chinese). Keep scopes small and messages imperative.
- PRs should include: summary of intent, user impact, manual test notes (commands run), and screenshots/GIFs for UI changes.
- Link related issues, call out config/env needs, and highlight any backward-incompatible behavior.

## Security & Configuration Tips
- Secrets only via environment variables; do not hardcode API keys or paths.
- Uploaded files are temporary; if you change retention logic or storage paths (`web/uploads/`), document the behavior and clean-up schedule.
