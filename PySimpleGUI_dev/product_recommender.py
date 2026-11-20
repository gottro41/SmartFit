

from __future__ import annotations

import requests


SERPAPI_KEY = "3524e31a0397ea5526803d14ea6df25dee13f2171ba697f61c3dd3cff133c18d"
SERPAPI_URL = "https://serpapi.com/search"


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


def normalize_color(color):
    if not color:
        return "none"

    color = color.lower().strip()

    for word in ["very", "dark", "medium", "light"]:
        color = color.replace(word, "")

    return color.strip()


def get_color(item):
    if not item:
        return "none"

    return normalize_color(item.get("primary_color", "none"))


def get_full_color(item):
    if not item:
        return "none"

    return item.get("primary_color", "none").lower().strip()


def get_pattern(item):
    if not item:
        return "none"

    return item.get("pattern", "none")


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


def get_outfit_tone(outfit):
    warm = 0
    cool = 0

    for item in outfit.values():
        if item:
            tone = color_tone(get_color(item))

            if tone == "warm":
                warm += 1

            if tone == "cool":
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


def find_outfit_issues(outfit):
    issues = []

    top = outfit.get("top")
    bottom = outfit.get("bottom")
    shoes = outfit.get("shoes")
    hat = outfit.get("hat")
    accessory = outfit.get("accessory")
    jacket = outfit.get("jacket")

    if top and bottom:
        if bad_color_pair(get_color(top), get_color(bottom)):
            issues.append({
                "type": "replacement",
                "replace_slot": "bottom",
                "target_category": "pants",
                "recommended_color": "black",
                "query": f"black pants to match {get_color(top)} shirt",
                "reason": "The top and bottom colors clash, so neutral pants would balance the outfit."
            })

        if same_color_different_shade(top, bottom):
            issues.append({
                "type": "replacement",
                "replace_slot": "bottom",
                "target_category": "pants",
                "recommended_color": get_color(top),
                "query": f"{get_color(top)} pants same shade outfit",
                "reason": "The top and bottom are the same color but different shades, which can look mismatched."
            })

        if exact_same_pattern(top, bottom):
            issues.append({
                "type": "replacement",
                "replace_slot": "bottom",
                "target_category": "pants",
                "recommended_color": "black",
                "query": "solid black pants",
                "reason": "The top and bottom have the exact same pattern, so a solid bottom would look cleaner."
            })

        if pattern_clash(top, bottom):
            issues.append({
                "type": "replacement",
                "replace_slot": "bottom",
                "target_category": "pants",
                "recommended_color": "black",
                "query": "solid black pants",
                "reason": "The top and bottom patterns clash, so a solid neutral bottom would improve the outfit."
            })

    if top and shoes:
        if get_color(top) != get_color(shoes):
            issues.append({
                "type": "replacement",
                "replace_slot": "shoes",
                "target_category": "shoes",
                "recommended_color": get_color(top),
                "query": f"{get_color(top)} sneakers",
                "reason": "Using the sandwich rule, the shoes can match the top while the bottom creates contrast."
            })

    if shoes:
        shoe_color = get_color(shoes)

        if shoe_color == "white":
            issues.append({
                "type": "addition",
                "replace_slot": None,
                "target_category": "socks",
                "recommended_color": "white",
                "query": "white socks for white sneakers",
                "reason": "Avoid black socks with white sneakers."
            })

        if shoe_color == "black":
            issues.append({
                "type": "addition",
                "replace_slot": None,
                "target_category": "socks",
                "recommended_color": "colored",
                "query": "colored socks for black sneakers",
                "reason": "Colored socks can work better with black sneakers."
            })

    if count_outfit_colors(outfit) > 4:
        issues.append({
            "type": "addition",
            "replace_slot": None,
            "target_category": "jacket",
            "recommended_color": "black",
            "query": "black jacket casual outfit",
            "reason": "The outfit has more than 3–4 colors, so a neutral layer would calm it down."
        })

    if top and not hat:
        issues.append({
            "type": "addition",
            "replace_slot": None,
            "target_category": "hat",
            "recommended_color": get_color(top),
            "query": f"{get_color(top)} cap",
            "reason": "The hat can match the top to make the outfit more cohesive."
        })

    if top and not jacket:
        outfit_tone = get_outfit_tone(outfit)
        top_color = get_color(top)

        if top_color == "pink":
            issues.append({
                "type": "addition",
                "replace_slot": None,
                "target_category": "jacket",
                "recommended_color": "white",
                "query": "white coat for pink outfit",
                "reason": "For a pink outfit, a white or similar-toned coat usually works well."
            })

        elif outfit_tone == "warm":
            issues.append({
                "type": "addition",
                "replace_slot": None,
                "target_category": "jacket",
                "recommended_color": "brown",
                "query": "brown jacket warm tone outfit",
                "reason": "The outfit leans warm, so a brown jacket keeps the tones consistent."
            })

        elif outfit_tone == "cool":
            issues.append({
                "type": "addition",
                "replace_slot": None,
                "target_category": "jacket",
                "recommended_color": "black",
                "query": "black jacket cool tone outfit",
                "reason": "The outfit leans cool, so a black jacket keeps the tones consistent."
            })

        else:
            issues.append({
                "type": "addition",
                "replace_slot": None,
                "target_category": "jacket",
                "recommended_color": "black",
                "query": "black jacket casual outfit",
                "reason": "A black jacket is a safe neutral layer."
            })

    if not accessory:
        outfit_tone = get_outfit_tone(outfit)

        if outfit_tone == "warm":
            issues.append({
                "type": "addition",
                "replace_slot": None,
                "target_category": "accessory",
                "recommended_color": "gold",
                "query": "gold necklace casual outfit",
                "reason": "Warm outfits usually pair better with gold-toned accessories."
            })

        elif outfit_tone == "cool":
            issues.append({
                "type": "addition",
                "replace_slot": None,
                "target_category": "accessory",
                "recommended_color": "silver",
                "query": "silver necklace casual outfit",
                "reason": "Cool outfits usually pair better with silver-toned accessories."
            })

        else:
            issues.append({
                "type": "addition",
                "replace_slot": None,
                "target_category": "accessory",
                "recommended_color": "silver",
                "query": "minimal silver necklace casual outfit",
                "reason": "A simple accessory can complete the outfit."
            })

    return issues[:5]


