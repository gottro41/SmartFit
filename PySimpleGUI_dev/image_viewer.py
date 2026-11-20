import os
import io
from PIL import Image, ImageTk, ImageDraw, ImageFont
import PySimpleGUI as sg

THUMB_SIZE = (180, 180)

def make_thumbnail(path, size):
    try:
        image = Image.open(path)
        image.thumbnail(size)

        bg = Image.new("RGB", size, (255, 105, 180))
        x = (size[0] - image.width) // 2
        y = (size[1] - image.height) // 2
        bg.paste(image, (x, y))

        draw = ImageDraw.Draw(bg)

        try:
            font = ImageFont.truetype("fonts/Helvetica.ttf", 16)
        except Exception:
            font = ImageFont.load_default()

        filename = os.path.basename(path)

        draw.rectangle(
            [(0, size[1] - 25), (size[0], size[1])],
            fill=(0, 0, 0)
        )

        draw.text(
            (10, size[1] - 22),
            filename,
            fill=(255, 255, 255),
            font=font
        )

        bio = io.BytesIO()
        bg.save(bio, format="PNG")

        return bio.getvalue()

    except Exception as e:
        print("Thumbnail Error:", e)
        return None


def create_scroll_window(image_paths):

    layout_rows = []

    row = []

    for i, path in enumerate(image_paths):

        thumb_data = make_thumbnail(path, THUMB_SIZE)

        if thumb_data:
            row.append(
                sg.Image(
                    data=thumb_data,
                    key=f"IMG_{i}",
                    enable_events=True
                )
            )

        if len(row) == 3:
            layout_rows.append(row)
            row = []

    if row:
        layout_rows.append(row)

    layout = [
        [
            sg.Column(
                layout_rows,
                scrollable=True,
                vertical_scroll_only=True,
                size=(760, 420)
            )
        ],
        [sg.Button("Back")]
    ]

    return sg.Window(
        "Wardrobe Viewer",
        layout,
        element_justification="c",
        finalize=True,
        resizable=True
    )


def create_window(folder):

    if not os.path.exists(folder):
        sg.popup("Folder not found:", folder)
        return

    image_paths = []

    for file in os.listdir(folder):

        if file.lower().endswith(
            (".png", ".jpg", ".jpeg", ".webp")
        ):
            image_paths.append(
                os.path.join(folder, file)
            )

    image_paths.sort()

    print(image_paths)

    window = create_scroll_window(image_paths)

    while True:

        event, values = window.read()

        if event in (sg.WIN_CLOSED, "Back"):
            break

    window.close()