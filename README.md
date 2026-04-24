# Soul Society agent simulator

A Bleach-themed Wumpus world project using Flask and SWI-Prolog.

## Project structure
- `app.py`: Flask backend and WorldState logic.
- `tests.py`: Batch test runner for simulation performance analysis.
- `prolog/kb.pl`: Prolog knowledge base and inference rules.
- `templates/`: HTML frontend.
- `static/`: CSS and JS assets.

## How to Run

### Option 1: python
1. SWI-Prolog must be installed on your system.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the app:
   ```bash
   python app.py
   ```
4. Run performance tests:
   ```bash
   python tests.py
   ```

### Option 2: Docker
1. Build the Docker image:
   ```bash
   docker build -t bleach-world .
   ```
2. Run the container:
   ```bash
   docker run -p 8000:8000 bleach-world
   ```
3. Access the simulator at `http://localhost:8000`.
