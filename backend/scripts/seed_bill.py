import os
import sys
import asyncio
import hashlib
import requests
import tempfile
from pathlib import Path

# Add backend directory to sys.path so we can import from app
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.config import settings
from app.database import supabase_admin
from app.services.extractor import extract_text_from_pdf

# ==========================================
# BILLS TO SEED
# ==========================================
# Two real bills for MVP testing — one financial, one regulatory.
# Both PDFs are publicly accessible and will be extracted via pdfplumber/OCR.
BILLS_TO_SEED = [
    {
        "url": "https://new.kenyalaw.org/akn/ke/act/ln/2026/13/eng@2026-02-13/publication",
        "title": "The Traffic (Motor Vehicle Inspection) Rules, 2026",
        "bill_type": "regulatory",
        "source_api": "scraper",
    },
    {
        "url": "https://nairobiassembly.go.ke/ncca/wp-content/uploads/paperlaid/2026/THE-NAIROBI-CITY-COUNTY-TRANSPORT-ACT-2020-MOTORCYCLE-TAXI-BODABODA-PERMIT-REGULATIONS-2025.pdf",
        "title": "The Nairobi City County Transport Act, 2020 — Motorcycle Taxi (Boda Boda) Permit Regulations, 2025",
        "bill_type": "regulatory",
        "source_api": "scraper",
    },
]


def get_url_hash(url: str) -> str:
    """Computes a 16-character SHA-256 hash of the URL."""
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]


def extract_via_llamaparse(pdf_path: str, api_key: str) -> str:
    """Attempts to extract text using LlamaParse."""
    print("Attempting text extraction via LlamaParse...")
    try:
        from llama_parse import LlamaParse
        parser = LlamaParse(
            api_key=api_key,
            result_type="text",
        )
        documents = parser.load_data(pdf_path)
        extracted_text = "\n".join([doc.text for doc in documents])
        if extracted_text.strip():
            print("LlamaParse extraction successful!")
            return extracted_text.strip()
        else:
            raise ValueError("LlamaParse returned empty text.")
    except Exception as e:
        print(f"LlamaParse extraction failed or not installed: {e}")
        raise e


