import PySimpleGUI as sg

import page_home
import page_wardrobe_category_list
import page_placeholder
import image_viewer_daniel
import camera_test
import page_make_outfit

from feedback_engine import save_outfit_feedback
from ml_style_model import train_model


sg.theme("DarkRed")
sg.set_options(font=("Helvetica.ttf", 16))


def save_rating_and_train(rating):
    outfit = getattr(
        page_make_outfit,
        "last_generated_outfit",
        None
    )

    if not outfit:
        print("No outfit available to rate.")
        return

    save_outfit_feedback(
        outfit,
        rating
    )

    print("Saved outfit rating:", rating)

    try:
        train_model()
    except Exception as e:
        print("Training error:", e)


def main():
    window = page_home.create_window()
    window.maximize()

    while True:
        event, values = window.read()

        if event in (sg.WIN_CLOSED, "Exit"):
            break

        if str(event).startswith("OPEN_PRODUCT_"):
            page_make_outfit.open_product_link(window, event)

        elif event == "View Wardrobe":
            window.close()
            window = page_wardrobe_category_list.create_window()
            window.maximize()

        elif event == "View Outfits":
            window.close()
            window = page_placeholder.create_window()
            window.maximize()

        elif event == "Add An Article":
            window.close()
            camera_test.create_window()
            window = page_home.create_window()
            window.maximize()

        elif event == "Make An Outfit":
            window.close()
            window = page_make_outfit.create_window()
            window.maximize()

        elif event == "Generate Again":
            window.close()
            window = page_make_outfit.create_window()
            window.maximize()

        elif event == "Recommend Products":
            outfit = getattr(
                page_make_outfit,
                "last_generated_outfit",
                None
            )

            if outfit:
                window.close()
                window = page_make_outfit.create_product_window(outfit)
                window.maximize()
            else:
                print("No outfit available for product recommendations.")

        elif event == "Like":
            save_rating_and_train(1)
            window.close()
            window = page_make_outfit.create_window()
            window.maximize()

        elif event == "Dislike":
            save_rating_and_train(-1)
            window.close()
            window = page_make_outfit.create_window()
            window.maximize()

        elif event == "Back":
            window.close()
            window = page_home.create_window()
            window.maximize()

        elif event in page_wardrobe_category_list.wardrobe_event_directory:
            window.close()
            image_viewer_daniel.create_window(
                page_wardrobe_category_list.wardrobe_event_directory[event]
            )
            window = page_wardrobe_category_list.create_window()
            window.maximize()

    window.close()


if __name__ == "__main__":
    main()