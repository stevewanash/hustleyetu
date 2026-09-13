"""
Vector Embedding & Structural Chunking Service for KeLegislate.
Handles legal structural text splitting, Gemini text-embedding-004 generation,
and pgvector RAG similarity retrieval.
"""

import logging
import random
import re
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from app.agents.gemini_client import get_gemini_client, count_tokens
from app.database import supabase_admin
from app.services.usage_logger import log_llm_usage

logger = logging.getLogger(__name__)

# Primary Structural Regex Patterns for Kenyan Legislation
STRUCTURAL_BOUNDARY_REGEX = re.compile(
    r"(?=(?:^|\n)\s*(?:"
    r"PART\s+[IVXLCDM]+[^\n]*|"
    r"(?:Rule|Section|Regulation|Clause|Article)\s+\d+[^\n]*|"
    r"SCHEDULE\s+(?:[IVXLCDM\d]+|FIRST|SECOND|THIRD|FOURTH|FIFTH|SIXTH|SEVENTH|EIGHTH|NINTH|TENTH)[^\n]*|"
    r"ARRANGEMENT OF (?:RULES|SECTIONS|CLAUSES)[^\n]*"
    r"))",
    re.IGNORECASE | re.MULTILINE
)

HEADING_EXTRACTOR_REGEX = re.compile(
    r"^\s*(PART\s+[IVXLCDM]+[^\n]*|"
    r"(?:Rule|Section|Regulation|Clause|Article)\s+\d+[^\n]*|"
    r"SCHEDULE\s+(?:[IVXLCDM\d]+|FIRST|SECOND|THIRD|FOURTH|FIFTH|SIXTH|SEVENTH|EIGHTH|NINTH|TENTH)[^\n]*|"
    r"ARRANGEMENT OF (?:RULES|SECTIONS|CLAUSES)[^\n]*)",
    re.IGNORECASE | re.MULTILINE
)


def extract_section_reference(chunk_text: str) -> Optional[str]:
    """Extracts the first legal section/rule/part heading from a text chunk."""
    match = HEADING_EXTRACTOR_REGEX.search(chunk_text)
    if match:
        heading = match.group(1).strip()
        # Clean up trailing punctuation or excessive whitespace
        heading = re.sub(r"[\s\.\:\-\—–]+$", "", heading)
        return heading[:150]
    return None


def split_text_recursively(
    text: str,
    max_chars: int = 1200,
    overlap_chars: int = 200,
    section_ref: Optional[str] = None
) -> List[Tuple[str, Optional[str]]]:
    """
    Recursively splits a text block into sub-chunks of max_chars with overlap.
    """
    text = text.strip()
    if not text:
        return []
    if len(text) <= max_chars:
        return [(text, section_ref)]

    # Split by double newline (paragraphs), single newline, or sentence end
    delimiters = ["\n\n", "\n", ". ", "; "]
    split_chunks: List[Tuple[str, Optional[str]]] = []
    
    current_pos = 0
    total_len = len(text)
    part_num = 1

    while current_pos < total_len:
        end_pos = min(current_pos + max_chars, total_len)
        if end_pos < total_len:
            # Try to break at natural delimiter
            best_break = -1
            chunk_slice = text[current_pos:end_pos]
            for delim in delimiters:
                last_idx = chunk_slice.rfind(delim)
                if last_idx != -1 and last_idx > max_chars * 0.4:
                    best_break = current_pos + last_idx + len(delim)
                    break
            if best_break != -1:
                end_pos = best_break

        sub_text = text[current_pos:end_pos].strip()
        if sub_text:
            sub_ref = f"{section_ref} (Part {part_num})" if section_ref and part_num > 1 else section_ref
            split_chunks.append((sub_text, sub_ref))
            part_num += 1

        if end_pos >= total_len:
            break
        current_pos = max(current_pos + 1, end_pos - overlap_chars)

    return split_chunks


