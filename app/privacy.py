import re
_PAN = re.compile(r"\b(?:\d[ -]?){13,19}\b")
def mask_text(s: str) -> str:
    """Replace anything that looks like a card number with ****last4."""
    def f(m):
        d = re.sub(r"\D", "", m.group()); return "****" + d[-4:]
    return _PAN.sub(f, s)
def safe(obj):
    """Recursively mask strings; used on everything sent to the LLM."""
    if isinstance(obj, str): return mask_text(obj)
    if isinstance(obj, dict): return {k: safe(v) for k, v in obj.items()}
    if isinstance(obj, list): return [safe(v) for v in obj]
    return obj
