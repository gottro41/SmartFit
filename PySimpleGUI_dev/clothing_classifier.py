from __future__ import annotations

import os
import shutil
import sys
from collections import Counter

import cv2
import numpy as np
from google.cloud import vision
from PIL import Image
from rembg import remove

from wardrobe_paths import (
    PROCESSED_FOLDER,
    WARDROBE_FILES,
    ensure_project_folders,
    load_json,
    save_json,
)

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "vision-key.json"

client = vision.ImageAnnotatorClient()

CATEGORY_KEYWORDS = {
    "shirt": ["shirt", "t-shirt", "tee", "blouse", "top", "polo", "sweater", "active shirt", "undershirt", "jersey"],
    "pants": ["pants", "trousers", "jeans", "leggings", "slacks", "joggers", "sweatpants", "cargo pants", "khakis"],
    "skirt": ["skirt"],
    "shoes": ["shoe", "shoes", "sneaker", "sneakers", "boot", "boots", "heel", "loafer", "sandals", "footwear"],
    "hat": ["hat", "cap", "beanie"],
    "accessory": ["tie", "belt", "scarf", "neckwear", "necklace", "bracelet"],
    "dress": ["dress", "gown"],
    "jacket": ["jacket", "coat", "hoodie", "blazer", "outerwear", "puffer", "windbreaker"],
}

COLOR_NAMES = {
    "black": np.array([20, 20, 20]),
    "white": np.array([245, 245, 245]),
    "grey": np.array([128, 128, 128]),
    "red": np.array([200, 40, 40]),
    "blue": np.array([50, 90, 200]),
    "green": np.array([50, 160, 80]),
    "yellow": np.array([230, 210, 60]),
    "orange": np.array([230, 130, 40]),
    "purple": np.array([140, 70, 180]),
    "pink": np.array([240, 80, 170]),
    "brown": np.array([120, 80, 50]),
    "tan": np.array([210, 180, 130]),
}


def remove_background(original_image_path):
    ensure_project_folders()

    filename = os.path.basename(original_image_path)
    name, _ = os.path.splitext(filename)

    output_path = os.path.join(
        PROCESSED_FOLDER,
        f"{name}_no_bg.png"
    )

    input_image = Image.open(original_image_path).convert("RGBA")
    output_image = remove(input_image)
    output_image.save(output_path)

    return output_path


def nearest_color_name(rgb):
    rgb_arr = np.array(rgb)
    best_name = "unknown"
    best_dist = float("inf")

    for name, ref in COLOR_NAMES.items():
        dist = np.linalg.norm(rgb_arr - ref)

        if dist < best_dist:
            best_dist = dist
            best_name = name

    return best_name


def get_brightness(rgb):
    r, g, b = rgb
    return (0.299 * r) + (0.587 * g) + (0.114 * b)


def get_color_shade(color_name, avg_rgb):
    brightness = get_brightness(avg_rgb)

    if color_name == "black":
        return "black"

    if color_name == "white":
        return "white"

    if brightness < 90:
        return f"dark {color_name}"

    if brightness < 170:
        return f"medium {color_name}"

    return f"light {color_name}"


def get_clothing_temperature(category, style, material):
    style = style.lower()
    material = material.lower()

    cold_keywords = [
        "hoodie", "jacket", "coat", "puffer", "sweater",
        "long sleeve", "wool", "denim", "boots"
    ]

    warm_keywords = [
        "t-shirt", "tee", "active shirt", "sandals",
        "skirt", "dress", "shorts"
    ]

    if category == "jacket":
        return "cold weather"

    if any(word in style or word in material for word in cold_keywords):
        return "cold weather"

    if any(word in style or word in material for word in warm_keywords):
        return "warm weather"

    if category in ["shirt", "skirt", "dress"]:
        return "warm weather"

    return "all weather"


def map_labels_to_category(labels):
    labels_lower = [label.lower() for label in labels]
    scores = {category: 0 for category in CATEGORY_KEYWORDS}

    for category, keywords in CATEGORY_KEYWORDS.items():
        for label in labels_lower:
            for keyword in keywords:
                if keyword == label:
                    scores[category] += 3
                elif keyword in label:
                    scores[category] += 2

    best_category = max(scores, key=scores.get)

    if scores[best_category] == 0:
        return "unknown"

    return best_category


def filename_category_fallback(image_path, current_category):
    if current_category != "unknown":
        return current_category

    filename = os.path.basename(image_path).lower()

    if "pants" in filename or "jeans" in filename or "trousers" in filename:
        return "pants"
    if "shirt" in filename or "tee" in filename or "top" in filename:
        return "shirt"
    if "shoe" in filename or "sneaker" in filename or "boot" in filename:
        return "shoes"
    if "dress" in filename:
        return "dress"
    if "skirt" in filename:
        return "skirt"
    if "hat" in filename or "cap" in filename:
        return "hat"
    if "jacket" in filename or "hoodie" in filename or "coat" in filename:
        return "jacket"
    if "tie" in filename or "belt" in filename or "scarf" in filename:
        return "accessory"

    return "unknown"


