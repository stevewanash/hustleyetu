import re
from typing import List, Dict, Any, Optional

# Word to number mapping for percentage written forms (e.g. "two point five", "five")
WORDS_TO_NUM = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, 
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
    "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20,
    "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70,
    "eighty": 80, "ninety": 90, "hundred": 100
}

MONTHS_MAP = {
    "january": 1, "jan": 1,
    "february": 2, "feb": 2,
    "march": 3, "mar": 3,
    "april": 4, "apr": 4,
    "may": 5,
    "june": 6, "jun": 6,
    "july": 7, "jul": 7,
    "august": 8, "aug": 8,
    "september": 9, "sep": 9, "sept": 9,
    "october": 10, "oct": 10,
    "november": 11, "nov": 11,
    "december": 12, "dec": 12
}

def parse_word_number(text_val: str) -> Optional[float]:
    """
    Parses a single written word or compound word representation of a number under 100
    (e.g., "five" -> 5.0, "twenty-five" or "twenty five" -> 25.0).
    """
    text_val = text_val.strip()
    if not text_val:
        return None
        
    # Check for simple word lookup
    if text_val in WORDS_TO_NUM:
        return float(WORDS_TO_NUM[text_val])
        
    # Check for compound word like "twenty-five" or "twenty five"
    parts = re.split(r'[- ]', text_val)
    if len(parts) == 2:
        w1, w2 = parts[0], parts[1]
        if w1 in WORDS_TO_NUM and w2 in WORDS_TO_NUM:
            val1 = WORDS_TO_NUM[w1]
            val2 = WORDS_TO_NUM[w2]
            # Ensure it is a tens word followed by a units word
            if val1 in [20, 30, 40, 50, 60, 70, 80, 90] and val2 in [1, 2, 3, 4, 5, 6, 7, 8, 9]:
                return float(val1 + val2)
    return None

def parse_percentage_value(match_str: str) -> Optional[float]:
    """
    Normalizes a matched percentage string into a float percentage value (e.g., 2.5% -> 2.5).
    Handles both digits and written word forms (including compound words).
    """
    cleaned = match_str.lower().strip()
    
    # Try digit representation first (e.g., 2.5%, 5 per cent)
    digit_match = re.search(r'\b(\d+(?:\.\d+)?)\b', cleaned)
    if digit_match:
        try:
            return float(digit_match.group(1))
        except ValueError:
            pass
            
    # Try word-based representation (e.g., "two point five", "five")
    # Clean ending percent/per cent words
    text_val = cleaned
    for suffix in ["percent", "per cent", "per-cent", "%"]:
        if text_val.endswith(suffix):
            text_val = text_val[:-len(suffix)].strip()
            
    # Check for decimal word representation: "two point five" or "twenty-five point five"
    if " point " in text_val:
        point_parts = text_val.split(" point ")
        if len(point_parts) == 2:
            whole_str, frac_str = point_parts[0], point_parts[1]
            whole_val = parse_word_number(whole_str)
            frac_val = parse_word_number(frac_str)
            if whole_val is not None and frac_val is not None:
                # Convert frac to decimal fraction (e.g. 5 -> 0.5)
                frac_decimal = frac_val / (10 ** len(str(int(frac_val))))
                return whole_val + frac_decimal
    else:
        return parse_word_number(text_val)
            
    return None

def parse_monetary_value(match_str: str) -> Optional[float]:
    """
    Normalizes a matched monetary string into a float value (e.g., KES 10,000 -> 10000.0).
    Handles multipliers like 'million', 'billion', 'thousand'.
    """
    cleaned = match_str.lower().strip()
    
    # Find numeric part
    num_match = re.search(r'([\d,]+(?:\.\d+)?)', cleaned)
    if not num_match:
        return None
        
    num_str = num_match.group(1).replace(",", "")
    try:
        val = float(num_str)
    except ValueError:
        return None
        
    # Determine multiplier
    multiplier = 1.0
    if "billion" in cleaned:
        multiplier = 1000000000.0
    elif "million" in cleaned:
        multiplier = 1000000.0
    elif "thousand" in cleaned:
        multiplier = 1000.0
        
    return val * multiplier

