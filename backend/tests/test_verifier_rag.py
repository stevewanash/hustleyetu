import pytest
from unittest.mock import MagicMock, patch
from app.agents.verifier import (
    verify_summary_claims,
    VerificationResult,
    BoundaryCheckItem,
    DiscrepancyItem,
)


@patch("app.agents.verifier.call_gemini")
def test_verify_summary_claims_with_rag_and_boundary_checks(mock_call_gemini):
    """Verify that verify_summary_claims passes RAG chunks and parses boundary check items."""
    mock_result = VerificationResult(
        verified=True,
        confidence=0.95,
        issues=[],
        discrepancies=[],
        boundary_checks=[
            BoundaryCheckItem(
                check_type="min_max_cap",
                description="Fine not exceeding KES 20,000",
                status="passed",
                details="Confirmed in Schedule 2"
            ),
            BoundaryCheckItem(
                check_type="temporal_validity",
                description="Annual inspection interval",
                status="passed",
                details="Rule 4 stipulates 12-month interval"
            ),
            BoundaryCheckItem(
                check_type="exemption",
                description="Military vehicles exempt",
                status="passed",
                details="Section 2(3) explicitly excludes military"
            )
        ]
    )

    mock_resp = MagicMock()
    mock_resp.parsed = mock_result
    mock_call_gemini.return_value = mock_resp

    rag_chunks = [
        {"section_ref": "Rule 4", "chunk_text": "Commercial vehicles shall be inspected annually."},
        {"section_ref": "Schedule 2", "chunk_text": "Penalties: Failure to inspect attracts fine not exceeding KES 20,000."},
    ]

    result = verify_summary_claims(
        summary_en="Commercial vehicles must undergo annual inspections or face fines up to KES 20,000.",
        regex_extractions=[{"value": "20,000", "unit": "KES"}],
        rag_chunks=rag_chunks,
        bill_id="test-bill-id",
    )

    assert result.verified is True
    assert result.confidence == 0.95
    assert len(result.boundary_checks) == 3
    assert result.boundary_checks[0].check_type == "min_max_cap"
    assert result.boundary_checks[0].status == "passed"

    # Verify prompt includes RAG chunks
    call_args = mock_call_gemini.call_args[1]
    assert "HIGHLIGHTED RAG CHUNKS" in call_args["prompt"]
    assert "Rule 4" in call_args["prompt"]
    assert call_args["agent_name"] == "verifier"


@patch("app.agents.verifier.supabase_admin")
def test_verify_bill_claims_idempotent_skip(mock_supabase):
    """Verify that verify_bill_claims skips execution if bill is already verified and force=False."""
    from app.agents.verifier import verify_bill_claims
    
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[{
            "id": "bill-already-verified",
            "ai_status": "verified",
            "verification_score": 0.92,
            "ai_summary_en": "Valid summary",
        }]
    )

    result = verify_bill_claims(bill_id="bill-already-verified", force=False)
    assert result.verified is True
    assert result.confidence == 0.92


@patch("app.agents.verifier.summarize_bill_text")
@patch("app.agents.verifier.verify_summary_claims")
@patch("app.agents.verifier.supabase_admin")
def test_verify_bill_claims_passes_on_retry(mock_supabase, mock_verify_summary, mock_summarize):
    """Verify feedback loop: initial verification failure triggers re-summarization and succeeds on retry."""
    from app.agents.verifier import verify_bill_claims
    from app.agents.summarizer import BillSummary

    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[{
            "id": "bill-retry-test",
            "ai_status": "summarized",
            "ai_summary_en": "Initial summary with missing cap",
            "extracted_text": "Section 1... Fine not exceeding KES 10,000",
            "regex_extractions": [],
            "bill_type": "regulatory"
        }]
    )
    mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(data=[])

    # First verify fails, second verify succeeds
    failed_result = VerificationResult(verified=False, confidence=0.50, issues=["Missing KES 10,000 cap"])
    passed_result = VerificationResult(verified=True, confidence=0.92, issues=[])
    mock_verify_summary.side_effect = [failed_result, passed_result]

    mock_summarize.return_value = BillSummary(
        summary_en="Corrected summary with KES 10,000 cap",
        implications_citizens=[],
        implications_business=[],
        industry_tags=[],
        source_citations=[]
    )

    result = verify_bill_claims(bill_id="bill-retry-test", force=True, max_retries=2)

    assert result.verified is True
    assert result.confidence == 0.92
    assert mock_summarize.call_count == 1
    assert mock_verify_summary.call_count == 2


@patch("app.agents.verifier.summarize_bill_text")
@patch("app.agents.verifier.verify_summary_claims")
@patch("app.agents.verifier.supabase_admin")
def test_verify_bill_claims_fails_after_max_retries_marks_failed(mock_supabase, mock_verify_summary, mock_summarize):
    """Verify that after exhausting max retries, verify_bill_claims sets ai_status='failed' and records ai_error."""
    from app.agents.verifier import verify_bill_claims
    from app.agents.summarizer import BillSummary

    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[{
            "id": "bill-fail-test",
            "ai_status": "summarized",
            "ai_summary_en": "Hallucinated summary",
            "extracted_text": "Section 1...",
            "regex_extractions": [],
            "bill_type": "regulatory"
        }]
    )
    mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(data=[])

    failed_result = VerificationResult(verified=False, confidence=0.40, issues=["Unresolvable hallucination"])
    mock_verify_summary.return_value = failed_result

    mock_summarize.return_value = BillSummary(
        summary_en="Still hallucinated summary",
        implications_citizens=[],
        implications_business=[],
        industry_tags=[],
        source_citations=[]
    )

    result = verify_bill_claims(bill_id="bill-fail-test", force=True, max_retries=2)

    assert result.verified is False
    assert result.confidence == 0.40

    # Verify final database update marked status as 'failed'
    update_calls = mock_supabase.table.return_value.update.call_args_list
    final_update_payload = update_calls[-1][0][0]
    assert final_update_payload["ai_status"] == "failed"
    assert "Verification failed after retries" in final_update_payload["ai_error"]