def chunk_legislative_text(
    text: str,
    max_chars_per_chunk: int = 1500,
    overlap_chars: int = 200
) -> List[Dict[str, Any]]:
    """
    Chunks legislative text using structural regex splitting at PART, Rule, Section,
    and Schedule boundaries. Falls back to recursive character splitting if structural
    headings are absent.

    Returns:
        List of dicts: [{"chunk_index": int, "chunk_text": str, "section_ref": str}]
    """
    text = text.strip()
    if not text:
        return []

    # 1. Primary Strategy: Structural regex boundary splitting
    raw_sections = [s.strip() for s in STRUCTURAL_BOUNDARY_REGEX.split(text) if s.strip()]

    chunks_with_refs: List[Tuple[str, Optional[str]]] = []

    # Check if structural splitting found multiple sections
    if len(raw_sections) >= 2:
        for section in raw_sections:
            ref = extract_section_reference(section)
            if len(section) > max_chars_per_chunk:
                sub_chunks = split_text_recursively(
                    section,
                    max_chars=max_chars_per_chunk,
                    overlap_chars=overlap_chars,
                    section_ref=ref
                )
                chunks_with_refs.extend(sub_chunks)
            else:
                chunks_with_refs.append((section, ref))
    else:
        # 2. Fallback Strategy: Recursive character splitting
        logger.warning("Structural boundaries not found in text; using recursive character splitting fallback.")
        chunks_with_refs = split_text_recursively(
            text,
            max_chars=1000,
            overlap_chars=overlap_chars,
            section_ref=None
        )

    formatted_chunks: List[Dict[str, Any]] = []
    for idx, (chunk_text, section_ref) in enumerate(chunks_with_refs):
        approx_tokens = max(1, len(chunk_text.split()))
        formatted_chunks.append({
            "chunk_index": idx,
            "chunk_text": chunk_text,
            "section_ref": section_ref,
            "token_count": approx_tokens,
        })

    return formatted_chunks


