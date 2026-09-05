import re

def redact_pii(text: str) -> str:
    """
    Redacts sensitive Personal Identifiable Information (PII) from text.
    Currently supports:
    - Credit Card numbers (13-19 digits, with or without spaces/dashes)
    - Email Addresses
    - Phone Numbers (Basic format matching)
    """
    if not text:
        return text

    masked_text = text

    # 1. Mask Credit Card Numbers
    # Matches 13 to 19 digits, allowing spaces or dashes in between
    cc_pattern = r'\b(?:\d[ -]*?){13,19}\b'
    # We use a callable to ensure it only masks if it actually looks like a long number sequence, 
    # but a simple substitution works for this baseline.
    masked_text = re.sub(cc_pattern, "[REDACTED_CREDIT_CARD]", masked_text)

    # 2. Mask Email Addresses
    email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    masked_text = re.sub(email_pattern, "[REDACTED_EMAIL]", masked_text)

    # 3. Mask Phone Numbers (US/Generic International format)
    # E.g. +1-555-555-5555, (555) 555-5555
    phone_pattern = r'\b(?:\+\d{1,2}\s?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b'
    masked_text = re.sub(phone_pattern, "[REDACTED_PHONE]", masked_text)

    # 4. Mask App UI Boilerplate (e.g., headers, bank names)
    # Case insensitive matching for OCR variations
    ui_patterns = [
        r'(?i)secure\s*transaction\s*cent(?:er|re)',
        r'(?i)service\s*transaction\s*cent(?:er|re)',
        r'(?i)@?\s*nova\s*mobile\s*banking'
    ]
    for pattern in ui_patterns:
        masked_text = re.sub(pattern, "[UI_HEADER_REMOVED]", masked_text)

    return masked_text
