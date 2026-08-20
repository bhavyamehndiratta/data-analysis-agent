# Data Analysis Agent

[▶ Watch demo](docs/demo.mov)

An agentic AI system that lets you upload any CSV or Excel dataset and ask questions about it in plain English. The agent autonomously writes Python analysis code, executes it, self-corrects errors, and returns statistically-validated insights in real time.

## Architecture
User Question
↓
FastAPI Backend
↓
Claude API (claude-sonnet-4-6)
↓
Hosted Code Execution (Anthropic sandbox)
↓
Agent Loop (write → execute → read → self-correct)
↓
Bounded Drill-Down (autonomous follow-up investigation)
↓
Self-Critique (statistical soundness check)
↓
Streaming Response → User

## Features

- **File Upload** — CSV and Excel support with automatic data quality checks (missing values, duplicates, type inference)
- **Agent Loop** — iterative code execution with self-correction, capped at 5 iterations
- **Bounded Drill-Down** — agent autonomously investigates follow-up findings up to 2 levels deep
- **Self-Critique** — agent checks its own answer for statistical soundness before returning
- **Streaming** — real-time response streaming via Server-Sent Events
- **Evaluation Harness** — LLM-as-judge evaluation with accuracy, hallucination rate, latency, and self-correction metrics tracked per run

## Tech Stack

- **Backend:** Python, FastAPI
- **LLM:** Claude API (claude-sonnet-4-6) with hosted code execution
- **Database:** SQLite (session persistence, analysis history, eval data)
- **Streaming:** Server-Sent Events (SSE)

## Setup

```bash
# Clone the repo
git clone https://github.com/bhavyamehndiratta/data-analysis-agent.git
cd data-analysis-agent

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install fastapi uvicorn anthropic python-multipart pandas openpyxl python-dotenv

# Add your Anthropic API key
echo "ANTHROPIC_API_KEY=your_key_here" > .env

# Run the server
uvicorn main:app --reload
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/upload` | Upload CSV/Excel, returns session_id and data quality report |
| POST | `/api/analyze` | Run full agent loop on a question |
| POST | `/api/stream` | Stream agent response in real time |
| POST | `/api/eval` | Run evaluation harness on a labeled test set |
| GET | `/api/eval/{run_id}` | Retrieve results of a previous eval run |

## Evaluation

The eval harness uses LLM-as-judge scoring — Claude evaluates whether the agent's answer captures the key facts of the expected answer, and flags hallucinations (facts stated but not supported by the data).

Metrics tracked per eval run:
- **Accuracy** — % of questions answered correctly
- **Hallucination rate** — % of answers containing unsupported facts
- **Avg iterations** — average self-correction attempts per question
- **Median latency** — p50 response time in ms

## Evaluation Results

Run on a 20-row employee dataset (5 questions across 3 categories):

| Metric | Result |
|--------|--------|
| Overall accuracy | 60% (3/5) — 80% excluding eval harness labeling error |
| Hallucination rate | 20% |
| Median latency | 21.6 seconds |
| Avg self-correction iterations | 1.0 |
| Test categories | aggregation, direct_query, statistical_significance |

## Sample Eval Test Case

```json
{
  "session_id": "your-session-id",
  "test_cases": [
    {
      "question": "What is the average salary by city?",
      "expected_answer": "Toronto: 95000, Vancouver: 72000, Montreal: 88000",
      "category": "aggregation"
    }
  ]
}
```