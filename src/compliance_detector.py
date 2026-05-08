import re
import json

# Patterns for SENSITIVE INFORMATION being shared by agent
# Specific enough to avoid false positives on general references
  
SENSITIVE_INFO_PATTERNS = [
    r'\$[\d,]+(\.\d{2})?\b',         # actual dollar amounts: $250, $1,200.00
    r'\boutstanding\s+balance\b',     # "outstanding balance"
    r'\bbalance\s+(of|is)\b',         # "balance of $X", "balance is $X"
    r'\byou\s+owe\b',                 # "you owe"
    r'\boutstanding\s+amount\b',      # "outstanding amount"
    r'\boverdue\s+amount\b',          # "overdue amount"
    r'\bamount\s+due\b',              # "amount due"
    r'\baccount\s+(number|ending)\b', # "account number", "account ending"
    r'\baccount\s+details\b',         # "account details"
    r'\bpayment\s+due\b',             # "payment due"
]

# Patterns for VERIFICATION REQUEST by agent
# Agent must ASK for one of these: asking is not the same as verified
  
VERIFICATION_REQUEST_PATTERNS = [
    r'\bdate\s+of\s+birth\b',         # "date of birth"
    r'\bdob\b',                        # "DOB"
    r'\bsocial\s+security\b',          # "social security"
    r'\bssn\b',                        # "SSN"
    r'\blast\s+four\b',                # "last four digits"
    r'\bconfirm\s+your\s+address\b',   # "confirm your address"
    r'\bverify\s+your\s+address\b',    # "verify your address"
    r'\bprovide\s+your\s+address\b',   # "provide your address"
    r'\bcurrent\s+address\b',          # "current address"
    r'\bstreet\s+address\b',           # "street address"
    r'\bzip\s+code\b',                 # "zip code"
    r'\bconfirm\s+your\s+identity\b',  # "confirm your identity"
    r'\bverify\s+your\s+identity\b',   # "verify your identity"
    r'\bverify\s+your\s+information\b',# "verify your information"
]

# Patterns for CUSTOMER VERIFICATION RESPONSE
# Customer providing DOB, address, SSN digits
  
CUSTOMER_VERIFICATION_RESPONSE_PATTERNS = [
    r'\b\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}\b',              # date format: 01/01/1990
    r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\b',
    r'\b\d+\s+\w+\s+(street|st|avenue|ave|road|rd|drive|dr|lane|ln|blvd|boulevard)\b',
    r'\b\d{4}\b',                                            # last 4 digits SSN or zip
]

# Patterns for AGENT CONFIRMING verification is complete
  
VERIFICATION_CONFIRMED_PATTERNS = [
    r'\bconfirmed\s+your\s+identity\b',   # "confirmed your identity"
    r'\bverified\s+your\s+identity\b',    # "verified your identity"
    r'\bcan\s+confirm\s+your\s+identity\b',
    r'\bi\s+can\s+now\s+confirm\b',       # "I can now confirm"
    r'\bthat\s+(checks|matches)\s+out\b', # "that checks out"
    r'\bthank\s+you\s+for\s+(confirming|verifying)\b',
    r'\bidentity\s+confirmed\b',
]


def _utterance_contains(utterance: dict, patterns: list[str]) -> bool:
    """Check if a single utterance matches any of the given patterns."""
    text_lower = utterance['text'].lower()
    return any(re.search(p, text_lower) for p in patterns)


def _get_matched_patterns(utterance: dict, patterns: list[str]) -> list[str]:
    """Return which patterns matched in this utterance."""
    text_lower = utterance['text'].lower()
    matched_patterns = []
    for p in patterns:
        if re.search(p, text_lower):
            matched_patterns.append(p)
    
    return matched_patterns


# Regex-based compliance detection
  
