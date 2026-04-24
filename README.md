# Soul Society agent simulator

A Bleach-themed Wumpus world project using Flask and SWI-Prolog.

## Project structure
- `app.py`: Flask backend and WorldState logic.
- `tests.py`: Batch test runner for simulation performance analysis.
- `prolog/kb.pl`: Prolog knowledge base and inference rules.
- `templates/`: HTML frontend.
- `static/`: CSS and JS assets.

## Setup
1. Install SWI-Prolog on your system.
2. Install dependencies: `pip install -r requirements.txt`
3. Run the app: `python app.py`
4. Run tests: `python tests.py`
