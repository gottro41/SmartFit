import os
import joblib
from sklearn.feature_extraction import DictVectorizer
from sklearn.ensemble import RandomForestRegressor

from wardrobe_paths import ensure_project_folders, load_json


FEEDBACK_FILE = "wardrobe_data/feedback_data.json"
MODEL_FILE = "wardrobe_data/ml_style_model.joblib"


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


def normalize_color(color):
    if not color:
        return "none"

    color = str(color).lower().strip()

    for word in ["very", "dark", "medium", "light", "warm", "cool", "cold"]:
        color = color.replace(word, "")

    return color.strip()


def color_tone(color):
    color = normalize_color(color)

    if color in WARM_COLORS:
        return "warm"

    if color in COOL_COLORS:
        return "cool"

    return "neutral"


def get_item(outfit, slot):
    if not outfit:
        return None

    item = outfit.get(slot)

    if item == "":
        return None

    return item


def get_color(item):
    if not item:
        return "none"

    return normalize_color(item.get("primary_color", "none"))


def get_pattern(item):
    if not item:
        return "none"

    return item.get("pattern", "none")


def get_style(item):
    if not item:
        return "none"

    return item.get("style", "none")


def get_material(item):
    if not item:
        return "unknown"

    return item.get("material", "unknown")


def count_outfit_colors(outfit):
    colors = []

    for item in outfit.values():
        if item:
            color = get_color(item)

            if color != "none":
                colors.append(color)

    return len(set(colors))


def outfit_to_features(outfit):
    top = get_item(outfit, "top")
    bottom = get_item(outfit, "bottom")
    shoes = get_item(outfit, "shoes")
    hat = get_item(outfit, "hat")
    accessory = get_item(outfit, "accessory")
    jacket = get_item(outfit, "jacket")
    dress = get_item(outfit, "dress")

    # If the outfit uses a dress, treat dress as the main top-style piece too.
    main_top = top or dress

    features = {
        "top_color": get_color(main_top),
        "bottom_color": get_color(bottom),
        "shoes_color": get_color(shoes),

        "top_pattern": get_pattern(main_top),
        "bottom_pattern": get_pattern(bottom),

        "top_style": get_style(main_top),
        "bottom_style": get_style(bottom),
        "shoe_style": get_style(shoes),

        "top_material": get_material(main_top),
        "bottom_material": get_material(bottom),

        "top_tone": color_tone(get_color(main_top)),
        "bottom_tone": color_tone(get_color(bottom)),
        "shoe_tone": color_tone(get_color(shoes)),

        "has_hat": 1 if hat else 0,
        "has_accessory": 1 if accessory else 0,
        "has_jacket": 1 if jacket else 0,
        "has_dress": 1 if dress else 0,

        "color_count": count_outfit_colors(outfit),
    }

    return features


def get_feedback_features(entry):
    # Supports feedback saved as:
    # {"features": {...}, "rating": 1}
    if isinstance(entry, dict) and isinstance(entry.get("features"), dict):
        return entry["features"]

    # Supports feedback saved as:
    # {"outfit": {...}, "rating": 1}
    if isinstance(entry, dict) and isinstance(entry.get("outfit"), dict):
        return outfit_to_features(entry["outfit"])

    # Supports older feedback where the entry itself is already the feature dict.
    if isinstance(entry, dict):
        possible_feature_keys = [
            "top_color",
            "bottom_color",
            "shoes_color",
            "top_pattern",
            "bottom_pattern",
            "top_style",
            "bottom_style",
            "shoe_style",
        ]

        if any(key in entry for key in possible_feature_keys):
            return entry

    return None


def get_feedback_rating(entry):
    if not isinstance(entry, dict):
        return None

    rating = entry.get("rating")

    if rating is None:
        rating = entry.get("score")

    try:
        return float(rating)
    except (TypeError, ValueError):
        return None


def train_model():
    ensure_project_folders()

    feedback_data = load_json(FEEDBACK_FILE)

    X_dicts = []
    y = []

    for entry in feedback_data:
        features = get_feedback_features(entry)
        rating = get_feedback_rating(entry)

        if features is None or rating is None:
            continue

        X_dicts.append(features)
        y.append(rating)

    if len(X_dicts) < 5:
        print("Not enough feedback yet to train model.")
        return None

    vectorizer = DictVectorizer(sparse=False)
    X = vectorizer.fit_transform(X_dicts)

    model = RandomForestRegressor(
        n_estimators=100,
        random_state=42
    )

    model.fit(X, y)

    os.makedirs(os.path.dirname(MODEL_FILE), exist_ok=True)

    joblib.dump(
        {
            "vectorizer": vectorizer,
            "model": model,
        },
        MODEL_FILE
    )

    print(f"ML model trained on {len(X_dicts)} feedback examples.")

    return model


def predict_user_score(outfit):
    ensure_project_folders()

    if not os.path.exists(MODEL_FILE):
        return 0

    try:
        saved = joblib.load(MODEL_FILE)

        vectorizer = saved["vectorizer"]
        model = saved["model"]

        features = outfit_to_features(outfit)
        X = vectorizer.transform([features])

        prediction = model.predict(X)[0]

        # Convert predicted like/dislike score into a small outfit bonus.
        # Example: +1 rating becomes about +5 points, -1 becomes about -5 points.
        return float(prediction) * 5

    except Exception as e:
        print("Prediction error:", e)
        return 0
