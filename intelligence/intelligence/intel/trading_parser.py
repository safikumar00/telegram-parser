import re


def normalize_text(text: str) -> str:
    return (
        text.upper()
        .replace("𝗫𝗔𝗨𝗨𝗦𝗗", "XAUUSD")
        .replace("–", "-")
        .replace("—", "-")
        .replace("→", " ")
    )


def extract_symbol(text):
    match = re.search(r"(XAUUSD|GOLD)", text)
    return "XAUUSD" if match else None


def extract_type(text):
    if "BUY" in text:
        return "BUY"
    if "SELL" in text:
        return "SELL"
    return None


def extract_entry(text):
    match = re.search(r"(\d{4,5})\s*[-/_]\s*(\d{2,5})", text)
    if match:
        a = float(match.group(1))
        b = float(match.group(2))
        return min(a, b), max(a, b)

    match = re.search(r"(BUY|SELL)\s+(\d{4,5})", text)
    if match:
        val = float(match.group(2))
        return val, val

    return None, None


def extract_targets(text):
    matches = re.findall(r"TP[^\d]*(\d{4,5})", text)
    return [float(x) for x in matches]


def extract_sl(text):
    match = re.search(r"SL[^\d]*(\d{4,5})", text)
    return float(match.group(1)) if match else None


def is_entry_signal(text):
    return (
        ("BUY" in text or "SELL" in text)
        and ("TP" in text or "TARGET" in text)
    )


def parse_signal(text: str):
    text = normalize_text(text)

    if not is_entry_signal(text):
        return None

    entry_min, entry_max = extract_entry(text)

    return {
        "symbol": extract_symbol(text),
        "type": extract_type(text),
        "entry_min": entry_min,
        "entry_max": entry_max,
        "targets": extract_targets(text),
        "stop_loss": extract_sl(text),
    }