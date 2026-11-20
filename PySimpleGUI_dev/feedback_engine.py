import os
import json

from wardrobe_paths import DATA_FOLDER, ensure_project_folders


FEEDBACK_FILE = os.path.join(DATA_FOLDER, "feedback_data.json")


def ensure_feedback_file():
    ensure_project_folders()

    if not os.path.exists(FEEDBACK_FILE):
        with open(FEEDBACK_FILE, "w") as f:
            json.dump([], f)


def load_feedback():
    ensure_feedback_file()

    with open(FEEDBACK_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def save_feedback(data):
    ensure_feedback_file()

    with open(FEEDBACK_FILE, "w") as f:
        json.dump(data, f, indent=4)


def item_features(item):
    if not item:
        return {
            "place": "none",
            "style": "none",
            "primary_color": "none",
            "secondary_color": "none",
            "pattern": "none",
            "material": "none",
        }

    return {
        "place": item.get("place", "none"),
        "style": item.get("style", "none"),
        "primary_color": item.get("primary_color", "none"),
        "secondary_color": item.get("secondary_color", "none"),
        "pattern": item.get("pattern", "none"),
        "material": item.get("material", "none"),
    }


def outfit_features(outfit):
    return {
        "top": item_features(outfit.get("top")),
        "bottom": item_features(outfit.get("bottom")),
        "shoes": item_features(outfit.get("shoes")),
        "hat": item_features(outfit.get("hat")),
        "accessory": item_features(outfit.get("accessory")),
        "jacket": item_features(outfit.get("jacket")),
    }


def save_outfit_feedback(outfit, rating):
    """
    rating should be:
    1 for liked outfit
    -1 for disliked outfit
    """

    data = load_feedback()

    feedback_entry = {
        "rating": rating,
        "outfit": outfit_features(outfit),
    }

    data.append(feedback_entry)

    save_feedback(data)


def compare_items(item_a, item_b):
    score = 0

    if item_a.get("primary_color") == item_b.get("primary_color"):
        score += 2

    if item_a.get("secondary_color") == item_b.get("secondary_color"):
        score += 1

    if item_a.get("pattern") == item_b.get("pattern"):
        score += 1

    if item_a.get("material") == item_b.get("material"):
        score += 1

    if item_a.get("style") == item_b.get("style"):
        score += 1

    return score


def compare_outfits(outfit_a, outfit_b):
    score = 0

    for slot in ["top", "bottom", "shoes", "hat", "accessory", "jacket"]:
        score += compare_items(
            outfit_a.get(slot, item_features(None)),
            outfit_b.get(slot, item_features(None))
        )

    return score


def learning_score(outfit):
    feedback = load_feedback()

    if not feedback:
        return 0

    current_features = outfit_features(outfit)

    total = 0

    for entry in feedback:
        past_outfit = entry.get("outfit", {})
        rating = entry.get("rating", 0)

        similarity = compare_outfits(
            current_features,
            past_outfit
        )

        if similarity >= 6:
            total += rating * 3
        elif similarity >= 3:
            total += rating * 1

    return total


if __name__ == "__main__":
    ensure_feedback_file()
    print("Feedback engine ready.")
    print("Feedback file:", FEEDBACK_FILE)