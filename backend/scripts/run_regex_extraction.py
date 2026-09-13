import os
import sys
import asyncio
import json
from pathlib import Path

# Add backend directory to sys.path so we can import from app
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.config import settings
from app.database import supabase_admin
from app.utils.regex_extractor import extract_bill_data

async def process_regex_extraction():
    print("=" * 60)
    print("Step 2.2: Regex Value Extraction")
    print("=" * 60)
    
    is_supabase_mock = settings.SUPABASE_URL == "https://mock.supabase.co" or "mock" in settings.SUPABASE_KEY
    local_data_dir = Path(__file__).resolve().parent.parent / "data"
    
    if not is_supabase_mock:
        print("Connecting to Supabase database...")
        try:
            # Query all bills with 'ingested' status
            res = supabase_admin.table("bills").select("id, title, extracted_text").eq("ai_status", "ingested").execute()
            bills = res.data
            
            if not bills:
                print("No bills found with status 'ingested'.")
                # Fallback check: maybe we should run it on all bills for testing purposes
                print("Checking if there are any bills at all in the database...")
                all_res = supabase_admin.table("bills").select("id, title, extracted_text, ai_status").execute()
                if all_res.data:
                    print(f"Found {len(all_res.data)} bills in database with statuses: {[b['ai_status'] for b in all_res.data]}.")
                    # If the user wants to re-run, we can choose the first one
                    print("Processing the most recent bill for demonstration/verification purposes...")
                    bills = [all_res.data[0]]
                else:
                    print("The database is completely empty. Please run the seed script first:")
                    print("  python scripts/seed_bill.py")
                    return
            
            for bill in bills:
                bill_id = bill["id"]
                title = bill["title"]
                text = bill["extracted_text"] or ""
                
                print(f"\nProcessing Bill: {title} (ID: {bill_id})")
                print(f"Extracted text length: {len(text)} characters.")
                
                # Perform regex extraction
                extractions = extract_bill_data(text)
                print(f"Found {len(extractions)} regex matches (percentages, monetary values, dates).")
                
                # Store results in Supabase
                print("Updating database...")
                update_res = supabase_admin.table("bills").update({
                    "regex_extractions": extractions,
                    "ai_status": "extracted"
                }).eq("id", bill_id).execute()
                
                if update_res.data:
                    print(f"Successfully updated bill status to 'extracted' and stored extractions!")
                else:
                    print(f"Failed to update bill {bill_id} in Supabase.")
                    
        except Exception as e:
            print(f"Error during Supabase operations: {e}")
            sys.exit(1)
            
    else:
        print("\nSupabase URL is mock/stubbed. Running extraction in local mock environment.")
        mock_db_path = local_data_dir / "seeded_bill_mock_db.json"
        
        if not mock_db_path.exists():
            print(f"Mock database file not found at {mock_db_path}. Please run the seed script first.")
            sys.exit(1)
            
        try:
            with open(mock_db_path, "r", encoding="utf-8") as f:
                bill = json.load(f)
                
            title = bill.get("title", "Mock Bill")
            text = bill.get("extracted_text", "")
            
            print(f"\nProcessing Local Mock Bill: {title}")
            print(f"Extracted text length: {len(text)} characters.")
            
            extractions = extract_bill_data(text)
            print(f"Found {len(extractions)} regex matches.")
            
            # Update local mock record
            bill["regex_extractions"] = extractions
            bill["ai_status"] = "extracted"
            
            with open(mock_db_path, "w", encoding="utf-8") as f:
                json.dump(bill, f, indent=4)
                
            print(f"Successfully updated local mock DB at: {mock_db_path}")
            
        except Exception as e:
            print(f"Failed to process mock extraction: {e}")
            sys.exit(1)

    print("\nStep 2.2 regex extraction script completed successfully!")

if __name__ == "__main__":
    asyncio.run(process_regex_extraction())
