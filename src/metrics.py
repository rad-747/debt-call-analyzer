def compute_call_duration(call: list[dict]) -> float:
    """Total call duration from first stime to last etime."""
    if not call:
        return 0.0
    return max(u['etime'] for u in call) - min(u['stime'] for u in call)

def compute_overtalk(call):
    duration = compute_call_duration(call)
    if duration == 0:
        return 0.0, 0.0

    overtalk_seconds = 0.0

    for i in range(len(call) - 1):
        u1 = call[i]
        u2 = call[i + 1]  # only check the NEXT utterance

        # If they overlap AND are different speakers
        if u2['stime'] < u1['etime'] and u1['speaker'] != u2['speaker']:
            overlap = u1['etime'] - u2['stime']
            overtalk_seconds += overlap

    overtalk_pct = (overtalk_seconds / duration) * 100
    return round(overtalk_seconds, 2), round(overtalk_pct, 2)

def compute_silence(call: list[dict]) -> tuple[float, float]:
    """
    Silence = gaps between consecutive utterances.
    Returns (silence_seconds, silence_percentage).
    """
    duration = compute_call_duration(call)
    if duration == 0:
        return 0.0, 0.0

    silence_seconds = 0.0

    for i in range(len(call) - 1):
        gap = call[i + 1]['stime'] - call[i]['etime']
        if gap > 0:
            silence_seconds += gap

    silence_pct = (silence_seconds / duration) * 100
    return round(silence_seconds, 2), round(silence_pct, 2)


def compute_all_metrics(calls: dict[str, list[dict]]) -> list[dict]:
    """
    Run metrics across all calls.
    Returns a list of dicts, one per call, ready for a DataFrame.
    """
    results = []

    for call_id, utterances in calls.items():
        if not utterances:
            continue

        duration = compute_call_duration(utterances)
        overtalk_secs, overtalk_pct = compute_overtalk(utterances)
        silence_secs, silence_pct = compute_silence(utterances)

        results.append({
            'call_id': call_id,
            'duration_secs': round(duration, 2),
            'overtalk_secs': overtalk_secs,
            'overtalk_pct': overtalk_pct,
            'silence_secs': silence_secs,
            'silence_pct': silence_pct,
        })

    return results