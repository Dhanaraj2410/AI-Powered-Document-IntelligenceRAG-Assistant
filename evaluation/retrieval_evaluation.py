import os
import sys
import json
import time
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from rag_app.models import EvaluationResult
from rag_app.services.hybrid_retriever_service import HybridRetrieverService
from rag_app.services.reranker_service import RerankerService
from rag_app.services.grounding_service import GroundingService
from rag_app.services.prompt_service import PromptService
from rag_app.services.llm_service import LLMService

def run_evaluation():
    print("=" * 60)
    print("STARTING RAG BENCHMARK EVALUATION (FAISS + BM25 + RERANKING)")
    print("=" * 60)

    dataset_path = os.path.join(os.path.dirname(__file__), 'evaluation_dataset.json')
    if not os.path.exists(dataset_path):
        print(f"Evaluation dataset not found at {dataset_path}")
        return

    with open(dataset_path, 'r', encoding='utf-8') as f:
        dataset = json.load(f)

    if not dataset:
        print("Evaluation dataset is empty; no metrics were calculated.")
        return

    retriever = HybridRetrieverService()
    total_cases = len(dataset)

    precision_hits = 0
    mrr_sum = 0.0
    faithfulness_sum = 0.0
    relevance_sum = 0.0
    latency_sum = 0.0
    evaluated_cases = 0
    skipped_cases = 0

    # Get sample user ID or first available user
    from django.contrib.auth.models import User
    user = User.objects.first()
    if not user:
        print("No User found in database. Create a user first before running evaluation.")
        return

    print(f"Evaluating across {total_cases} benchmark test cases for User '{user.username}'...")

    for case in dataset:
        target = User.objects.get(pk=user.id).documents.filter(title=case.get('target_doc')).first()
        if not target:
            skipped_cases += 1
            print(f"  [Q{case['id']}] skipped: target document '{case.get('target_doc')}' is not indexed for this user")
            continue
        evaluated_cases += 1
        t0 = time.time()
        question = case["question"]
        expected_keywords = case.get("expected_keywords", [])

        # 1. Retrieve candidates
        candidates = retriever.retrieve_relevant_chunks(query=question, user_id=user.id, document_id=target.id, top_k=5)
        # 2. Rerank
        reranked = RerankerService.rerank_chunks(question, candidates, top_n=3)
        t1 = time.time()
        latency = t1 - t0
        latency_sum += latency

        # Check precision hit
        hit_found = False
        rank_hit = 0

        for idx, item in enumerate(reranked, 1):
            content_lower = item["content"].lower()
            if any(kw.lower() in content_lower for kw in expected_keywords):
                if not hit_found:
                    hit_found = True
                    rank_hit = idx
                    precision_hits += 1

        if hit_found and rank_hit > 0:
            mrr_sum += (1.0 / rank_hit)

        # Grounding / Faithfulness check on top chunk
        messages = PromptService.build_qa_prompt(question, reranked)['messages']
        answer = LLMService._synthesize_answer_from_context(messages).get('content', '')
        g_res = GroundingService.verify_grounding(answer, reranked)
        faithfulness_sum += g_res["faithfulness_score"]

        # Relevance score estimate based on keyword density
        answer_lower = answer.lower()
        answer_matches = sum(1 for keyword in expected_keywords if keyword.lower() in answer_lower)
        rel_score = answer_matches / max(len(expected_keywords), 1)
        relevance_sum += rel_score

        print(f"  [Q{case['id']}] '{question[:30]}...' -> Hit: {hit_found} | Rank: {rank_hit} | Time: {latency*1000:.1f}ms")

    # Compute Final Aggregate Metrics
    denominator = max(evaluated_cases, 1)
    p_at_k = round(precision_hits / denominator, 4)
    mrr = round(mrr_sum / denominator, 4)
    faithfulness = round(faithfulness_sum / denominator, 4)
    relevance = round(relevance_sum / denominator, 4)
    avg_latency = round(latency_sum / denominator, 3)

    eval_record = EvaluationResult.objects.create(
        precision_at_k=p_at_k,
        mrr_score=mrr,
        faithfulness_score=faithfulness,
        relevance_score=relevance,
        avg_latency_sec=avg_latency,
        total_test_cases=evaluated_cases,
        details={"retrieval_hits": precision_hits, "evaluated_cases": evaluated_cases, "skipped_missing_target": skipped_cases,
                 "answer_metrics": "local lexical overlap heuristics; not model-judged"}
    )

    print("\n" + "=" * 60)
    print("RAG BENCHMARK RESULTS")
    print("=" * 60)
    print(f"  Retrieval Precision@K: {p_at_k * 100:.1f}%")
    print(f"  Mean Reciprocal Rank (MRR): {mrr:.2f}")
    print(f"  Faithfulness / Grounding Score: {faithfulness * 100:.1f}%")
    print(f"  Answer Relevance Score: {relevance * 100:.1f}%")
    print(f"  Average Pipeline Latency: {avg_latency:.3f} seconds")
    print(f"  Skipped (target docs not indexed): {skipped_cases}")
    print("  Faithfulness/relevance are local lexical proxies, not model-judged evaluations.")
    print("=" * 60)
    print(f"Evaluation Record #{eval_record.id} successfully saved to database.")

if __name__ == '__main__':
    run_evaluation()