def download_pdf(url: str) -> bytes:
    """Downloads a PDF from a URL with retry and user-agent spoofing."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    response = requests.get(url, headers=headers, timeout=30, verify=False)
    response.raise_for_status()
    return response.content


async def extract_text(pdf_data: bytes, url: str, llamaparse_key: str | None) -> str:
    """
    Extracts text from PDF data using the best available method.
    Priority: LlamaParse > pdfplumber > OCR fallback.
    """
    extracted_text = ""

    # Try LlamaParse first if API key is available
    if llamaparse_key and llamaparse_key != "your-llamaparse-api-key" and not llamaparse_key.startswith("mock"):
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_pdf:
            temp_pdf.write(pdf_data)
            temp_pdf_path = temp_pdf.name

        try:
            extracted_text = extract_via_llamaparse(temp_pdf_path, llamaparse_key)
        except Exception:
            print("LlamaParse failed. Falling back to local extraction...")
        finally:
            try:
                os.remove(temp_pdf_path)
            except OSError:
                pass

    # Fallback to pdfplumber + OCR
    if not extracted_text:
        print(f"Extracting text via pdfplumber/OCR from {url}...")
        try:
            extracted_text = await extract_text_from_pdf(url)
            print(f"Local extraction successful! Extracted {len(extracted_text)} characters.")
        except Exception as e:
            print(f"Local extraction failed: {e}")
            raise

    return extracted_text


async def seed_single_bill(bill_config: dict, local_data_dir: Path, is_supabase_mock: bool):
    """Seeds a single bill into the database."""
    url = bill_config["url"]
    title = bill_config["title"]
    bill_type = bill_config["bill_type"]
    source_api = bill_config["source_api"]

    url_hash = get_url_hash(url)
    print(f"\n{'=' * 60}")
    print(f"Seeding: {title}")
    print(f"Type   : {bill_type}")
    print(f"URL    : {url}")
    print(f"Hash   : {url_hash}")
    print(f"{'=' * 60}")

    # 1. Download PDF
    print("\nDownloading bill PDF...")
    try:
        pdf_data = download_pdf(url)
        print(f"Downloaded successfully ({len(pdf_data)} bytes).")
    except Exception as e:
        print(f"Failed to download PDF: {e}")
        print("Skipping this bill.")
        return

    # 2. Extract Text
    llamaparse_key = getattr(settings, "LLAMAPARSE_API_KEY", None)
    try:
        extracted_text = await extract_text(pdf_data, url, llamaparse_key)
    except Exception as e:
        print(f"Failed to extract text: {e}")
        print("Skipping this bill.")
        return

    if not extracted_text or len(extracted_text) < 50:
        print(f"Warning: Extracted text is too short ({len(extracted_text)} chars). Bill may be scanned/corrupt.")

    # Save preview locally
    safe_filename = url_hash + "_text.txt"
    local_preview_path = local_data_dir / safe_filename
    with open(local_preview_path, "w", encoding="utf-8") as f:
        f.write(extracted_text)
    print(f"Extracted text saved locally at: {local_preview_path}")

    # 3. Store PDF in Supabase Storage (Optional)
    storage_path = None
    if not is_supabase_mock:
        print("\nUploading PDF to Supabase Storage...")
        bucket_name = "bills"
        try:
            try:
                supabase_admin.storage.create_bucket(bucket_name, options={"public": True})
            except Exception:
                pass  # Already exists

            file_name = f"{url_hash}.pdf"
            supabase_admin.storage.from_(bucket_name).upload(
                path=file_name,
                file=pdf_data,
                file_options={"content-type": "application/pdf", "x-upsert": "true"}
            )
            storage_path = f"{bucket_name}/{file_name}"
            print(f"Uploaded to Storage: '{storage_path}'")
        except Exception as e:
            print(f"Warning: Failed to upload to Supabase Storage: {e}")
    else:
        print("\nSupabase is mock. Skipping Storage upload.")

    # 4. Insert/update record in database
    if not is_supabase_mock:
        print("\nInserting record into Supabase PostgreSQL...")
        try:
            # Deduplicate check
            res = supabase_admin.table("bills").select("id").eq("url_hash", url_hash).execute()
            if res.data:
                bill_id = res.data[0]["id"]
                print(f"Bill already exists (ID: {bill_id}). Updating...")
                supabase_admin.table("bills").update({
                    "extracted_text": extracted_text,
                    "pdf_storage_path": storage_path,
                    "bill_type": bill_type,
                    "ai_status": "ingested"
                }).eq("url_hash", url_hash).execute()
            else:
                insert_res = supabase_admin.table("bills").insert({
                    "title": title,
                    "url_hash": url_hash,
                    "source_url": url,
                    "pdf_storage_path": storage_path,
                    "extracted_text": extracted_text,
                    "bill_type": bill_type,
                    "ai_status": "ingested",
                    "source_api": source_api
                }).execute()
                bill_id = insert_res.data[0]["id"]
                print(f"Seeded new bill (ID: {bill_id})")
            print("Database operation completed successfully!")

            # 5. Pre-generate & cache example scenario/checklist in tier_impact_cache
            print("Pre-generating example scenario/checklist for bill...")
            try:
                from app.agents.impact_agent import compute_financial_impact_analysis
                bill_record = {
                    "id": bill_id,
                    "title": title,
                    "bill_type": bill_type,
                    "extracted_text": extracted_text[:4000],
                    "source_url": url,
                }
                impact_res = compute_financial_impact_analysis(bill_record)
                impact_dict = impact_res.model_dump()
                supabase_admin.table("tier_impact_cache").upsert({
                    "bill_id": bill_id,
                    "industry": "ALL",
                    "tier_label": "ALL",
                    "impact_data": impact_dict
                }, on_conflict="bill_id, industry, tier_label").execute()
                print("Pre-generated impact scenario cached in tier_impact_cache successfully!")
            except Exception as e:
                print(f"Warning: Failed to cache impact scenario: {e}")
        except Exception as e:
            print(f"Failed to insert into Supabase database: {e}")
            print("Please check your database connection or SQL migrations.")
    else:
        print("\nSupabase is mock. Simulating DB insert locally.")
        import json
        mock_db_path = local_data_dir / f"seeded_bill_{url_hash}_mock_db.json"
        mock_record = {
            "id": f"mock-uuid-{url_hash}",
            "title": title,
            "url_hash": url_hash,
            "source_url": url,
            "pdf_storage_path": None,
            "extracted_text": extracted_text,
            "bill_type": bill_type,
            "ai_status": "ingested",
            "source_api": source_api
        }
        with open(mock_db_path, "w", encoding="utf-8") as f:
            json.dump(mock_record, f, indent=4)
        print(f"Mock record saved at: {mock_db_path}")


async def seed_bills():
    """Seeds all configured bills into the database."""
    print("=" * 60)
    print("Phase R.4: Seed Test Bills (Finance Bill 2024 + Bodaboda Regulations 2025)")
    print("=" * 60)

    is_supabase_mock = settings.SUPABASE_URL == "https://mock.supabase.co" or "mock" in settings.SUPABASE_KEY
    local_data_dir = Path(__file__).resolve().parent.parent / "data"
    local_data_dir.mkdir(exist_ok=True)

    for bill_config in BILLS_TO_SEED:
        await seed_single_bill(bill_config, local_data_dir, is_supabase_mock)

    print(f"\n{'=' * 60}")
    print(f"Seeding complete! Processed {len(BILLS_TO_SEED)} bills.")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    asyncio.run(seed_bills())
