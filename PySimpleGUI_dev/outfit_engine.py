import json
import random

from ml_style_model import predict_user_score
from outfit_memory import (
    repetition_penalty,
    favorite_combo_bonus,
    save_outfit_history,
)

from wardrobe_paths import (
    WARDROBE_FILES,
    ensure_project_folders,
    load_json,
)


ensure_project_folders()

shirts = []
pants = []
skirts = []
shoes = []
hats = []
accessories = []
dresses = []
jackets = []


NEUTRALS = [
    "black", "white", "grey", "gray",
    "tan", "beige", "brown", "cream",
    "navy", "none"
]

WARM_COLORS = [
    "red", "orange", "yellow", "pink",
    "brown", "tan", "cream", "beige"
]

COOL_COLORS = [
    "blue", "green", "purple", "grey",
    "gray", "black", "white", "navy"
]

BAD_COLOR_COMBOS = [
    ("purple", "yellow"),
    ("yellow", "purple"),
    ("white", "red"),
    ("red", "white"),
    ("green", "pink"),
    ("pink", "green"),
    ("orange", "pink"),
    ("pink", "orange"),
]

PATTERN_CLASHES = [
    ("polka dots", "stripes"),
    ("stripes", "polka dots"),
    ("polka dots", "stripes_horizontal"),
    ("stripes_horizontal", "polka dots"),
    ("polka dots", "stripes_vertical"),
    ("stripes_vertical", "polka dots"),
]


def refresh_wardrobe():
    global shirts, pants, skirts, shoes, hats, accessories, dresses, jackets

    ensure_project_folders()

    shirts = load_json(WARDROBE_FILES["shirt"])
    pants = load_json(WARDROBE_FILES["pants"])
    skirts = load_json(WARDROBE_FILES["skirt"])
    shoes = load_json(WARDROBE_FILES["shoes"])
    hats = load_json(WARDROBE_FILES["hat"])
    accessories = load_json(WARDROBE_FILES["accessory"])
    dresses = load_json(WARDROBE_FILES["dress"])
    jackets = load_json(WARDROBE_FILES["jacket"])


def normalize_color(color):
    if not color:
        return "none"

    color = str(color).lower().strip()

    for word in ["very", "dark", "medium", "light", "muted", "vibrant", "bright"]:
        color = color.replace(word, "")

    color = " ".join(color.split())

    return color if color else "none"


def get_color(item):
    if not item:
        return "none"

    return normalize_color(item.get("primary_color", "none"))


def get_full_color(item):
    if not item:
        return "none"

    return str(item.get("primary_color", "none")).lower().strip()


def get_pattern(item):
    if not item:
        return "none"

    return item.get("pattern", "none")


def get_material(item):
    if not item:
        return "unknown"

    return item.get("material", "unknown")


def get_place(item):
    if not item:
        return "unknown"

    return item.get("place", "unknown")


def get_style(item):
    if not item:
        return ""

    return item.get("style", "").lower()


def is_neutral(color):
    return normalize_color(color) in NEUTRALS


def color_tone(color):
    color = normalize_color(color)

    if color in WARM_COLORS:
        return "warm"

    if color in COOL_COLORS:
        return "cool"

    return "neutral"


def bad_color_pair(color_a, color_b):
    return (
        normalize_color(color_a),
        normalize_color(color_b)
    ) in BAD_COLOR_COMBOS


def same_color_different_shade(item_a, item_b):
    if not item_a or not item_b:
        return False

    base_a = get_color(item_a)
    base_b = get_color(item_b)

    full_a = get_full_color(item_a)
    full_b = get_full_color(item_b)

    if base_a == "none" or base_b == "none":
        return False

    return base_a == base_b and full_a != full_b


def same_color_same_shade(item_a, item_b):
    if not item_a or not item_b:
        return False

    return get_full_color(item_a) == get_full_color(item_b)


def pattern_clash(item_a, item_b):
    pattern_a = get_pattern(item_a)
    pattern_b = get_pattern(item_b)

    if pattern_a == "none" or pattern_b == "none":
        return False

    return (pattern_a, pattern_b) in PATTERN_CLASHES


