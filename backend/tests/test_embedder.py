import pytest
from unittest.mock import MagicMock, patch
from app.services.embedder import (
    chunk_legislative_text,
    extract_section_reference,
    split_text_recursively,
    generate_embeddings,
    retrieve_relevant_chunks,
)


def test_extract_section_reference():
    """Verify section heading extraction for various legal heading styles."""
    assert extract_section_reference("PART II — MOTOR VEHICLE INSPECTIONS\nAll vehicles shall...") == "PART II — MOTOR VEHICLE INSPECTIONS"
    assert extract_section_reference("Rule 4. Annual Inspection Tests\nEvery commercial vehicle...") == "Rule 4. Annual Inspection Tests"
    assert extract_section_reference("Section 12: Exemptions and Waivers\n(1) The following are exempt...") == "Section 12: Exemptions and Waivers"
    assert extract_section_reference("SCHEDULE 1 — INSPECTION FEES\nItem 1: Motor cycle KES 1,000") == "SCHEDULE 1 — INSPECTION FEES"
    assert extract_section_reference("Random text without any heading") is None


def test_chunk_legislative_text_structural():
    """Verify structural regex splitting on Kenyan legal document format."""
    legal_text = """
    PART I — PRELIMINARY
    Rule 1. Citation and commencement.
    These Rules may be cited as the Traffic (Motor Vehicle Inspection) Rules, 2026.
    Rule 2. Interpretation.
    In these Rules, unless the context otherwise requires—
    "Authority" means the National Transport and Safety Authority.

    PART II — INSPECTION TESTS
    Rule 3. Privately-owned motor vehicle inspection tests.
    Every private vehicle older than four years shall undergo an inspection test every two years.
    Rule 4. Annual inspection tests.
    Every commercial service vehicle, public service vehicle, and motorcycle shall undergo an annual inspection.

    SCHEDULE I — INSPECTION FEES
    Item 1: Motorcycle — KES 1,000.
    Item 2: Private vehicle — KES 3,000.
    """
    chunks = chunk_legislative_text(legal_text)
    assert len(chunks) >= 3
    
    # Verify section references are captured
    section_refs = [c["section_ref"] for c in chunks if c["section_ref"]]
    assert any("PART I" in s or "Rule 1" in s for s in section_refs)
    assert any("PART II" in s or "Rule 3" in s or "Rule 4" in s for s in section_refs)
    assert any("SCHEDULE" in s for s in section_refs)


def test_chunk_legislative_text_fallback():
    """Verify fallback to recursive splitter when text has no legal headings."""
    unstructured_text = "This is a continuous block of scanned text without any section headings. " * 30
    chunks = chunk_legislative_text(unstructured_text, max_chars_per_chunk=500, overlap_chars=50)
    assert len(chunks) > 1
    assert chunks[0]["chunk_index"] == 0
    assert chunks[1]["chunk_index"] == 1


def test_split_text_recursively():
    """Verify recursive character splitting with overlap."""
    text = "Paragraph 1 content.\n\nParagraph 2 content.\n\nParagraph 3 content.\n\nParagraph 4 content."
    chunks = split_text_recursively(text, max_chars=40, overlap_chars=10, section_ref="Section 5")
    assert len(chunks) >= 2
    assert all(c[1] is not None for c in chunks)


@patch("app.services.embedder.get_gemini_client")
def test_generate_embeddings(mock_get_client):
    """Verify batch embedding generation calling Gemini API."""
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_emb1 = MagicMock()
    mock_emb1.values = [0.1] * 768
    mock_emb2 = MagicMock()
    mock_emb2.values = [0.2] * 768

    mock_response = MagicMock()
    mock_response.embeddings = [mock_emb1, mock_emb2]
    mock_client.models.embed_content.return_value = mock_response

    vectors = generate_embeddings(["Chunk 1 text", "Chunk 2 text"], batch_size=5, throttle_delay=0.0)
    assert len(vectors) == 2
    assert len(vectors[0]) == 768
    assert vectors[0][0] == 0.1
    assert vectors[1][0] == 0.2


@patch("app.services.embedder.generate_embeddings")
@patch("app.services.embedder.supabase_admin")
def test_retrieve_relevant_chunks_rpc(mock_db, mock_gen_emb):
    """Verify vector similarity retrieval via Supabase RPC."""
    mock_gen_emb.return_value = [[0.1] * 768]
    mock_rpc = MagicMock()
    mock_rpc.execute.return_value.data = [
        {"id": "chunk-1", "similarity": 0.88, "chunk_text": "Mandatory inspection rule", "section_ref": "Rule 4"},
        {"id": "chunk-2", "similarity": 0.75, "chunk_text": "Fee schedule", "section_ref": "Schedule 1"},
    ]
    mock_db.rpc.return_value = mock_rpc

    results = retrieve_relevant_chunks(bill_id="bill-123", query="inspection frequency", top_k=2)
    assert len(results) == 2
    assert results[0]["similarity"] == 0.88
    assert results[0]["section_ref"] == "Rule 4"