def search_google_shopping(query, max_results=8):
    if SERPAPI_KEY == "PUT_YOUR_SERPAPI_KEY_HERE":
        raise RuntimeError("Add your SerpApi key inside product_recommender.py first.")

    params = {
        "engine": "google_shopping",
        "q": query,
        "api_key": SERPAPI_KEY,
        "gl": "us",
        "hl": "en",
    }

    response = requests.get(
        SERPAPI_URL,
        params=params,
        timeout=20
    )

    response.raise_for_status()

    data = response.json()
    results = data.get("shopping_results", [])

    products = []

    for result in results[:max_results]:
        products.append({
            "title": result.get("title"),
            "price": result.get("price"),
            "store": result.get("source"),
            "rating": result.get("rating"),
            "reviews": result.get("reviews"),
            "link": result.get("product_link") or result.get("link"),
            "thumbnail": result.get("thumbnail"),
        })

    return products


def score_product(product, goal):
    score = 0

    title = (product.get("title") or "").lower()
    store = (product.get("store") or "").lower()

    color = goal["recommended_color"]
    category = goal["target_category"]

    if color in title:
        score += 4

    if category in title:
        score += 3

    if category == "pants" and any(word in title for word in ["pants", "jeans", "trousers", "cargo"]):
        score += 3

    if category == "shoes" and any(word in title for word in ["shoe", "sneaker", "boot"]):
        score += 3

    if category == "jacket" and any(word in title for word in ["jacket", "coat", "hoodie"]):
        score += 3

    if category == "hat" and any(word in title for word in ["hat", "cap", "beanie"]):
        score += 3

    if category == "socks" and "sock" in title:
        score += 3

    if category == "accessory" and any(word in title for word in ["necklace", "bracelet", "ring", "belt", "scarf"]):
        score += 3

    if product.get("rating"):
        score += 1

    if product.get("reviews"):
        score += 1

    trusted_stores = [
        "nike", "adidas", "uniqlo", "zara",
        "h&m", "nordstrom", "target", "gap",
        "asos", "old navy", "urban outfitters"
    ]

    if any(store_name in store for store_name in trusted_stores):
        score += 1

    return score


def recommend_products_for_outfit(outfit):
    issues = find_outfit_issues(outfit)

    recommendations = []

    for issue in issues:
        products = search_google_shopping(issue["query"])

        ranked_products = sorted(
            products,
            key=lambda product: score_product(product, issue),
            reverse=True
        )

        recommendations.append({
            "goal": {
                "type": issue["type"],
                "replace_slot": issue["replace_slot"],
                "target_category": issue["target_category"],
                "reason": issue["reason"],
            },
            "products": ranked_products[:3],
        })

    return recommendations


def print_recommendations(recommendations):
    print("\n--- PRODUCT RECOMMENDATIONS ---")

    for rec in recommendations:
        goal = rec["goal"]

        print("\n================================")
        print("TYPE:", goal["type"])
        print("CATEGORY:", goal["target_category"])

        if goal["replace_slot"]:
            print("REPLACE:", goal["replace_slot"])

        print("WHY:", goal["reason"])

        for i, product in enumerate(rec["products"], start=1):
            print("\n--------------------------------")
            print(f"{i}. {product.get('title')}")
            print("STORE:", product.get("store"))
            print("PRICE:", product.get("price"))
            print("RATING:", product.get("rating"))
            print("LINK:", product.get("link"))


if __name__ == "__main__":
    test_outfit = {
        "top": {
            "place": "shirt",
            "primary_color": "medium orange",
            "pattern": "none",
        },
        "bottom": {
            "place": "pants",
            "primary_color": "pink",
            "pattern": "none",
        },
        "shoes": {
            "place": "shoes",
            "primary_color": "green",
            "pattern": "none",
        },
        "hat": "",
        "accessory": "",
        "jacket": "",
    }

    recommendations = recommend_products_for_outfit(test_outfit)
    print_recommendations(recommendations)