def exact_same_pattern(item_a, item_b):
    pattern_a = get_pattern(item_a)
    pattern_b = get_pattern(item_b)

    if pattern_a == "none" or pattern_b == "none":
        return False

    return pattern_a == pattern_b


def texture_clash(item_a, item_b):
    material_a = get_material(item_a)
    material_b = get_material(item_b)

    bad_texture_pairs = [
        ("satin", "cotton"),
        ("cotton", "satin"),
        ("shiny", "cozy"),
        ("cozy", "shiny"),
    ]

    return (material_a, material_b) in bad_texture_pairs


def color_score(item_a, item_b):
    color_a = get_color(item_a)
    color_b = get_color(item_b)

    if color_a == "none" or color_b == "none":
        return 0

    if bad_color_pair(color_a, color_b):
        return -8

    if same_color_different_shade(item_a, item_b):
        return -5

    if same_color_same_shade(item_a, item_b):
        return 5

    if is_neutral(color_a) or is_neutral(color_b):
        return 4

    if color_tone(color_a) == color_tone(color_b):
        return 3

    return 1


def pattern_score(item_a, item_b):
    if pattern_clash(item_a, item_b):
        return -8

    if exact_same_pattern(item_a, item_b):
        return -3

    pattern_a = get_pattern(item_a)
    pattern_b = get_pattern(item_b)

    if pattern_a == "none" and pattern_b == "none":
        return 3

    if pattern_a == "none" or pattern_b == "none":
        return 2

    return 1


def material_score(item_a, item_b):
    if texture_clash(item_a, item_b):
        return -5

    if get_material(item_a) == get_material(item_b):
        return 2

    return 0


def get_outfit_tone(outfit):
    warm = 0
    cool = 0

    for item in outfit.values():
        if item:
            item_tone = color_tone(get_color(item))

            if item_tone == "warm":
                warm += 1

            if item_tone == "cool":
                cool += 1

    if warm > cool:
        return "warm"

    if cool > warm:
        return "cool"

    return "neutral"


def count_outfit_colors(outfit):
    colors = []

    for item in outfit.values():
        if item:
            color = get_color(item)

            if color != "none":
                colors.append(color)

    return len(set(colors))


def shoe_rule_score(candidate, outfit):
    if get_place(candidate) != "shoes":
        return 0

    style = get_style(candidate)

    bottom = outfit.get("bottom")
    dress = outfit.get("dress")

    score = 0

    if "sneaker" in style or "shoe" in style:
        score += 2

        if dress and "fancy" in get_style(dress):
            score -= 4

    if "heel" in style or "flat" in style:
        if dress:
            score += 3

        if bottom and get_place(bottom) == "pants":
            score -= 2

    if "boot" in style:
        if bottom and get_place(bottom) in ["pants", "skirt"]:
            score += 2

    return score


def hat_rule_score(candidate, outfit):
    if get_place(candidate) != "hat":
        return 0

    top = outfit.get("top") or outfit.get("dress")

    if not top:
        return 0

    if get_color(candidate) == get_color(top):
        return 4

    if is_neutral(get_color(candidate)):
        return 2

    return 0


def accessory_rule_score(candidate, outfit):
    if get_place(candidate) != "accessory":
        return 0

    outfit_tone = get_outfit_tone(outfit)
    candidate_tone = color_tone(get_color(candidate))

    if outfit_tone == candidate_tone:
        return 3

    if is_neutral(get_color(candidate)):
        return 2

    return 0


def jacket_rule_score(candidate, outfit):
    if get_place(candidate) != "jacket":
        return 0

    top = outfit.get("top") or outfit.get("dress")
    bottom = outfit.get("bottom")

    score = 0

    if top:
        score += color_score(top, candidate)

    if bottom:
        score += color_score(bottom, candidate)

    if is_neutral(get_color(candidate)):
        score += 3

    if top and get_color(top) == "pink":
        if get_color(candidate) in ["white", "pink"]:
            score += 4

    return score


