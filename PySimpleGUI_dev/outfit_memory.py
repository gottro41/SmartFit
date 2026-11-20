from datetime import datetime

from wardrobe_paths import ensure_project_folders, load_json, save_json


HISTORY_FILE = "wardrobe_data/outfit_history.json"


def get_item_signature(item):
    if not item:
        return "none"

    place = item.get("place", "unknown")
    item_id = item.get("id", "unknown")
    style = item.get("style", "unknown")
    color = item.get("primary_color", "unknown")

    return f"{place}:{item_id}:{style}:{color}"


def outfit_signature(outfit):
    if not outfit:
        return "empty"

    parts = []

    for slot in [
        "top",
        "bottom",
        "shoes",
        "hat",
        "accessory",
        "jacket",
        "dress",
    ]:
        item = outfit.get(slot)
        parts.append(
            f"{slot}={get_item_signature(item)}"
        )

    return "|".join(parts)


def outfit_pair_signatures(outfit):
    if not outfit:
        return []

    pairs = []

    top = outfit.get("top") or outfit.get("dress")
    bottom = outfit.get("bottom")
    shoes = outfit.get("shoes")
    jacket = outfit.get("jacket")

    if top and bottom:
        pairs.append(
            "top_bottom:"
            + get_item_signature(top)
            + "+"
            + get_item_signature(bottom)
        )

    if top and shoes:
        pairs.append(
            "top_shoes:"
            + get_item_signature(top)
            + "+"
            + get_item_signature(shoes)
        )

    if bottom and shoes:
        pairs.append(
            "bottom_shoes:"
            + get_item_signature(bottom)
            + "+"
            + get_item_signature(shoes)
        )

    if top and jacket:
        pairs.append(
            "top_jacket:"
            + get_item_signature(top)
            + "+"
            + get_item_signature(jacket)
        )

    return pairs


def load_history():
    ensure_project_folders()

    history = load_json(HISTORY_FILE)

    if not isinstance(history, list):
        return []

    return history


def save_outfit_history(outfit):
    ensure_project_folders()

    if not outfit:
        return

    history = load_history()

    history.append(
        {
            "timestamp": datetime.now().isoformat(),
            "signature": outfit_signature(outfit),
            "pairs": outfit_pair_signatures(outfit),
        }
    )

    history = history[-100:]

    save_json(
        HISTORY_FILE,
        history
    )

    print("Saved outfit history.")


def repetition_penalty(outfit):
    history = load_history()

    if not history:
        return 0

    signature = outfit_signature(outfit)
    current_pairs = set(
        outfit_pair_signatures(outfit)
    )

    penalty = 0

    for entry in history[-20:]:
        if entry.get("signature") == signature:
            penalty -= 8

        old_pairs = set(
            entry.get("pairs", [])
        )

        repeated_pairs = current_pairs.intersection(
            old_pairs
        )

        penalty -= len(repeated_pairs) * 1.5

    return penalty


def favorite_combo_bonus(outfit):
    history = load_history()

    if not history:
        return 0

    current_pairs = set(
        outfit_pair_signatures(outfit)
    )

    if not current_pairs:
        return 0

    pair_counts = {}

    for entry in history:
        for pair in entry.get("pairs", []):
            pair_counts[pair] = pair_counts.get(pair, 0) + 1

    bonus = 0

    for pair in current_pairs:
        count = pair_counts.get(pair, 0)

        if count >= 3:
            bonus += 2

        elif count >= 2:
            bonus += 1

    return bonus