def guess_style(labels, category):
    labels_lower = [label.lower() for label in labels]

    style_keywords = [
        "t-shirt", "active shirt", "long sleeve", "undershirt", "jersey",
        "jeans", "leggings", "trousers", "slacks", "joggers", "sweatpants",
        "sneakers", "sneaker", "boot", "boots", "loafer", "sandals",
        "cap", "beanie", "scarf", "tie",
        "dress", "gown", "hoodie", "jacket", "coat", "puffer", "skirt"
    ]

    for label in labels_lower:
        for keyword in style_keywords:
            if keyword in label:
                return keyword

    return category


def guess_material(labels):
    labels_lower = " ".join(label.lower() for label in labels)

    if "denim" in labels_lower or "jeans" in labels_lower:
        return "denim"
    if "leather" in labels_lower:
        return "leather"
    if "metal" in labels_lower:
        return "metal"
    if "wool" in labels_lower:
        return "wool"
    if "rubber" in labels_lower:
        return "rubber"
    if "knit" in labels_lower:
        return "knit"

    return "fabric"


def get_foreground_pixels(clean_image_path):
    image = Image.open(clean_image_path).convert("RGBA")
    arr = np.array(image)

    rgb = arr[:, :, :3]
    alpha = arr[:, :, 3]

    foreground = rgb[alpha > 30]

    if len(foreground) == 0:
        return np.empty((0, 3), dtype=np.uint8)

    return foreground


def get_colors_from_foreground(clean_image_path):
    pixels = get_foreground_pixels(clean_image_path)

    if len(pixels) == 0:
        return "unknown", "none"

    sample_size = min(len(pixels), 8000)
    sample_indices = np.random.choice(
        len(pixels),
        sample_size,
        replace=False
    )

    sampled_pixels = pixels[sample_indices]

    color_counts = Counter()
    color_rgb_values = {}

    for rgb in sampled_pixels:
        rgb_tuple = tuple(int(x) for x in rgb)
        name = nearest_color_name(rgb_tuple)

        color_counts[name] += 1

        if name not in color_rgb_values:
            color_rgb_values[name] = []

        color_rgb_values[name].append(rgb_tuple)

    common = color_counts.most_common()
    filtered = []

    for color, count in common:
        fraction = count / sample_size

        if fraction < 0.04:
            continue

        filtered.append((color, fraction))

    if not filtered:
        return "unknown", "none"

    primary_base = filtered[0][0]
    primary_pixels = color_rgb_values.get(primary_base, [])

    if primary_pixels:
        avg_rgb = tuple(np.mean(primary_pixels, axis=0).astype(int))
        primary = get_color_shade(primary_base, avg_rgb)
    else:
        primary = primary_base

    if len(filtered) > 1:
        secondary_base = filtered[1][0]
        secondary_pixels = color_rgb_values.get(secondary_base, [])

        if secondary_pixels:
            avg_rgb = tuple(np.mean(secondary_pixels, axis=0).astype(int))
            secondary = get_color_shade(secondary_base, avg_rgb)
        else:
            secondary = secondary_base
    else:
        secondary = "none"

    return primary, secondary


def detect_pattern_simple(clean_image_path):
    image = cv2.imread(clean_image_path, cv2.IMREAD_UNCHANGED)

    if image is None:
        return "unknown"

    if len(image.shape) == 3 and image.shape[-1] == 4:
        alpha = image[:, :, 3]
        image = image[:, :, :3]
        image[alpha == 0] = [255, 255, 255]

    image = cv2.resize(image, (500, 500))
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    edges = cv2.Canny(gray, 80, 160)
    edge_density = np.mean(edges > 0)

    if edge_density < 0.025:
        return "none"

    blurred = cv2.medianBlur(gray, 5)

    circles = cv2.HoughCircles(
        blurred,
        cv2.HOUGH_GRADIENT,
        dp=1.2,
        minDist=28,
        param1=120,
        param2=24,
        minRadius=7,
        maxRadius=30,
    )

    if circles is not None and len(circles[0]) >= 22:
        return "polka dots"

    lines = cv2.HoughLinesP(
        edges,
        rho=1,
        theta=np.pi / 180,
        threshold=65,
        minLineLength=45,
        maxLineGap=8,
    )

    if lines is not None:
        angles = []

        for line in lines:
            x1, y1, x2, y2 = line[0]
            angle = abs(np.degrees(np.arctan2(y2 - y1, x2 - x1)))
            angles.append(angle)

        if angles:
            horizontal = sum(1 for a in angles if a < 15 or a > 165)
            vertical = sum(1 for a in angles if 75 < a < 105)
            total = len(angles)

            if total > 0 and horizontal / total > 0.55:
                return "stripes_horizontal"

            if total > 0 and vertical / total > 0.55:
                return "stripes_vertical"

            if total > 0 and horizontal > total * 0.2 and vertical > total * 0.2:
                return "checkered"

    if edge_density > 0.075:
        return "patterned"

    return "none"