def sandwich_rule_score(candidate, outfit):
    test_outfit = outfit.copy()

    place = get_place(candidate)

    if place == "shirt":
        test_outfit["top"] = candidate

    if place in ("pants", "skirt"):
        test_outfit["bottom"] = candidate

    if place == "shoes":
        test_outfit["shoes"] = candidate

    top = test_outfit.get("top") or test_outfit.get("dress")
    bottom = test_outfit.get("bottom")
    shoes_item = test_outfit.get("shoes")

    if not top or not bottom or not shoes_item:
        return 0

    if (
        get_color(top) == get_color(shoes_item)
        and get_color(bottom) != get_color(top)
    ):
        return 6

    return 0


def evaluate_points(reference, candidate, outfit=None):
    if not candidate:
        return -999

    if get_place(reference) == get_place(candidate):
        return -999

    if outfit is None:
        outfit = {}

    points = 0

    points += color_score(reference, candidate)
    points += pattern_score(reference, candidate)
    points += material_score(reference, candidate)

    points += shoe_rule_score(candidate, outfit)
    points += hat_rule_score(candidate, outfit)
    points += accessory_rule_score(candidate, outfit)
    points += jacket_rule_score(candidate, outfit)
    points += sandwich_rule_score(candidate, outfit)

    if candidate.get("favorite"):
        points += 2

    if candidate.get("last_worn"):
        points -= 2

    if not candidate.get("image_path"):
        points -= 10

    return points


def outfit_penalty(outfit):
    penalty = 0

    top = outfit.get("top") or outfit.get("dress")
    bottom = outfit.get("bottom")

    if top and bottom:
        if bad_color_pair(get_color(top), get_color(bottom)):
            penalty -= 10

        if pattern_clash(top, bottom):
            penalty -= 10

        if exact_same_pattern(top, bottom):
            penalty -= 4

        if same_color_different_shade(top, bottom):
            penalty -= 6

    if count_outfit_colors(outfit) > 4:
        penalty -= 6

    return penalty


def apply_piece_to_outfit(outfit, piece):
    test_outfit = outfit.copy()
    place = get_place(piece)

    if place == "shirt":
        test_outfit["top"] = piece

    elif place in ("pants", "skirt"):
        test_outfit["bottom"] = piece

    elif place == "shoes":
        test_outfit["shoes"] = piece

    elif place == "hat":
        test_outfit["hat"] = piece

    elif place == "accessory":
        test_outfit["accessory"] = piece

    elif place == "jacket":
        test_outfit["jacket"] = piece

    elif place == "dress":
        test_outfit["dress"] = piece

    return test_outfit


def choose_best_piece(reference, wardrobe_items, outfit):
    best_piece = ""
    best_points = -999

    valid_items = [
        item for item in wardrobe_items
        if item and item.get("image_path")
    ]

    if not valid_items:
        return ""

    for piece in valid_items:
        points = evaluate_points(reference, piece, outfit)

        test_outfit = apply_piece_to_outfit(outfit, piece)

        points += outfit_penalty(test_outfit)

        ml_bonus = predict_user_score(test_outfit)
        points += ml_bonus

        memory_penalty = repetition_penalty(test_outfit)
        memory_bonus = favorite_combo_bonus(test_outfit)

        points += memory_penalty
        points += memory_bonus

        if random.random() < 0.15:
            points += random.uniform(-2, 4)

        if points > best_points:
            best_piece = piece
            best_points = points

        elif points == best_points and best_piece != "":
            best_piece = random.choice([best_piece, piece])

    return best_piece


