import os
import io
from PIL import Image, ImageDraw, ImageFont
import PySimpleGUI as sg
import json

with open('wardrobe_data/shirts.json', 'r') as file:
        shirts_json = json.load(file)
with open('wardrobe_data/pants.json', 'r') as file:
        pants_json = json.load(file)
with open('wardrobe_data/skirts.json', 'r') as file:
        skirts_json = json.load(file)
with open('wardrobe_data/shoes.json', 'r') as file:
        shoes_json = json.load(file)
with open('wardrobe_data/hats.json', 'r') as file:
        hats_json = json.load(file)
with open('wardrobe_data/accessories.json', 'r') as file:
        accessories_json = json.load(file)
with open('wardrobe_data/dresses.json', 'r') as file:
        dresses_json = json.load(file)
with open('wardrobe_data/jackets.json', 'r') as file:
        jackets_json = json.load(file)

json_directory = {
    "wardrobe_images/wardrobe_hats": hats_json,
    "wardrobe_images/wardrobe_accessories": accessories_json,
    "wardrobe_images/wardrobe_jackets": jackets_json,
    "wardrobe_images/wardrobe_dresses": dresses_json,
    "wardrobe_images/wardrobe_shirts": shirts_json,
    "wardrobe_images/wardrobe_pants": pants_json,
    "wardrobe_images/wardrobe_skirts": skirts_json,
    "wardrobe_images/wardrobe_shoes": shoes_json
}

def create_window(folder):
    sg.theme('DarkRed')

    image_paths = []

    IMAGE_FOLDER = folder      # Folder containing images
    THUMB_SIZE = (180, 180)
    COLUMNS = 4

    SUPPORTED = (".png", ".jpg", ".jpeg")

    image_paths = [
        os.path.join(IMAGE_FOLDER, f)
        for f in os.listdir(IMAGE_FOLDER)
        if f.lower().endswith(SUPPORTED)
    ]
    # print(image_paths)

    def create_scroll_window():

        # -----------------------------
        # CREATE THUMBNAIL WITH LABEL
        # -----------------------------

        def make_thumbnail(path, size):
            img = Image.open(path).convert("RGB")
            img.thumbnail(size)

            # Create background
            thumb = Image.new("RGB", size, (30, 30, 30))

            # Center image
            x = (size[0] - img.width) // 2
            y = (size[1] - img.height) // 2
            thumb.paste(img, (x, y))

            draw = ImageDraw.Draw(thumb)

            #thumb = Image.alpha_composite(
            #    thumb.convert("RGBA")
            #)

            draw = ImageDraw.Draw(thumb)

            filename = os.path.basename(path)

            # Default font
            font = ImageFont.truetype("Helvetica.ttf", 16)

            # Text
            draw.text(
                (14, size[1] - 24),
                filename,
                fill="white",
                font=font
            )

            # Convert to bytes
            bio = io.BytesIO()
            thumb.save(bio, format="PNG")

            return bio.getvalue()

        # -----------------------------
        # LOAD IMAGES
        # -----------------------------



        # -----------------------------
        # BUILD GRID
        # -----------------------------

        rows = []
        current_row = []

        for i, path in enumerate(image_paths):
            thumb_data = make_thumbnail(path, THUMB_SIZE)

            button = sg.Button(
                image_data=thumb_data,
                key=path,
                border_width=0,
                pad=(5, 5)
            )

            current_row.append(button)

            if (i + 1) % COLUMNS == 0:
                rows.append(current_row)
                current_row = []

        if current_row:
            rows.append(current_row)

        # -----------------------------
        # SCROLLABLE COLUMN
        # -----------------------------

        layout = [
            [sg.Button("Back", size=(10,2))],
            [
                sg.Column(
                    rows,
                    scrollable=True,
                    sbar_width=30,
                    sbar_arrow_width=30,
                    vertical_scroll_only=True,
                    expand_x=True,
                    expand_y=True,
                    key="-SCROLL-",
                )
            ]
        ]
        
        
        return sg.Window(
            "Touchscreen Image Viewer",
            layout,
            #element_justification="c",
            location=(0, 0),
            size=(800, 480),
            no_titlebar=True,
            finalize=True,
            resizable=True
        )

        # -----------------------------
        # ENABLE CLICK-DRAG SCROLLING
        # -----------------------------

        widget = window["-SCROLL-"].Widget.canvas

        def start_scroll(event):
            widget.scan_mark(0, event.y)

        def drag_scroll(event):
            widget.scan_dragto(0, event.y, gain=1)

        widget.xview_moveto(0)

        widget.bind("<ButtonPress-1>", start_scroll)
        widget.bind("<B1-Motion>", drag_scroll)
        print(image_paths)

    # -----------------------------
    # FULL IMAGE WINDOW
    # -----------------------------

    def open_full_image(path):
        img = Image.open(path)

        max_size = (800, 480)
        img.thumbnail(max_size)

        bio = io.BytesIO()
        img.save(bio, format="PNG")
        
        search_through_arr = json_directory[folder]
        # print(path)
        # print(search_through_arr)
        for article in search_through_arr:
            # print(f"\t{article["image_path"]}")
            # print(path == article["image_path"])
            if path == article["image_path"]:
                article_dict = article
                print("Found it!")
        if article_dict["secondary_color"] != "none":
            fullscreen_text = f"{article_dict["primary_color"]} and {article_dict["secondary_color"]} {article_dict["pattern"]}\n{article_dict["style"]}\n good to wear in {article_dict["temperature"]}"
        else:
            fullscreen_text = f"{article_dict["primary_color"]} {article_dict["style"]}\n good to wear in {article_dict["temperature"]}"
        print(fullscreen_text)        

        layout = [
            [sg.Button("Back", size=(10,2))],
            [sg.Image(data=bio.getvalue()), sg.Text(fullscreen_text, font="Times")]
        ]
        
        return sg.Window(
            os.path.basename(path),
            layout,
            element_justification="c",
            no_titlebar=True, 
            location=(0, 0), 
            size=(800, 480),
            modal=True,
            finalize=True,
            resizable=True
        )
    print(image_paths)
    # -----------------------------
    # EVENT LOOP
    # -----------------------------

    window = create_scroll_window()
    window_tracker = "scroll window"
    window.maximize()

    while True:
        #print(image_paths)
        event, values = window.read()
        
        if event == sg.WIN_CLOSED:
            break

        if window_tracker == "scroll window" and event == "Back":
            break

        if event in image_paths:
            window.close()
            window_tracker = "full image"
            window = open_full_image(event)
            window.maximize()
        
        if window_tracker == "full image" and event == "Back":
            window.close()
            window_tracker = "scroll window"
            window = create_scroll_window()
            window.maximize()

    window.close()