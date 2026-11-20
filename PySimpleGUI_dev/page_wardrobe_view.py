import os
import io
from PIL import Image, ImageDraw, ImageFont
import PySimpleGUI as sg

def create_window(image_folder_path):
    IMAGE_FOLDER = image_folder_path
    THUMB_SIZE = (180, 180)
    COLUMNS = 4
    SUPPORTED = (".png", ".jpg", ".jpeg")

    def make_thumbnail(path, thumb_size):
        img = Image.open(path).convert("RGB")
        img.thumbnail(thumb_size)

        overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        filename = os.path.basename(path)
        draw.text(
            (12, image.height - 12),
            filename,
            fill=(255, 255, 255, 255)
        )

        combined = Image.alpha_composite(
            image.convert("RGBA"),
            overlay
        )

        bio = io.BytesIO()
        thumb.save(bio, format="PNG")

        image_files = [
            os.path.join(IMAGE_FOLDER, f)
            for f in os.listdir(IMAGE_FOLDER)
            if f.lower().endswith(SUPPORTED)
        ]

        return bio.getvalue()

    



    layout = [
        [sg.Button("Back")]
    ]