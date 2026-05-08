import re
import json
from src.loader import get_agent_utterances, get_customer_utterances

# Profanity patterns

PROFANITY_PATTERNS = [
 r'(?<!\w)f[\*u][\*c][\*k]\w*(?!\w)',   # fuck, f*ck, f**k, fucking

r'(?<!\w)f\*+(?!\w)',                   # f***, F***, f****

    
    # shit, sh*t, shitload, shitty, shithead
    r'\bsh[\*i][\*t]\w*\b',

    # bullshit, bullsh*t
    r'\bbullsh[\*i][\*t]\b',

    # s**t, s***
    r'\bs\*{2,3}\b',

    # dumbass, dumbasses, jackass, jackasses, badass, kickass
    r'\b(dumb|bad|jack|smart|wise|lazy|fat|kick)ass\w*\b',

    # asshole, assholes
    r'\basshole\w*\b',

    # ass (standalone only)
    r'\bass\b',

    # bitch, bitches, bitching
    r'\bbitch\w*\b',

    # goddamn, goddamned
    r'\bgoddamn\w*\b',

    # damn, damned
    r'\bdamn\w*\b',

    # hell
    r'\bhell\b',

    # bastard
    r'\bbastard\b',

    # crap
    r'\bcrap\b',

    # piss, pissed, pissing
    r'\bpiss\w*\b',

    # freaking
    r'\bfreaking\b',

    # screw, screw you, screw off, screw this
    r'\bscrew\b',

    # idiot, idiots, idiotic
    r'\bidiot\w*\b',

    # moron, morons
    r'\bmoron\w*\b',

    # stupid, stupidity
    r'\bstupid\w*\b',

    # jerk, jerks
    r'\bjerk\w*\b',

    # loser, losers
    r'\bloser\w*\b',

    # deadbeat, deadbeats
    r'\bdeadbeat\w*\b',

    # pathetic
    r'\bpathetic\b',

    # get lost
    r'\bget\s+lost\b',

    # go to hell
    r'\bgo\s+to\s+hell\b',

    # drop dead
    r'\bdrop\s+dead\b',

    # shut up, shut the f*** up
    r'\bshut\b.{0,15}\bup\b',
]


def _check_utterances(utterances: list[dict]) -> list[dict]:
    """
    Check a list of utterances for profanity.
    Returns list of flagged utterances with matched words and patterns.
    """
    flagged = []
    for utt in utterances:
        text_lower = utt['text'].lower()
        matched = []
        for p in PROFANITY_PATTERNS:
            m = re.search(p, text_lower, re.IGNORECASE)
            if m:
                original_word = utt['text'][m.start():m.end()]  # slice from original
                matched.append({'word': original_word, 'pattern': p})
        if matched:
            flagged.append({
                'speaker': utt['speaker'],
                'text': utt['text'],
                'stime': utt['stime'],
                'etime': utt['etime'],
                'matched_patterns': matched,
            })
    return flagged


# Regex-based detection

def detect_profanity_regex(call: list[dict]) -> dict:
    """
    Regex approach: check agent and customer utterances separately.
    Returns a result dict with flags and details.
    """
    agent_utts = get_agent_utterances(call)
    customer_utts = get_customer_utterances(call)

    agent_flagged = _check_utterances(agent_utts)
    customer_flagged = _check_utterances(customer_utts)

    return {
        'approach': 'regex',
        'agent_profanity_detected': len(agent_flagged) > 0,
        'customer_profanity_detected': len(customer_flagged) > 0,
        'agent_flagged_utterances': agent_flagged,
        'customer_flagged_utterances': customer_flagged,
    }


# LLM-based detection (Groq)

def detect_profanity_llm(call: list[dict], api_key: str) -> dict:
    """
    LLM approach: send transcript to Groq (Llama 3.3) and identify
    profane or abusive language per speaker.
    """
    from groq import Groq
    import json
    import re

    client = Groq(api_key=api_key)

    lines = []
    for utt in call:
        lines.append(f"[{utt['speaker']}]: {utt['text']}")

    transcript = "\n".join(lines)

    prompt = f"""You are a call quality analyst reviewing a debt collection call transcript.

Analyze the transcript below and identify:

1. Profane language:
   - swear words, vulgarity, obscene language, explicit insults

2. Abusive or dismissive language:
   - hostile, insulting, threatening, degrading, or dismissive phrases
   - examples: "get lost", "shut up", "you're wasting my time"

Do NOT classify dismissive or rude phrases as profanity unless actual SWEAR words are used.

The reasoning field MUST be detailed and analytical, not a one-line summary.

For each flagged line:
- include the full utterance
- include the exact triggering phrase/word
- include a specific reason explaining why that phrase is problematic
- classify it as one of:
  - "profanity"
  - "abusive"
  - "dismissive"
  - "unprofessional"

Respond ONLY in this exact JSON format with no extra text, no markdown, no code fences:
{{
  "agent_profanity_detected": true,
  "customer_profanity_detected": false,
  "agent_flagged_lines": [
    {{
      "text": "utterance goes here",
      "reason": "triggering phrase goes here",
      "category": "dismissive"
    }}
  ],
  "customer_flagged_lines": [
    {{
      "text": "utterance goes here",
      "reason": "triggering phrase goes here",
      "category": "profanity"
    }}
  ],
"reasoning": "Write a detailed paragraph of at least 120 words. Mention: (1) overall tone of the conversation, (2) whether the agent remained professional, (3) every type of problematic language detected, (4) why each flagged phrase was categorized as profanity, abusive, dismissive, or unprofessional, and (5) how the customer's language affected the interaction."
}}

If no issues are detected for a speaker, return an empty list for their flagged_lines.

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


# Batch runner across all calls (regex only: LLM is per-call in the app)

def run_profanity_on_all_calls(calls: dict[str, list[dict]]) -> list[dict]:
    """
    Run regex detection across all calls.
    Returns a flat list of results, one dict per call.
    """
    results = []
    for call_id, utterances in calls.items():
        result = detect_profanity_regex(utterances)
        result['call_id'] = call_id
        results.append(result)
    return results