import unittest
from unittest.mock import MagicMock, patch
from pydantic import ValidationError

from app.agents.gemini_client import GeminiResponse
from app.agents.summarizer import BillSummary, summarize_bill_text, summarize_bill
from app.agents.translator import SwahiliTranslation, translate_summary_text, translate_bill
from app.agents.verifier import VerificationResult, verify_summary_claims, verify_bill_claims
from app.models.hustle_profiles import INDUSTRIES


class TestAgentsUnit(unittest.TestCase):

    # ==========================================
    # SUMMARIZER TESTS
    # ==========================================
    @patch("app.agents.summarizer.call_gemini")
    def test_summarize_bill_text_success(self, mock_call_gemini):
        mock_summary = BillSummary(
            summary_en="This bill proposes a 2.5% circulation tax on motor vehicles in Kenya.",
            implications_citizens=["Vehicle owners pay 2.5% annual tax.", "Minimum tax is KES 5,000."],
            implications_business=["Fleet operators face increased overheads."],
            industry_tags=["Transport & Logistics", "Finance & Mobile Money", "Invalid Tag"],
            source_citations=["Section 12(1)", "Clause 4"],
            key_financial_changes=["2.5% value rate", "KES 5,000 floor"],
            key_regulatory_changes=["Annual tax registration"],
        )
        mock_call_gemini.return_value = GeminiResponse(
            text="",
            parsed=mock_summary,
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            latency_ms=250.0,
            model_name="gemini-2.5-flash",
        )

        result = summarize_bill_text(
            extracted_text="The Motor Vehicle Circulation Tax Bill 2026...",
            regex_extractions=[{"value": "2.5%", "type": "percentage"}],
            bill_type="financial",
        )

        self.assertIsInstance(result, BillSummary)
        self.assertEqual(result.summary_en, mock_summary.summary_en)
        # Verify tag filtering removed "Invalid Tag"
        self.assertIn("Transport & Logistics", result.industry_tags)
        self.assertIn("Finance & Mobile Money", result.industry_tags)
        self.assertNotIn("Invalid Tag", result.industry_tags)
        mock_call_gemini.assert_called_once()

    @patch("app.agents.summarizer.supabase_admin")
    @patch("app.agents.summarizer.summarize_bill_text")
    def test_summarize_bill_db_integration(self, mock_summarize_text, mock_supabase):
        mock_summary = BillSummary(
            summary_en="English summary.",
            implications_citizens=["Imp 1"],
            implications_business=["Imp 2"],
            industry_tags=["Transport & Logistics"],
            source_citations=["Section 1"],
        )
        mock_summarize_text.return_value = mock_summary

        # Mock Supabase table select/update/delete/insert pipeline
        mock_table = MagicMock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "extracted_text": "Bill text...",
                "regex_extractions": [],
                "bill_type": "financial",
            }]
        )
        mock_table.update.return_value.eq.return_value.execute.return_value = MagicMock()
        mock_table.delete.return_value.eq.return_value.execute.return_value = MagicMock()
        mock_table.insert.return_value.execute.return_value = MagicMock()

        res = summarize_bill("123e4567-e89b-12d3-a456-426614174000", force=True)
        self.assertEqual(res, mock_summary)
        mock_table.update.assert_called_once()
        mock_table.delete.assert_called_once()
        mock_table.insert.assert_called_once()

    @patch("app.agents.summarizer.call_gemini")
    def test_summarize_bill_text_truncation_warning(self, mock_call_gemini):
        mock_summary = BillSummary(
            summary_en="Long bill summary.",
            implications_citizens=[],
            implications_business=[],
            industry_tags=["Transport & Logistics"],
            source_citations=[],
        )
        mock_call_gemini.return_value = GeminiResponse(
            text="",
            parsed=mock_summary,
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            latency_ms=250.0,
            model_name="gemini-2.5-flash",
        )

        long_text = "A" * 120000
        with self.assertLogs("app.agents.summarizer", level="WARNING") as log_cm:
            result = summarize_bill_text(extracted_text=long_text)
            self.assertTrue(any("truncated from 120000 to 100000" in message for message in log_cm.output))
        self.assertEqual(result.summary_en, mock_summary.summary_en)

    @patch("app.agents.summarizer.supabase_admin")
    @patch("app.agents.summarizer.summarize_bill_text")
    def test_summarize_bill_idempotency_skip(self, mock_summarize_text, mock_supabase):
        mock_table = MagicMock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "extracted_text": "Bill text...",
                "ai_summary_en": "Existing summary",
                "ai_status": "summarized",
                "bill_type": "financial",
            }]
        )
        mock_table.select.return_value.eq.return_value.execute.side_effect = [
            MagicMock(data=[{
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "extracted_text": "Bill text...",
                "ai_summary_en": "Existing summary",
                "ai_status": "summarized",
                "bill_type": "financial",
            }]),
            MagicMock(data=[{"industry_tag": "Transport & Logistics"}]),
        ]

        res = summarize_bill("123e4567-e89b-12d3-a456-426614174000", force=False)
        self.assertEqual(res.summary_en, "Existing summary")
        # Ensure summarize_bill_text was NOT called due to idempotency skip
        mock_summarize_text.assert_not_called()


    # ==========================================
    # TRANSLATOR TESTS
    # ==========================================
    @patch("app.agents.translator.call_gemini")
    def test_translate_summary_text_success(self, mock_call_gemini):
        mock_translation = SwahiliTranslation(
            summary_sw="Mswada huu unapendekeza kodi ya asilimia 2.5 kwa magari nchini Kenya. (Section 12(1))"
        )
        mock_call_gemini.return_value = GeminiResponse(
            text="",
            parsed=mock_translation,
            prompt_tokens=50,
            completion_tokens=30,
            total_tokens=80,
            latency_ms=180.0,
            model_name="gemini-2.5-flash",
        )

        swahili_text = translate_summary_text("This bill proposes a 2.5% tax on vehicles in Kenya. (Section 12(1))")
        self.assertTrue("Mswada" in swahili_text)
        self.assertTrue("Section 12(1)" in swahili_text)
        mock_call_gemini.assert_called_once()

    @patch("app.agents.translator.call_gemini")
    def test_translate_summary_text_citation_warning(self, mock_call_gemini):
        # Swahili text omits Section 12(1) citation
        mock_translation = SwahiliTranslation(
            summary_sw="Mswada huu unapendekeza kodi ya asilimia 2.5 kwa magari."
        )
        mock_call_gemini.return_value = GeminiResponse(
            text="",
            parsed=mock_translation,
            prompt_tokens=50,
            completion_tokens=30,
            total_tokens=80,
            latency_ms=180.0,
            model_name="gemini-2.5-flash",
        )

        with self.assertLogs("app.agents.translator", level="WARNING") as log_cm:
            swahili_text = translate_summary_text("This bill proposes a 2.5% tax. (Section 12(1))")
            self.assertTrue(any("omitted legal citations" in message for message in log_cm.output))
        self.assertTrue("Mswada" in swahili_text)

    def test_translate_summary_text_empty_input(self):
        with self.assertRaises(ValueError):
            translate_summary_text("")

    @patch("app.agents.translator.supabase_admin")
    @patch("app.agents.translator.translate_summary_text")
    def test_translate_bill_db_integration(self, mock_translate_text, mock_supabase):
        mock_translate_text.return_value = "Muhtasari wa Kiswahili"
        mock_table = MagicMock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"id": "123e4567-e89b-12d3-a456-426614174000", "ai_summary_en": "English summary", "ai_status": "summarized"}]
        )
        mock_table.update.return_value.eq.return_value.execute.return_value = MagicMock()

        res = translate_bill("123e4567-e89b-12d3-a456-426614174000", force=True)
        self.assertEqual(res, "Muhtasari wa Kiswahili")
        mock_table.update.assert_called_once()

    @patch("app.agents.translator.supabase_admin")
    @patch("app.agents.translator.translate_summary_text")
    def test_translate_bill_idempotency_skip(self, mock_translate_text, mock_supabase):
        mock_table = MagicMock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "ai_summary_en": "English summary",
                "ai_summary_sw": "Existing Swahili summary",
                "ai_status": "translated",
            }]
        )

        res = translate_bill("123e4567-e89b-12d3-a456-426614174000", force=False)
        self.assertEqual(res, "Existing Swahili summary")
        # Ensure translate_summary_text was NOT called due to idempotency skip
        mock_translate_text.assert_not_called()


    # ==========================================
    # VERIFIER TESTS
    # ==========================================
    @patch("app.agents.verifier.call_gemini")
    def test_verify_summary_claims_success(self, mock_call_gemini):
        mock_verification = VerificationResult(
            verified=True,
            issues=[],
            confidence=0.95,
            discrepancies=[],
        )
        mock_call_gemini.return_value = GeminiResponse(
            text="",
            parsed=mock_verification,
            prompt_tokens=80,
            completion_tokens=20,
            total_tokens=100,
            latency_ms=150.0,
            model_name="gemini-3.5-flash",
        )

        result = verify_summary_claims(
            summary_en="The tax is set at 2.5%.",
            regex_extractions=[{"value": "2.5%", "type": "percentage"}],
        )

        self.assertTrue(result.verified)
        self.assertEqual(result.confidence, 0.95)
        self.assertEqual(len(result.issues), 0)
        mock_call_gemini.assert_called_once()

    @patch("app.agents.verifier.call_gemini")
    def test_verify_summary_claims_empty_regex_warning(self, mock_call_gemini):
        mock_verification = VerificationResult(
            verified=True,
            issues=[],
            confidence=0.70,
            discrepancies=[],
        )
        mock_call_gemini.return_value = GeminiResponse(
            text="",
            parsed=mock_verification,
            prompt_tokens=80,
            completion_tokens=20,
            total_tokens=100,
            latency_ms=150.0,
            model_name="gemini-3.5-flash",
        )

        with self.assertLogs("app.agents.verifier", level="WARNING") as log_cm:
            result = verify_summary_claims(summary_en="The tax is set at 2.5%.", regex_extractions=[])
            self.assertTrue(any("No regex extractions provided" in message for message in log_cm.output))
        self.assertEqual(result.confidence, 0.70)

    @patch("app.agents.verifier.supabase_admin")
    @patch("app.agents.verifier.verify_summary_claims")
    def test_verify_bill_claims_db_integration(self, mock_verify_claims, mock_supabase):
        mock_verify_claims.return_value = VerificationResult(
            verified=True,
            issues=[],
            confidence=0.92,
            discrepancies=[],
        )
        mock_table = MagicMock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "extracted_text": "Bill text...",
                "ai_summary_en": "Summary text",
                "regex_extractions": [],
                "ai_status": "summarized",
            }]
        )
        mock_table.update.return_value.eq.return_value.execute.return_value = MagicMock()

        res = verify_bill_claims("123e4567-e89b-12d3-a456-426614174000", force=True)
        self.assertEqual(res.confidence, 0.92)
        mock_table.update.assert_called_once()

    @patch("app.agents.verifier.supabase_admin")
    @patch("app.agents.verifier.summarize_bill_text")
    @patch("app.agents.verifier.verify_summary_claims")
    def test_verify_bill_claims_retry_loop(self, mock_verify_claims, mock_summarize_text, mock_supabase):
        # 1st attempt fails, 2nd attempt passes
        fail_result = VerificationResult(
            verified=False,
            issues=["Numeric mismatch: 3% vs 2.5%"],
            confidence=0.40,
            discrepancies=[],
        )
        pass_result = VerificationResult(
            verified=True,
            issues=[],
            confidence=0.95,
            discrepancies=[],
        )
        mock_verify_claims.side_effect = [fail_result, pass_result]

        mock_summarize_text.return_value = MagicMock(summary_en="Revised summary with 2.5% rate.")

        mock_table = MagicMock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "extracted_text": "Bill text...",
                "ai_summary_en": "Summary text with error",
                "regex_extractions": [],
                "ai_status": "summarized",
            }]
        )
        mock_table.update.return_value.eq.return_value.execute.return_value = MagicMock()

        res = verify_bill_claims("123e4567-e89b-12d3-a456-426614174000", force=True, max_retries=2)
        self.assertTrue(res.verified)
        self.assertEqual(res.confidence, 0.95)
        # Verify re-summarization was called once during feedback retry
        mock_summarize_text.assert_called_once()

    @patch("app.agents.verifier.supabase_admin")
    @patch("app.agents.verifier.verify_summary_claims")
    def test_verify_bill_claims_idempotency_skip(self, mock_verify_claims, mock_supabase):
        mock_table = MagicMock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "extracted_text": "Bill text...",
                "ai_summary_en": "Summary text",
                "regex_extractions": [],
                "ai_status": "verified",
                "verification_score": 0.95,
            }]
        )

        res = verify_bill_claims("123e4567-e89b-12d3-a456-426614174000", force=False)
        self.assertTrue(res.verified)
        self.assertEqual(res.confidence, 0.95)
        # Ensure verify_summary_claims was NOT called due to idempotency skip
        mock_verify_claims.assert_not_called()


if __name__ == "__main__":
    unittest.main()