def make_outfit(reference, includeToggleArr=None):
    refresh_wardrobe()

    if includeToggleArr is None:
        includeToggleArr = []

    if not reference:
        return None

    search_through_list = []

    include_dresses = (
        "dresses" in includeToggleArr
        and reference.get("place") not in ["shirt", "skirt", "pants", "dress"]
    )

    if include_dresses or reference.get("place") == "dress":
        order_maker_dict = {
            "dress": ["shoes"],
            "shoes": ["dresses"],
            "hat": ["dresses", "shoes"],
            "accessory": ["dresses", "shoes"],
            "jacket": ["dresses", "shoes"],
        }
    else:
        order_maker_dict = {
            "shirt": ["pants", "skirts", "shoes"],
            "pants": ["shirts", "shoes"],
            "skirt": ["shirts", "shoes"],
            "shoes": ["shirts", "skirts", "pants"],
            "dress": ["shoes"],
            "hat": ["shirts", "skirts", "pants", "shoes"],
            "accessory": ["shirts", "skirts", "pants", "shoes"],
            "jacket": ["shirts", "skirts", "pants", "shoes"],
        }

    wardrobe_directory = {
        "shirts": shirts,
        "pants": pants,
        "skirts": skirts,
        "shoes": shoes,
        "dresses": dresses,
        "hats": hats,
        "accessories": accessories,
        "jackets": jackets,
    }

    reference_place = reference.get("place")

    if reference_place not in order_maker_dict:
        return None

    if "hats" in includeToggleArr and reference_place != "hat":
        search_through_list.append("hats")

    if "accessories" in includeToggleArr and reference_place != "accessory":
        search_through_list.append("accessories")

    if "jackets" in includeToggleArr and reference_place != "jacket":
        search_through_list.append("jackets")

    search_through_list += order_maker_dict[reference_place]

    search_through_list = list(dict.fromkeys(search_through_list))

    search_order = random.sample(
        search_through_list,
        len(search_through_list)
    )

    if include_dresses or reference_place == "dress":
        outfit = {
            "hat": "",
            "dress": "",
            "shoes": "",
            "accessory": "",
            "jacket": "",
        }
    else:
        outfit = {
            "hat": "",
            "top": "",
            "bottom": "",
            "shoes": "",
            "accessory": "",
            "jacket": "",
        }

    if reference_place == "hat":
        outfit["hat"] = reference

    elif reference_place == "accessory":
        outfit["accessory"] = reference

    elif reference_place == "dress":
        outfit["dress"] = reference

    elif reference_place == "shirt":
        outfit["top"] = reference

    elif reference_place in ("skirt", "pants"):
        outfit["bottom"] = reference

    elif reference_place == "shoes":
        outfit["shoes"] = reference

    elif reference_place == "jacket":
        outfit["jacket"] = reference

    for wardrobe in search_order:
        current_wardrobe = wardrobe_directory.get(wardrobe, [])

        best_piece = choose_best_piece(
            reference,
            current_wardrobe,
            outfit
        )

        if not best_piece:
            continue

        if wardrobe == "hats":
            outfit["hat"] = best_piece

        elif wardrobe == "accessories":
            outfit["accessory"] = best_piece

        elif wardrobe == "dresses":
            outfit["dress"] = best_piece

        elif wardrobe == "shirts":
            outfit["top"] = best_piece

        elif wardrobe == "shoes":
            outfit["shoes"] = best_piece

        elif wardrobe == "jackets":
            outfit["jacket"] = best_piece

        elif wardrobe in ("skirts", "pants"):
            if outfit.get("bottom") == "":
                outfit["bottom"] = best_piece
            else:
                current_score = evaluate_points(
                    reference,
                    outfit["bottom"],
                    outfit
                )

                new_score = evaluate_points(
                    reference,
                    best_piece,
                    outfit
                )

                if new_score > current_score:
                    outfit["bottom"] = best_piece

                elif new_score == current_score:
                    outfit["bottom"] = random.choice([
                        best_piece,
                        outfit["bottom"]
                    ])

    save_outfit_history(outfit)

    return outfit


refresh_wardrobe()


if __name__ == "__main__":
    refresh_wardrobe()

    if shirts:
        outfit = make_outfit(
            random.choice(shirts),
            ["hats", "accessories", "jackets"]
        )

        print(json.dumps(outfit, indent=4))
    else:
        print("No shirts found.")