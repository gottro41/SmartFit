import os
import json

DATA_FOLDER = "wardrobe_data"
IMAGE_FOLDER = "wardrobe_images"
UPLOAD_FOLDER = "uploads"
PROCESSED_FOLDER = "processed_images"

WARDROBE_FILES = {
    "shirt": "wardrobe_data/shirts.json",
    "pants": "wardrobe_data/pants.json",
    "skirt": "wardrobe_data/skirts.json",
    "shoes": "wardrobe_data/shoes.json",
    "hat": "wardrobe_data/hats.json",
    "accessory": "wardrobe_data/accessories.json",
    "dress": "wardrobe_data/dresses.json",
    "jacket": "wardrobe_data/jackets.json",
}


def ensure_project_folders():
    os.makedirs(DATA_FOLDER, exist_ok=True)
    os.makedirs(IMAGE_FOLDER, exist_ok=True)
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(PROCESSED_FOLDER, exist_ok=True)

    for filename in WARDROBE_FILES.values():
        if not os.path.exists(filename):
            with open(filename, "w") as f:
                json.dump([], f)


def load_json(filename):
    if not os.path.exists(filename):
        return []

    with open(filename, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def save_json(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)