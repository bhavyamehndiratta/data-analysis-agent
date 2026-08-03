import json
import time
import sqlite3
from datetime import datetime
from app.services.claude_service import run_analysis
from app.database import get_db

QUESTION_CATEGORIES = [
    "direct_query",
    "aggregation", 
    "trend_analysis",
    "segmentation",
    "anomaly_detection",
    "statistical_significance",
    "multi_step_causal"
]

def init_eval_tables():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS eval_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL,
            dataset_path TEXT NOT NULL,
            total_questions INTEGER,
            accuracy REAL,
            hallucination_rate REAL,
            avg_iterations REAL,
            median_latency_ms REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS eval_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL,
            question TEXT NOT NULL,
            category TEXT NOT NULL,
            expected_answer TEXT,
            actual_answer TEXT,
            correct INTEGER,
            hallucinated INTEGER,
            iterations INTEGER,
            latency_ms REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def judge_answer(question: str, expected: str, actual: str) -> dict:
    """Use Claude to judge whether the actual answer matches the expected answer."""
    from anthropic import Anthropic
    import os
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=256,
        messages=[{
            "role": "user",
            "content": f"""You are evaluating a data analysis agent's answer.

Question: {question}
Expected answer: {expected}
Actual answer: {actual}

Respond with JSON only, no explanation:
{{
  "correct": true or false,
  "hallucinated": true or false,
  "reasoning": "one sentence"
}}

correct = the actual answer captures the key facts of the expected answer
hallucinated = the actual answer states specific facts not supported by the data"""
        }]
    )

    text = response.content[0].text.strip()
    text = text.replace("```json", "").replace("```", "").strip()
    return json.loads(text)

def run_eval(filepath: str, test_cases: list[dict]) -> dict:
    """
    test_cases: list of dicts with keys:
        - question: str
        - expected_answer: str  
        - category: str (from QUESTION_CATEGORIES)
    """
    import uuid
    run_id = str(uuid.uuid4())
    results = []

    for case in test_cases:
        start = time.time()
        
        try:
            result = run_analysis(filepath, case["question"], max_depth=0)  # no drill-down during eval
            actual_answer = result["answer"]
            iterations = result["iterations"]
        except Exception as e:
            actual_answer = f"ERROR: {str(e)}"
            iterations = 0

        latency_ms = (time.time() - start) * 1000

        # Judge the answer
        try:
            judgment = judge_answer(case["question"], case["expected_answer"], actual_answer)
            correct = judgment["correct"]
            hallucinated = judgment["hallucinated"]
        except Exception:
            correct = False
            hallucinated = False

        results.append({
            "run_id": run_id,
            "question": case["question"],
            "category": case["category"],
            "expected_answer": case["expected_answer"],
            "actual_answer": actual_answer,
            "correct": int(correct),
            "hallucinated": int(hallucinated),
            "iterations": iterations,
            "latency_ms": latency_ms
        })

    # Compute aggregate metrics
    total = len(results)
    accuracy = sum(r["correct"] for r in results) / total
    hallucination_rate = sum(r["hallucinated"] for r in results) / total
    avg_iterations = sum(r["iterations"] for r in results) / total
    latencies = sorted(r["latency_ms"] for r in results)
    median_latency = latencies[total // 2]

    # Store in SQLite
    conn = get_db()
    conn.execute(
        "INSERT INTO eval_runs (run_id, dataset_path, total_questions, accuracy, hallucination_rate, avg_iterations, median_latency_ms) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (run_id, filepath, total, accuracy, hallucination_rate, avg_iterations, median_latency)
    )
    for r in results:
        conn.execute(
            "INSERT INTO eval_results (run_id, question, category, expected_answer, actual_answer, correct, hallucinated, iterations, latency_ms) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (r["run_id"], r["question"], r["category"], r["expected_answer"], r["actual_answer"], r["correct"], r["hallucinated"], r["iterations"], r["latency_ms"])
        )
    conn.commit()
    conn.close()

    return {
        "run_id": run_id,
        "total_questions": total,
        "accuracy": round(accuracy, 3),
        "hallucination_rate": round(hallucination_rate, 3),
        "avg_iterations": round(avg_iterations, 2),
        "median_latency_ms": round(median_latency, 1),
        "results": results
    }