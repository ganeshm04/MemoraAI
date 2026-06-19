import asyncio
import os
import sys
from datetime import datetime

# Add root directory to python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.evaluation.evaluator import RAGEvaluator


def get_status_emoji(score: float) -> str:
    if score >= 0.85:
        return "🟢 Excellent"
    elif score >= 0.70:
        return "🟡 Degraded"
    else:
        return "🔴 Failed"


async def main():
    print("=" * 60)
    print("         MemoraAI - RAG Pipeline Quality Evaluation")
    print("=" * 60)

    dataset_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "app", "evaluation", "dataset.json"
    )

    evaluator = RAGEvaluator(dataset_path)

    print(f"Loading QA dataset from {dataset_path}...")
    try:
        summary = await evaluator.run_evaluation()
    except Exception as e:
        print(f"CRITICAL: Evaluation run failed: {str(e)}", file=sys.stderr)
        sys.exit(1)

    print("\nEvaluation complete! Formatting report...")

    # Calculate status strings
    avg_faith = summary["average_faithfulness"]
    avg_rel = summary["average_relevance"]
    avg_rec = summary["average_recall"]

    faith_status = get_status_emoji(avg_faith)
    relevance_status = get_status_emoji(avg_rel)
    recall_status = get_status_emoji(avg_rec)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Generate Markdown Report Content
    report_lines = [
        "# MemoraAI — RAG Pipeline Quality Report",
        "",
        f"**Generated on:** {timestamp} (Local System Time)",
        "",
        "## 📊 Summary Performance Metrics",
        "",
        "| Evaluation Dimension | Metric Type | Score | Target Status |",
        "| :--- | :--- | :--- | :--- |",
        f"| **Faithfulness** | Hallucination Index | `{avg_faith:.2f} / 1.00` | {faith_status} |",
        f"| **Answer Relevance** | Responsive Score | `{avg_rel:.2f} / 1.00` | {relevance_status} |",
        f"| **Context Recall** | Information Extraction | `{avg_rec:.2f} / 1.00` | {recall_status} |",
        "",
        "> [!IMPORTANT]",
        "> **Faithfulness (Hallucination Index)** measures if the generated answer relies *only* on the retrieved context.",
        "> **Answer Relevance** evaluates if the answer directly addresses the query topic.",
        "> **Context Recall** checks if the RAG search retrieved all the facts present in the ground-truth reference answer.",
        "",
        "---",
        "",
        "## 🔬 Individual Evaluation Test Cases",
        ""
    ]

    for item in summary["results"]:
        q_id = item["id"]
        query = item["query"]
        ref_ans = item["reference_answer"]
        gen_ans = item["generated_answer"]
        chunks_count = item["retrieved_chunks_count"]
        
        faith_score = item["faithfulness"].get("score", 0.0)
        faith_reason = item["faithfulness"].get("reasoning", "No explanation provided.")
        
        rel_score = item["relevance"].get("score", 0.0)
        rel_reason = item["relevance"].get("reasoning", "No explanation provided.")
        
        rec_score = item["recall"].get("score", 0.0)
        rec_reason = item["recall"].get("reasoning", "No explanation provided.")

        report_lines.extend([
            f"### Test Case `{q_id}`: *\"{query}\"*",
            "",
            f"- **Retrieved Context Chunks Count:** {chunks_count}",
            "- **Score Overview:**",
            f"  - **Faithfulness:** `{faith_score:.2f}` ({get_status_emoji(faith_score)})",
            f"  - **Relevance:** `{rel_score:.2f}` ({get_status_emoji(rel_score)})",
            f"  - **Context Recall:** `{rec_score:.2f}` ({get_status_emoji(rec_score)})",
            "",
            "#### Factual Alignment & Responses",
            "```text",
            f"Reference Answer: {ref_ans}",
            "---",
            f"Generated Answer: {gen_ans}",
            "```",
            "",
            "#### Judge Evaluations Reasoning",
            "> [!NOTE]",
            f"> **Faithfulness Judgment:** {faith_reason}",
            ">",
            f"> **Relevance Judgment:** {rel_reason}",
            ">",
            f"> **Recall Judgment:** {rec_reason}",
            "",
            "---",
            ""
        ])

    report_content = "\n".join(report_lines)

    # Save to docs folder
    docs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs")
    os.makedirs(docs_dir, exist_ok=True)
    report_path = os.path.join(docs_dir, "RAG_EVALUATION_REPORT.md")

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)

    print("=" * 60)
    print("                Evaluation Metrics Summary")
    print("=" * 60)
    print(f"Faithfulness Score : {avg_faith:.2f} / 1.00 ({faith_status})")
    print(f"Answer Relevance   : {avg_rel:.2f} / 1.00 ({relevance_status})")
    print(f"Context Recall Score: {avg_rec:.2f} / 1.00 ({recall_status})")
    print("-" * 60)
    print(f"Detailed Markdown report successfully written to: {report_path}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