def parse_date_value(match_str: str) -> Optional[str]:
    """
    Normalizes a matched date string into standard YYYY-MM-DD ISO format.
    """
    cleaned = match_str.lower().strip()
    
    # 1. Check for YYYY-MM-DD / YYYY/MM/DD
    iso_match = re.match(r'\b(\d{4})[-/](\d{1,2})[-/](\d{1,2})\b', cleaned)
    if iso_match:
        year, month, day = map(int, iso_match.groups())
        return f"{year:04d}-{month:02d}-{day:02d}"
        
    # 2. Check for DD-MM-YYYY / DD/MM/YYYY
    # NOTE: In Kenya, dates are conventionally written as DD-MM-YYYY.
    # If the format is ambiguous (e.g., 03/04/2026), we default to DD-MM-YYYY (April 3).
    # Word-based formats (like "29th July 2026") are preferred as they are unambiguous.
    dmy_match = re.match(r'\b(\d{1,2})[-/](\d{1,2})[-/](\d{4})\b', cleaned)
    if dmy_match:
        day, month, year = map(int, dmy_match.groups())
        return f"{year:04d}-{month:02d}-{day:02d}"

    # 3. Check for DD-MM-YY / DD/MM/YY
    dmy_short_match = re.match(r'\b(\d{1,2})[-/](\d{1,2})[-/](\d{2})\b', cleaned)
    if dmy_short_match:
        day, month, year_short = map(int, dmy_short_match.groups())
        year = 2000 + year_short if year_short < 50 else 1900 + year_short
        return f"{year:04d}-{month:02d}-{day:02d}"
        
    # 4. Check for Day Month Year: e.g. "29th July 2026" / "29 July 2026"
    day_month_year = re.match(
        r'\b(\d{1,2})(?:st|nd|rd|th)?\s+'
        r'(january|february|march|april|may|june|july|august|september|october|november|december|'
        r'jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec)\s+(\d{4})\b', 
        cleaned
    )
    if day_month_year:
        day_str, month_str, year_str = day_month_year.groups()
        day = int(day_str)
        month = MONTHS_MAP.get(month_str)
        year = int(year_str)
        if month:
            return f"{year:04d}-{month:02d}-{day:02d}"
            
    # 5. Check for Month Day Year: e.g. "July 29, 2026" / "July 29 2026"
    month_day_year = re.match(
        r'\b(january|february|march|april|may|june|july|august|september|october|november|december|'
        r'jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec)\s+(\d{1,2})(?:st|nd|rd|th)?(?:,\s*|\s+)(\d{4})\b',
        cleaned
    )
    if month_day_year:
        month_str, day_str, year_str = month_day_year.groups()
        day = int(day_str)
        month = MONTHS_MAP.get(month_str)
        year = int(year_str)
        if month:
            return f"{year:04d}-{month:02d}-{day:02d}"
            
    # 6. Check for Year only as fallback if needed, but we keep it to full dates for precision
    return None

def extract_bill_data(text: str) -> List[Dict[str, Any]]:
    """
    Analyzes the bill text using regular expressions to extract percentages, monetary values, and dates.
    Returns a list of extractions with normalized values, raw match texts, indices, and ±200 character surrounding context.
    """
    extractions = []
    
    # 1. Regex definitions
    # Match digit percentage (e.g. 2.5%, 5 percent, 10 per cent) or word percentage (e.g. two point five per cent)
    tens = "twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety"
    units = "one|two|three|four|five|six|seven|eight|nine"
    percent_words = "|".join(WORDS_TO_NUM.keys())
    percentage_pattern = re.compile(
        r'\b(?:\d+(?:\.\d+)?\s*(?:%|percent\b|per\s+cent\b)|'
        rf'(?:(?:{tens})[- ](?:{units})|{percent_words})(?:\s+point\s+(?:{percent_words}))?\s*(?:percent\b|per\s+cent\b))',
        re.IGNORECASE
    )
    
    # Match monetary amounts with KES/Ksh prefix or shillings suffix, supporting commas, decimals, and million/billion multipliers
    monetary_pattern = re.compile(
        r'\b(?:(?:kes|ksh|kshs)\.?\s*\d+(?:,\d{3})*(?:\.\d+)?\b(?:\s*(?:million|billion|thousand)\b)?|'
        r'\d+(?:,\d{3})*(?:\.\d+)?\b\s*(?:million|billion|thousand\b)?\s*(?:shillings|kenya\s+shillings|kes|ksh)\b)',
        re.IGNORECASE
    )
    
    # Match dates in common Kenyan legislation formats
    months_pattern = "|".join(MONTHS_MAP.keys())
    date_pattern = re.compile(
        # Day Month Year or Month Day Year
        r'\b(?:\d{1,2}(?:st|nd|rd|th)?\s+(?:' + months_pattern + r')\s+\d{4}|'
        r'(?:' + months_pattern + r')\s+\d{1,2}(?:st|nd|rd|th)?(?:,\s*|\s+)\d{4}|'
        r'\d{4}[-/]\d{1,2}[-/]\d{1,2}|'
        r'\d{1,2}[-/]\d{1,2}[-/]\d{4}|'
        r'\d{1,2}[-/]\d{1,2}[-/]\d{2})\b',
        re.IGNORECASE
    )
    
    # Track matches by span to avoid overlapping duplicates
    matched_spans = []

    def is_overlapping(start: int, end: int) -> bool:
        for s, e in matched_spans:
            if max(start, s) < min(end, e):
                return True
        return False

    # Extract helper
    def process_matches(pattern: re.Pattern, val_type: str, parser_func):
        for match in pattern.finditer(text):
            start, end = match.span()
            if is_overlapping(start, end):
                continue
                
            raw_text = match.group(0)
            normalized = parser_func(raw_text)
            
            # Extract surrounding context ±200 characters
            context_start = max(0, start - 200)
            context_end = min(len(text), end + 200)
            context = text[context_start:context_end]
            
            # If the context starts/ends mid-word, clean it up slightly if desired,
            # but standard slicing is fine for AI agents.
            
            extractions.append({
                "type": val_type,
                "value": normalized if normalized is not None else raw_text,
                "raw": raw_text,
                "context": context,
                "start": start,
                "end": end
            })
            matched_spans.append((start, end))

    # Process in order of specificity (dates, percentages, then money)
    process_matches(date_pattern, "date", parse_date_value)
    process_matches(percentage_pattern, "percentage", parse_percentage_value)
    process_matches(monetary_pattern, "monetary", parse_monetary_value)
    
    # Sort extractions by their starting index in the document
    extractions.sort(key=lambda x: x["start"])
    return extractions

# Alias for consistent function naming across pipeline agents
extract_financial_values = extract_bill_data