def get_next_id(json_file):
    items = load_json(json_file)

    if not items:
        return 0

    return max(item.get("id", 0) for item in items) + 1


def save_image_copy(image_path, category, item_id):
    base_folder = "wardrobe_images"

    category_folder_map = {
        "shirt": "wardrobe_shirts",
        "pants": "wardrobe_pants",
        "skirt": "wardrobe_skirts",
        "shoes": "wardrobe_shoes",
        "hat": "wardrobe_hats",
        "accessory": "wardrobe_accessories",
        "dress": "wardrobe_dresses",
        "jacket": "wardrobe_jackets",
    }

    category_folder = category_folder_map.get(category, "misc")

    full_folder_path = os.path.join(
        base_folder,
        category_folder
    )

    os.makedirs(full_folder_path, exist_ok=True)

    new_image_name = f"{category}_{item_id}.png"

    new_image_path = os.path.join(
        full_folder_path,
        new_image_name
    )

    shutil.copy(image_path, new_image_path)

    return new_image_path


def save_item_to_category_file(item, image_path):
    ensure_project_folders()

    category = item["place"]

    if category not in WARDROBE_FILES:
        print("Could not save: unknown clothing category.")
        return

    json_file = WARDROBE_FILES[category]

    items = load_json(json_file)

    item["id"] = get_next_id(json_file)

    clean_image_path = item.get("clean_image_path", image_path)

    saved_image_path = save_image_copy(
        clean_image_path,
        category,
        item["id"]
    )

    item["image_path"] = saved_image_path

    if "clean_image_path" in item:
        del item["clean_image_path"]

    items.append(item)

    save_json(json_file, items)

    print(f"Saved to {json_file}")
    print(f"Image saved to {saved_image_path}")


def analyze_clothing(image_path):
    ensure_project_folders()

    client = vision.ImageAnnotatorClient()

    clean_image_path = remove_background(image_path)

    with open(clean_image_path, "rb") as image_file:
        content = image_file.read()

    image = vision.Image(content=content)

    label_response = client.label_detection(image=image)

    if label_response.error.message:
        raise RuntimeError(label_response.error.message)

    labels = [
        label.description
        for label in label_response.label_annotations
    ]

    if labels:
        print("AI Labels:", labels)
    else:
        print("AI Labels: NONE FOUND")

    category = map_labels_to_category(labels)

    original_category = category

    category = filename_category_fallback(
        image_path,
        category
    )

    if original_category == "unknown" and category != "unknown":
        print(f"Used fallback category: {category}")

    style = guess_style(labels, category)
    material = guess_material(labels)

    primary_color, secondary_color = get_colors_from_foreground(
        clean_image_path
    )

    temperature = get_clothing_temperature(
        category,
        style,
        material
    )

    pattern = detect_pattern_simple(clean_image_path)

    item = {
        "id": 0,
        "place": category,
        "style": style,
        "primary_color": primary_color,
        "secondary_color": secondary_color,
        "pattern": pattern,
        "material": material,
        "temperature": temperature,
        "clean_image_path": clean_image_path,
    }

    return item


def main():
    ensure_project_folders()

    if len(sys.argv) != 2:
        print("Usage: python clothing_classifier.py image.jpg")
        return

    image_path = sys.argv[1]

    item = analyze_clothing(image_path)

    print("\n--- RESULT ---")
    print("Place:", item["place"])
    print("Style:", item["style"])
    print("Primary Color:", item["primary_color"])
    print("Secondary Color:", item["secondary_color"])
    print("Pattern:", item["pattern"])
    print("Material:", item["material"])
    print("Temperature:", item["temperature"])

    save_item_to_category_file(item, image_path)

def return_item_info(image_path):
    ensure_project_folders()

    item = analyze_clothing(image_path)

    return {
        "item": item,
        "text": f"""--- RESULT ---
    Place: {item["place"]}
    Style: {item["style"]}
    Primary Color: {item["primary_color"]}
    Secondary Color: {item["secondary_color"]}
    Pattern:     {item["pattern"]}
    Material: {item["material"]}
    Temperature: {item["temperature"]}"""}

    # save_item_to_category_file(item, image_path)

def gui_save(image_path):
    ensure_project_folders()

    item = analyze_clothing(image_path)

    save_item_to_category_file(item, image_path)


#if __name__ == "__main__":
#    main()
