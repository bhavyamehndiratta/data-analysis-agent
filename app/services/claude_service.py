import os
import pandas as pd
from anthropic import Anthropic

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

MAX_ITERATIONS = 5

def build_dataset_context(filepath: str) -> str:
    if filepath.endswith(".csv"):
        df = pd.read_csv(filepath)
    else:
        df = pd.read_excel(filepath)

    preview = df.head(3).to_string(index=False)
    dtypes = df.dtypes.to_string()
    shape = f"{len(df)} rows x {len(df.columns)} columns"

    return f"""Dataset shape: {shape}

Column types:
{dtypes}

First 5 rows:
{preview}
"""

def extract_follow_up_questions(answer: str) -> list[str]:
    """Ask Claude to identify follow-up questions worth investigating from an answer."""
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        messages=[{
            "role": "user",
            "content": f"""Given this data analysis result:

{answer}

Identify up to 2 specific follow-up questions that would meaningfully deepen understanding of this result. 
Only suggest questions that could be answered with the same dataset.
Return ONLY the questions, one per line, no numbering, no explanation."""
        }]
    )
    
    text = response.content[0].text.strip()
    questions = [q.strip() for q in text.split("\n") if q.strip()]
    return questions[:2]

def run_analysis(filepath: str, question: str, depth: int = 0, max_depth: int = 2) -> dict:
    dataset_context = build_dataset_context(filepath)

    system_prompt = """Data analysis agent. Use code execution to answer questions accurately. Be concise.
- Never guess. Always run code.
- Fix errors and retry.
- Flag statistical caveats briefly.
"""

    user_message = f"""Here is the dataset:

{dataset_context}

To use it in code, load it like this:
```python
import pandas as pd
import io

data = \"\"\"
{open(filepath).read()}
\"\"\"
df = pd.read_csv(io.StringIO(data))
```

Question: {question}
"""

    messages = [{"role": "user", "content": user_message}]
    
    iterations = 0
    code_executed = []
    final_answer = ""

    while iterations < MAX_ITERATIONS:
        iterations += 1

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=system_prompt,
            tools=[{"type": "code_execution_20250522", "name": "code_execution"}],
            messages=messages
        )

        # Collect text and tool use blocks from this response
        assistant_content = response.content
        messages.append({"role": "assistant", "content": assistant_content})

        # Check if Claude is done
        if response.stop_reason == "end_turn":
            for block in assistant_content:
                if hasattr(block, "text"):
                    final_answer += block.text
            break

        # If Claude used a tool, feed results back and continue
        if response.stop_reason == "tool_use":
            tool_results = []
            for block in assistant_content:
                if block.type == "tool_use":
                    code_executed.append(block.input.get("code", ""))
                    # The hosted execution tool returns results automatically
                    # We just need to acknowledge the tool use to continue
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": "Code executed successfully via hosted execution."
                    })
            
            messages.append({"role": "user", "content": tool_results})

    # Bounded drill-down — agent investigates follow-up questions autonomously
    drill_down_results = []
    if depth < max_depth and final_answer:
        follow_ups = extract_follow_up_questions(final_answer)
        for follow_up in follow_ups[:2]:  # max 2 follow-ups per level
            drill_result = run_analysis(filepath, follow_up, depth=depth+1, max_depth=max_depth)
            drill_down_results.append({
                "question": follow_up,
                "answer": drill_result["answer"]
            })

    return {
        "answer": final_answer,
        "code_executed": code_executed,
        "iterations": iterations,
        "stop_reason": response.stop_reason,
        "drill_down": drill_down_results
    }