def detect_compliance_regex(call: list[dict]) -> dict:
    """
    Walk through the call transcript in chronological order.

    State machine:
      UNVERIFIED → (agent asks) → VERIFICATION_REQUESTED
                → (customer responds) → VERIFICATION_PROVIDED
                → (agent confirms OR agent proceeds) → VERIFIED

    VIOLATION = agent discloses sensitive info while state != VERIFIED
    """
    verification_requested = False
    verification_done = False
    violation_found = False
    violations = []
    verification_utterances = []

    for utt in call:

        if utt['speaker'] == 'Agent':

            # 1. Check sensitive info FIRST using current verification state
            if _utterance_contains(utt, SENSITIVE_INFO_PATTERNS):
                if not verification_done:
                    violation_found = True
                    violations.append({
                        'text': utt['text'],
                        'stime': utt['stime'],
                        'matched': _get_matched_patterns(utt, SENSITIVE_INFO_PATTERNS)
                    })

            # 2. Check if agent is requesting verification
            if _utterance_contains(utt, VERIFICATION_REQUEST_PATTERNS):
                verification_requested = True
                verification_utterances.append({
                    'text': utt['text'],
                    'stime': utt['stime'],
                    'matched': _get_matched_patterns(utt, VERIFICATION_REQUEST_PATTERNS)
                })

            # 3. Check if agent explicitly confirms verification complete
            if _utterance_contains(utt, VERIFICATION_CONFIRMED_PATTERNS):
                verification_done = True

        elif utt['speaker'] == 'Customer':

            # 4. If agent had requested verification, check if customer responds
            if verification_requested and not verification_done:
                if _utterance_contains(utt, CUSTOMER_VERIFICATION_RESPONSE_PATTERNS):
                    verification_done = True

    return {
        'approach': 'regex',
        'violation_detected': violation_found,
        'verification_done': verification_done,
        'violations': violations,
        'verification_utterances': verification_utterances,
    }


# LLM-based compliance detection (Groq)
  
def detect_compliance_llm(call: list[dict], api_key: str) -> dict:
    """
    LLM approach: send the full transcript to Groq (Llama 3.3).
    Determine whether sensitive info was shared before identity verification.
    """
    from groq import Groq

    client = Groq(api_key=api_key)

    transcript = "\n".join(
        f"[{utt['speaker']}]: {utt['text']}" for utt in call
    )

    prompt = f"""You are a compliance analyst reviewing a debt collection call.

Your job is to check whether the agent shared any sensitive information BEFORE verifying the customer's identity.

Sensitive information includes ONLY specific customer/account details such as:
- Exact account balance or amount owed with a number/currency
- Account number, loan ID, or reference number
- Specific payment due date
- Specific overdue amount
- Payment history or missed payment count
- Bank/card details
- Address, DOB, SSN, PAN, Aadhaar, or other personal identity details

Generic debt-related phrases are NOT sensitive disclosure.
Do NOT flag phrases like:
- "I'm calling about your overdue balance"
- "I'm calling regarding your account"
- "This is about a debt/payment matter"
unless the agent reveals a specific amount, date, account number, or other customer-specific detail.

Identity verification means the agent asked for AND the customer provided at least one of:
- Date of birth
- Social Security Number (SSN) or last 4 digits
- Home address

Important rules(must comply all):
- Only DOB, SSN, or address count as valid verification.
- If the agent ONLY asked for a name and nothing else, verification_lines must be EMPTY.
- Agent merely ASKING for verification is not enough- customer must actually provide it
- Agent saying "I cannot share details until I verify you" is COMPLIANT, not a violation
- Check the sequence carefully: what came first- disclosure or verification?
- Asking for the customer's NAME is NOT identity verification. Name alone is never sufficient.
- Mentioning "overdue balance" without the actual amount is NOT a violation.
- Mentioning a debt/payment topic in general is NOT a violation.
- A violation requires actual customer-specific sensitive information before verification.


Respond ONLY in this exact JSON format with no extra text, no markdown, no code fences:
{{
  "violation_detected": true,
  "verification_done": false,
  "reasoning": "step by step explanation of what happened and when",
  "violation_lines": [
    {{"text": "exact agent line", "reason": "what sensitive info was disclosed"}}
  ],
  "verification_lines": [
    {{"text": "exact agent line where agent asked for DOB, SSN, or address only"}}
  ]
}}

If no violations found, return empty list for violation_lines.
If no verification found, return empty list for verification_lines.

Transcript:
{transcript}"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )

    raw = response.choices[0].message.content.strip()

    if raw.startswith("```"):
        raw = re.sub(r"```(?:json)?", "", raw).strip().strip("```").strip()

    try:
        result = json.loads(raw)
    except json.JSONDecodeError as e:
        raise Exception(f"LLM returned malformed JSON: {e}\nRaw output: {raw}")

    result['approach'] = 'llm'
    return result


# Batch runner across all calls (regex only)
  
def run_compliance_on_all_calls(calls: dict[str, list[dict]]) -> list[dict]:
    """
    Run regex compliance detection across all calls.
    Returns a list of result dicts, one per call.
    """
    results = []
    for call_id, utterances in calls.items():
        result = detect_compliance_regex(utterances)
        result['call_id'] = call_id
        results.append(result)
    return results