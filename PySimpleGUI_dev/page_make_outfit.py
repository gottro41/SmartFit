import io
import random
import webbrowser

import PySimpleGUI as sg
from PIL import Image

import outfit_engine

try:
    from product_recommender import recommend_products_for_outfit
except Exception as e:
    recommend_products_for_outfit = None
    print("Product recommender import error:", e)


last_generated_outfit = None


def image_to_bytes(image_path, max_size=(90, 90)):
    try:
        img = Image.open(image_path).convert("RGBA")
        img.thumbnail(max_size)

        bio = io.BytesIO()
        img.save(bio, format="PNG")
        return bio.getvalue()

    except Exception as e:
        print("Image load error:", e)
        return None


def item_name(item):
    if not item:
        return "None"

    color = item.get("primary_color", "unknown")
    style = item.get("style", item.get("place", "item"))

    return f"{color}_{style}".replace(" ", "_")


def make_item_card(slot, item):
    rows = [
        [sg.Text(slot.upper(), font=("Helvetica", 9, "bold"))]
    ]

    if not item:
        rows.append([sg.Text("None", size=(14, 1), font=("Helvetica", 7))])
        return sg.Column(
            rows,
            size=(150, 135),
            element_justification="c",
            pad=(2, 0),
        )

    img_data = image_to_bytes(item.get("image_path"))

    if img_data:
        rows.append([sg.Image(data=img_data)])

    rows.append([
        sg.Text(
            item_name(item),
            size=(16, 2),
            font=("Helvetica", 7),
            justification="center",
        )
    ])

    return sg.Column(
        rows,
        size=(150, 135),
        element_justification="c",
        pad=(2, 0),
    )


def generate_outfit():
    outfit_engine.refresh_wardrobe()

    usable_shirts = [
        item for item in outfit_engine.shirts
        if item.get("image_path")
    ]

    if not usable_shirts:
        return None

    reference = random.choice(usable_shirts)

    outfit = outfit_engine.make_outfit(
        reference,
        ["hats", "accessories", "jackets"]
    )

    return outfit


def has_real_item(outfit):
    if not outfit:
        return False

    return any(
        item
        for item in outfit.values()
        if item not in ["", None]
    )


def create_product_window(outfit):
    if recommend_products_for_outfit is None:
        layout = [
            [sg.Text("Product recommender is not connected.", font=("Helvetica", 15))],
            [sg.Button("Back", size=(12, 2))]#, sg.Button("Exit", size=(12, 2))],
        ]

        return sg.Window(
            "SmartFit Product Recommendations",
            layout,
            location=(0, 0),
            size=(800, 480),
            keep_on_top=True,
            element_justification="c",
            finalize=True,
        )

    try:
        recommendations = recommend_products_for_outfit(outfit)

    except Exception as e:
        layout = [
            [sg.Text("Could not load product recommendations.", font=("Helvetica", 15))],
            [sg.Text(str(e), size=(70, 5), font=("Helvetica", 9))],
            [sg.Button("Back", size=(12, 2))]#, sg.Button("Exit", size=(12, 2))],
        ]

        return sg.Window(
            "SmartFit Product Recommendations",
            layout,
            location=(0, 0),
            size=(800, 480),
            keep_on_top=True,
            element_justification="c",
            finalize=True,
        )

    rows = [
        [sg.VPush()],
        [sg.Text("Recommended Products", font=("Helvetica", 17, "bold"))],
        [sg.Text("Items that could improve or complete this outfit.", font=("Helvetica", 12))],
    ]

    product_count = 0

    for rec in recommendations:
        goal = rec.get("goal", {})
        reason = goal.get("reason", "Recommended item")

        rows.append([
            sg.Text(
                reason,
                size=(72, 2),
                font=("Helvetica", 12, "bold"),
            )
        ])

        for product in rec.get("products", [])[:2]:
            product_count += 1

            title = product.get("title") or "Product"
            price = product.get("price") or "Price unavailable"
            store = product.get("store") or "Store unavailable"
            link = product.get("link") or ""

            rows.append([
                sg.Text(title[:48], size=(42, 1), font=("Helvetica", 8)),
                sg.Text(price, size=(12, 1), font=("Helvetica", 8)),
                # sg.Button("Open", key=f"OPEN_PRODUCT_{product_count}", size=(7, 1)),
            ])

            rows.append([
                sg.Text(store[:58], size=(65, 1), font=("Helvetica", 10))
            ])

            rows.append([
                sg.Text(link, key=f"LINK_{product_count}", visible=False)
            ])

    if product_count == 0:
        rows.append([sg.Text("No product recommendations found.", font=("Helvetica", 13))])

    rows.append([
        sg.Button("Back", size=(12, 2)),
        #sg.Button("Exit", size=(12, 2)),
    ])
    rows.append([sg.VPush()])

    layout = [
        [
            sg.Column(
                rows,
                scrollable=True,
                sbar_width=30,
                sbar_arrow_width=30,
                vertical_scroll_only=True,
                size=(760, 440),
                element_justification="c",
            )
        ]
    ]

    return sg.Window(
        "SmartFit Product Recommendations",
        layout,
        location=(0, 0),
        size=(800, 480),
        keep_on_top=True,
        finalize=True,
    )


def create_window():
    global last_generated_outfit

    outfit = generate_outfit()

    if has_real_item(outfit):
        last_generated_outfit = outfit
    else:
        last_generated_outfit = None

    if not outfit:
        layout = [
            [sg.Text("Not enough clothing saved yet.", font=("Helvetica", 18))],
            [sg.Text("Add at least one shirt first.", font=("Helvetica", 14))],
            [
                sg.Button("Back", size=(14, 2)),
                #sg.Button("Exit", size=(14, 2)),
            ],
        ]

        return sg.Window(
            "SmartFit Outfit Maker",
            layout,
            location=(0, 0),
            size=(800, 480),
            keep_on_top=True,
            element_justification="c",
            finalize=True,
        )

    layout = [
        [
            sg.Button("Get Products", key="Recommend Products", size=(12, 1)),
            sg.Push(),
            sg.Button("Back", size=(8, 1)),
        ],

        [sg.Text("SmartFit Outfit", font=("Helvetica", 14, "bold"))],

        [
            make_item_card("hat", outfit.get("hat")),
            make_item_card("top", outfit.get("top")),
            make_item_card("jacket", outfit.get("jacket")),
        ],

        [
            make_item_card("bottom", outfit.get("bottom")),
            make_item_card("shoes", outfit.get("shoes")),
            make_item_card("accessory", outfit.get("accessory")),
        ],

        [
            sg.Button("Like", size=(10, 2)),
            sg.Button("Dislike", size=(10, 2)),
            sg.Button("Again", key="Generate Again", size=(10, 2)),
            #sg.Button("Exit", size=(8, 2)),
        ],
    ]

    return sg.Window(
        "SmartFit Outfit Maker",
        layout,
        location=(0, 0),
        size=(800, 480),
        keep_on_top=True,
        element_justification="c",
        finalize=True,
    )


def open_product_link(window, event):
    if not str(event).startswith("OPEN_PRODUCT_"):
        return

    number = str(event).replace("OPEN_PRODUCT_", "")
    link_key = f"LINK_{number}"

    try:
        link = window[link_key].get()

        if link:
            webbrowser.open(link)

    except Exception as e:
        print("Could not open product link:", e)