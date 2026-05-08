import json
import os

def load_call(filepath: str) -> list[dict]:
    """Load a single call JSON file and return list of utterances."""
    with open(filepath, 'r') as f:
        return json.load(f)

def get_call_id(filepath: str) -> str:
    """Extract call ID from filename."""
    return os.path.basename(filepath).replace('.json', '')

def load_all_calls(data_dir: str) -> dict[str, list[dict]]:
    """
    Load all JSON call files from a directory.
    Returns a dict: { call_id: [utterances] }
    """
    calls = {}
    for filename in os.listdir(data_dir):
        if filename.endswith('.json') and not filename.startswith('.'):
            filepath = os.path.join(data_dir, filename)
            call_id = get_call_id(filepath)
            calls[call_id] = load_call(filepath)
    return calls

def get_agent_utterances(call: list[dict]) -> list[dict]:
    """Filter only agent utterances from a call."""
    return [u for u in call if u['speaker'] == 'Agent']

def get_customer_utterances(call: list[dict]) -> list[dict]:
    """Filter only customer utterances from a call."""
    return [u for u in call if u['speaker'] == 'Customer']