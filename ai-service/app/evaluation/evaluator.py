import json
import os
import structlog
from typing import Optional
from app.config import config
from app.retrieval.pipeline import retrieval_pipeline
from app.generation.gemini import gemini_client, GenerationRequest
from db.connection import db

logger = structlog.get_logger(__name__)

FAITHFULNESS_PROMPT = """
You are a RAG evaluation judge. Your task is to evaluate the FAITHFULNESS of a generated answer with respect to the provided context.
Faithfulness measures whether the generated answer is strictly grounded in the context and does not contain hallucinations or external information.

Context:
{context}

Generated Answer:
{answer}

Evaluate step-by-step:
1. Identify all factual claims in the generated answer.
2. For each claim, verify if it is directly supported by the context.
3. Compute a score between 0.0 and 1.0 (1.0 = all claims are fully grounded, 0.0 = no claims are grounded).

Respond ONLY with a valid JSON object of the following format:
{{
    "reasoning": "Explain your step-by-step evaluation here",
    "score": 0.95
}}
"""

RELEVANCE_PROMPT = """
You are a RAG evaluation judge. Your task is to evaluate the RELEVANCE of a generated answer to the user query.
Answer Relevance measures how directly and completely the generated answer addresses the user query.

User Query:
{query}

Generated Answer:
{answer}

Evaluate step-by-step:
1. Analyze the user's intent in the query.
2. Check if the generated answer directly answers the query without being vague, redundant, or incomplete.
3. Compute a score between 0.0 and 1.0 (1.0 = perfectly relevant and complete, 0.0 = completely irrelevant).

Respond ONLY with a valid JSON object of the following format:
{{
    "reasoning": "Explain your step-by-step evaluation here",
    "score": 0.95
}}
"""

RECALL_PROMPT = """
You are a RAG evaluation judge. Your task is to evaluate the CONTEXT RECALL of the retrieved context with respect to the reference answer.
Context Recall measures whether the retrieved context contains all the key details and facts required to formulate the reference answer (ground truth).

Reference Answer:
{reference_answer}

Retrieved Context:
{context}

Evaluate step-by-step:
1. Identify the key factual details in the reference answer.
2. Check if each detail is present in the retrieved context.
3. Compute a score between 0.0 and 1.0 (1.0 = all key details are present in the context, 0.0 = none are present).

Respond ONLY with a valid JSON object of the following format:
{{
    "reasoning": "Explain your step-by-step evaluation here",
    "score": 0.95
}}
"""