def generate_embeddings(
    texts: List[str],
    model: str = "text-embedding-004",
    batch_size: int = 10,
    throttle_delay: float = 0.5,
    bill_id: Optional[str] = None
) -> List[List[float]]:
    """
    Generates 768-dimensional vector embeddings for a list of texts using Gemini API.
    Processes in batches with throttle delay to avoid HTTP 429 quota exhaustion.
    """
    if not texts:
        return []

    client = get_gemini_client()
    all_embeddings: List[List[float]] = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        start_time = time.perf_counter()

        # Retry loop for 429 rate-limits or transient API errors
        max_retries = 3
        res = None
        for attempt in range(max_retries):
            try:
                res = client.models.embed_content(
                    model=model,
                    contents=batch,
                )
                break
            except Exception as e:
                is_rate_limit = "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e) or "Quota" in str(e)
                if (is_rate_limit or attempt < max_retries - 1) and attempt < max_retries - 1:
                    sleep_time = (2 ** attempt) + random.uniform(0.1, 0.5)
                    logger.warning(f"Embedding batch {i // batch_size + 1} attempt {attempt + 1} failed ({e}). Retrying in {sleep_time:.2f}s...")
                    time.sleep(sleep_time)
                else:
                    logger.error(f"Error generating embeddings for batch {i // batch_size + 1} after {max_retries} attempts: {e}")
                    raise e

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        if hasattr(res, "embeddings") and res.embeddings:
            batch_vectors = [list(e.values) for e in res.embeddings]
        elif hasattr(res, "embedding") and res.embedding:
            batch_vectors = [list(res.embedding.values)]
        else:
            raise ValueError(f"Unexpected embedding response structure: {res}")

        all_embeddings.extend(batch_vectors)

        # Log usage
        total_chars = sum(len(t) for t in batch)
        approx_tokens = max(1, total_chars // 4)
        log_llm_usage(
            agent_name="embedder",
            model=model,
            prompt_tokens=approx_tokens,
            completion_tokens=0,
            total_tokens=approx_tokens,
            latency_ms=elapsed_ms,
            bill_id=bill_id
        )

        # Apply micro-throttle between batches if more remain
        if i + batch_size < len(texts):
            time.sleep(throttle_delay)

    return all_embeddings


def embed_and_store_bill_chunks(
    bill_id: str,
    extracted_text: str,
    model: str = "text-embedding-004",
    force: bool = False,
) -> List[Dict[str, Any]]:
    """
    Chunks legislative text, computes embeddings using Gemini text-embedding-004,
    and upserts rows into Supabase `bill_chunks`.

    Args:
        bill_id: UUID of the bill.
        extracted_text: Full text of the bill.
        model: Embedding model name (default: text-embedding-004).
        force: If False, skips embedding if chunks already exist in Supabase.

    Returns:
        List of chunk dicts.
    """
    if not extracted_text or not extracted_text.strip():
        logger.warning(f"No extracted text provided for bill {bill_id}. Skipping chunking.")
        return []

    # Idempotency check: if chunks already exist and force is False, return existing chunks
    if supabase_admin and not force:
        try:
            existing = supabase_admin.table("bill_chunks").select("id, chunk_index, section_ref, token_count").eq("bill_id", bill_id).execute()
            if existing.data and len(existing.data) > 0:
                logger.info(f"Bill '{bill_id}' already has {len(existing.data)} chunks in Supabase. Skipping embedding (idempotent).")
                return existing.data
        except Exception as check_err:
            logger.warning(f"Could not check existing chunks for bill {bill_id}: {check_err}")

    chunks = chunk_legislative_text(extracted_text)
    if not chunks:
        logger.warning(f"Chunking yielded 0 chunks for bill {bill_id}.")
        return []

    logger.info(f"Generated {len(chunks)} structural chunks for bill {bill_id}.")

    # Generate embeddings
    chunk_texts = [c["chunk_text"] for c in chunks]
    embeddings = generate_embeddings(chunk_texts, model=model, bill_id=bill_id)

    db_rows = []
    for chunk, vector in zip(chunks, embeddings):
        db_rows.append({
            "bill_id": bill_id,
            "chunk_index": chunk["chunk_index"],
            "chunk_text": chunk["chunk_text"],
            "section_ref": chunk["section_ref"],
            "token_count": chunk["token_count"],
            "embedding": vector,
        })

    # Persist to Supabase using upsert
    if supabase_admin:
        try:
            for i in range(0, len(db_rows), 50):
                sub_batch = db_rows[i:i + 50]
                supabase_admin.table("bill_chunks").upsert(sub_batch, on_conflict="bill_id, chunk_index").execute()
            logger.info(f"Successfully stored {len(db_rows)} chunks with vector embeddings in Supabase for bill {bill_id}.")
        except Exception as e:
            logger.error(f"Failed to insert bill chunks into Supabase: {e}")
            raise e

    return db_rows


def retrieve_relevant_chunks(
    bill_id: str,
    query: str,
    top_k: int = 5,
    match_threshold: float = 0.0,
    model: str = "text-embedding-004"
) -> List[Dict[str, Any]]:
    """
    Performs pgvector cosine similarity search over `bill_chunks` for a given bill.

    Args:
        bill_id: UUID of the bill.
        query: Query or focus text.
        top_k: Maximum number of relevant chunks to return.
        match_threshold: Minimum cosine similarity threshold.
        model: Embedding model name.

    Returns:
        List of matching chunk dicts with similarity score.
    """
    if not query.strip():
        return []

    # 1. Embed query text
    query_embeddings = generate_embeddings([query], model=model)
    if not query_embeddings:
        return []
    query_vector = query_embeddings[0]

    # 2. Call match_bill_chunks Supabase RPC function
    if supabase_admin:
        try:
            rpc_params = {
                "query_embedding": query_vector,
                "match_threshold": match_threshold,
                "match_count": top_k,
                "filter_bill_id": bill_id,
            }
            res = supabase_admin.rpc("match_bill_chunks", rpc_params).execute()
            if res.data:
                return res.data
        except Exception as e:
            logger.warning(f"pgvector RPC call failed, falling back to direct query: {e}")

        # Fallback: Query all chunks for bill and calculate cosine similarity in Python
        try:
            res = supabase_admin.table("bill_chunks").select("id, bill_id, chunk_index, chunk_text, section_ref, embedding").eq("bill_id", bill_id).execute()
            if res.data:
                q_vec = np.array(query_vector, dtype=float)
                norm_q = np.linalg.norm(q_vec)
                scored_chunks = []
                for row in res.data:
                    emb = row.get("embedding")
                    if emb:
                        # emb may be a string or list
                        if isinstance(emb, str):
                            emb = [float(x.strip()) for x in emb.strip("[]").split(",") if x.strip()]
                        c_vec = np.array(emb, dtype=float)
                        norm_c = np.linalg.norm(c_vec)
                        if norm_q > 0 and norm_c > 0:
                            sim = float(np.dot(q_vec, c_vec) / (norm_q * norm_c))
                        else:
                            sim = 0.0
                        if sim >= match_threshold:
                            scored_chunks.append({
                                "id": row.get("id"),
                                "bill_id": row.get("bill_id"),
                                "chunk_index": row.get("chunk_index"),
                                "chunk_text": row.get("chunk_text"),
                                "section_ref": row.get("section_ref"),
                                "similarity": round(sim, 4),
                            })
                scored_chunks.sort(key=lambda x: x["similarity"], reverse=True)
                return scored_chunks[:top_k]
        except Exception as e2:
            logger.error(f"Fallback chunk retrieval failed: {e2}")

    return []