class RAGEvaluator:
    """LLM-as-a-judge automated RAG evaluation system."""

    def __init__(self, dataset_path: str):
        self.dataset_path = dataset_path
        self.test_cases = []

    def load_dataset(self) -> None:
        """Load baseline Q&A test cases."""
        if not os.path.exists(self.dataset_path):
            raise FileNotFoundError(f"Dataset file not found at {self.dataset_path}")
        with open(self.dataset_path, "r", encoding="utf-8") as f:
            self.test_cases = json.load(f)
        logger.info("dataset_loaded", count=len(self.test_cases))

    def _parse_judge_json(self, text: str) -> dict:
        """Robustly parse JSON response from Gemini Judge."""
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            print(f"\nDEBUG: JSON parse failed. Raw response text was:\n{text}\n")
            logger.warning("json_parse_failed_falling_back_to_index_slicing", text=text, error=str(exc))
            
            import re
            
            # 1. Try to find score
            score = 0.0
            score_match = re.search(r'["\']?score["\']?\s*:\s*([0-9.]+)', text, re.IGNORECASE)
            if score_match:
                try:
                    score = float(score_match.group(1))
                except ValueError:
                    pass
            
            # 2. Try to find reasoning
            reasoning = "Failed to parse model JSON reasoning."
            reasoning_start_match = re.search(r'["\']?reasoning["\']?\s*:\s*["\']', text, re.IGNORECASE)
            if reasoning_start_match:
                start_idx = reasoning_start_match.end()
                quote_char = text[start_idx - 1]
                
                # Check if score comes after reasoning
                end_pattern = rf'{quote_char}\s*,\s*["\']?score["\']?'
                end_match = re.search(end_pattern, text[start_idx:], re.IGNORECASE)
                if end_match:
                    end_idx = start_idx + end_match.start()
                    reasoning = text[start_idx:end_idx].strip()
                else:
                    # Look for the last quote character
                    last_quote_idx = text.rfind(quote_char)
                    if last_quote_idx > start_idx:
                        reasoning = text[start_idx:last_quote_idx].strip()
            
            reasoning = reasoning.replace('\\"', '"').replace('\\n', '\n')
            return {"reasoning": reasoning, "score": score}

    async def _query_judge(self, prompt: str) -> dict:
        """Call Gemini to run judge assessment."""
        req = GenerationRequest(
            prompt=prompt,
            system_prompt="You are a precise, objective evaluation judge that outputs raw JSON strictly complying with instructions.",
            temperature=0.1,  # Low temperature for objective scores
            max_tokens=1000,
            response_mime_type="application/json",
        )
        response = await gemini_client.generate(req)
        return self._parse_judge_json(response.text)

    async def run_evaluation(self) -> dict:
        """Run the end-to-end evaluation suite."""
        self.load_dataset()
        results = []

        total_faithfulness = 0.0
        total_relevance = 0.0
        total_recall = 0.0
        success_count = 0

        # Ensure database is active for retrieval query
        db_connected = False
        try:
            await db.connect()
            db_connected = True
        except Exception as e:
            logger.warning("db_connect_skipped_or_failed", error=str(e))

        try:
            for idx, tc in enumerate(self.test_cases, 1):
                query = tc["query"]
                ref_ans = tc["reference_answer"]
                
                print(f"[{idx}/{len(self.test_cases)}] Evaluating query: '{query}'...")
                
                # 1. Execute RAG Retrieval Pipeline
                retrieved_chunks = []
                try:
                    retrieval_results = await retrieval_pipeline.search(query=query)
                    # Filter by similarity threshold to emulate production query route
                    threshold = config.settings.SIMILARITY_THRESHOLD
                    retrieved_chunks = [
                        r for r in retrieval_results
                        if r.vector_score >= threshold or r.bm25_score > 0 or (r.rerank_score and r.rerank_score >= 0.0)
                    ]
                except Exception as e:
                    logger.error("evaluation_retrieval_failed", query=query, error=str(e))
                
                context_str = "\n\n".join([
                    f"[Chunk {i}] (Source: {c.source}):\n{c.content}"
                    for i, c in enumerate(retrieved_chunks, 1)
                ]) if retrieved_chunks else "No relevant context retrieved."

                # 2. Run LLM generation
                system_prompt = """You are a helpful AI assistant. Answer questions using ONLY the provided context. 
If the context doesn't contain enough information, say "I don't have enough information to answer this question."
Do not make up information or provide unsupported claims.
Always cite relevant information from the context when answering."""

                full_prompt = f"Context:\n{context_str}\n\nUser: {query}\n\nAssistant:"
                
                gen_req = GenerationRequest(
                    prompt=full_prompt,
                    system_prompt=system_prompt,
                    temperature=0.0,  # Factual temperature
                    max_tokens=1000,
                )
                
                generated_answer = "I don't have enough information to answer this question."
                try:
                    gen_res = await gemini_client.generate(gen_req)
                    generated_answer = gen_res.text
                except Exception as e:
                    logger.error("evaluation_generation_failed", query=query, error=str(e))

                # 3. LLM-as-a-Judge assessment
                # Faithfulness
                faith_prompt = FAITHFULNESS_PROMPT.format(context=context_str, answer=generated_answer)
                faith_res = await self._query_judge(faith_prompt)
                
                # Relevance
                rel_prompt = RELEVANCE_PROMPT.format(query=query, answer=generated_answer)
                rel_res = await self._query_judge(rel_prompt)
                
                # Context Recall
                recall_prompt = RECALL_PROMPT.format(reference_answer=ref_ans, context=context_str)
                recall_res = await self._query_judge(recall_prompt)

                tc_result = {
                    "id": tc["id"],
                    "query": query,
                    "reference_answer": ref_ans,
                    "generated_answer": generated_answer,
                    "retrieved_chunks_count": len(retrieved_chunks),
                    "faithfulness": faith_res,
                    "relevance": rel_res,
                    "recall": recall_res,
                }
                results.append(tc_result)

                total_faithfulness += faith_res.get("score", 0.0)
                total_relevance += rel_res.get("score", 0.0)
                total_recall += recall_res.get("score", 0.0)
                success_count += 1
                
        finally:
            if db_connected:
                await db.disconnect()

        n = success_count if success_count > 0 else 1
        summary = {
            "average_faithfulness": total_faithfulness / n,
            "average_relevance": total_relevance / n,
            "average_recall": total_recall / n,
            "total_evaluated": success_count,
            "results": results,
        }
        return summary
