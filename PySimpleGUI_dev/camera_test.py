import os
import time
import tempfile

import cv2
import PySimpleGUI as sg

from clothing_classifier import analyze_clothing, save_item_to_category_file


def create_window():
    sg.theme("DarkRed")

    camera_column = [
        [sg.Button("Back", size=(10, 1))],
        [sg.Text("Tap the camera view to take a photo in 5 seconds", font=("Helvetica", 12))],
        [sg.Image(key="-IMAGE-", size=(480, 480), enable_events=True)],
        [sg.Text("", key="-STATUS-", size=(45, 2), font=("Helvetica", 14))],
    ]

    review_column = [
        [sg.Text("Save or retake this picture?", font=("Helvetica", 14, "bold"))],
        [
            sg.Button("Retake", button_color=("white", "red"), size=(12, 2)),
            sg.Button("Save", button_color=("white", "green"), size=(12, 2)),
        ],
        [sg.Image(key="-PREVIEW-", size=(360, 360))],
        [sg.Text("", key="-REVIEW_TEXT-", size=(40, 8), font=("Helvetica", 12))],
    ]

    layout = [
        [
            sg.Column(camera_column, key="-CAMERA-PANEL-", visible=True, element_justification="c"),
            sg.Column(review_column, key="-REVIEW-PANEL-", visible=False, element_justification="c"),
        ]
    ]

    window = sg.Window(
        "Article Capture System",
        layout,
        no_titlebar=True,
        location=(0, 0),
        size=(800, 560),
        keep_on_top=True,
        element_justification="c",
        finalize=True,
    )
    window.maximize()

    cap = cv2.VideoCapture(0, cv2.CAP_V4L2)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 480)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    if not cap.isOpened():
        window["-STATUS-"].update("Error: Could not open USB webcam.", text_color="red")

    countdown_active = False
    review_mode_active = False
    target_time = 0
    last_displayed_sec = -1

    temp_path = None
    captured_item = None
    captured_frame_bgr = None

    while True:
        event, values = window.read(timeout=20)

        if event in (sg.WIN_CLOSED, "Back"):
            break

        if not review_mode_active:
            if event == "-IMAGE-" and not countdown_active:
                countdown_active = True
                target_time = time.time() + 5.0
                last_displayed_sec = -1
                window["-STATUS-"].update("Self-timer started...")

            ret, frame_bgr = cap.read()

            if ret:
                display_frame = frame_bgr.copy()

                if countdown_active:
                    remaining_time = target_time - time.time()
                    current_sec = int(remaining_time) + 1

                    if remaining_time > 0:
                        if current_sec != last_displayed_sec:
                            window["-STATUS-"].update(f"Taking photo in {current_sec}s...")
                            last_displayed_sec = current_sec

                        cv2.putText(
                            display_frame,
                            str(current_sec),
                            (50, 80),
                            cv2.FONT_HERSHEY_TRIPLEX,
                            2,
                            (0, 0, 255),
                            4,
                            cv2.LINE_AA,
                        )

                    else:
                        captured_frame_bgr = frame_bgr.copy()

                        with tempfile.NamedTemporaryFile(
                            suffix=".png",
                            delete=False,
                            dir="uploads",
                        ) as temp_file:
                            temp_path = temp_file.name

                        cv2.imwrite(temp_path, captured_frame_bgr)

                        success, encoded_img = cv2.imencode(".png", captured_frame_bgr)

                        if success:
                            window["-PREVIEW-"].update(data=encoded_img.tobytes())

                        window["-STATUS-"].update("Analyzing clothing...")

                        try:
                            captured_item = analyze_clothing(temp_path)

                            review_text = (
                                f"Category: {captured_item.get('place')}\n"
                                f"Style: {captured_item.get('style')}\n"
                                f"Primary: {captured_item.get('primary_color')}\n"
                                f"Secondary: {captured_item.get('secondary_color')}\n"
                                f"Pattern: {captured_item.get('pattern')}\n"
                                f"Material: {captured_item.get('material')}\n"
                                f"Weather: {captured_item.get('temperature')}"
                            )

                            window["-REVIEW_TEXT-"].update(review_text)

                        except Exception as e:
                            captured_item = None
                            window["-REVIEW_TEXT-"].update(f"Classification failed:\n{e}")

                        review_mode_active = True
                        countdown_active = False
                        last_displayed_sec = -1

                        window["-CAMERA-PANEL-"].update(visible=False)
                        window["-REVIEW-PANEL-"].update(visible=True)

                success, encoded_img = cv2.imencode(".png", display_frame)

                if success:
                    window["-IMAGE-"].update(data=encoded_img.tobytes())

        else:
            if event == "Retake":
                if temp_path and os.path.exists(temp_path):
                    os.remove(temp_path)

                temp_path = None
                captured_item = None
                captured_frame_bgr = None

                review_mode_active = False

                window["-REVIEW-PANEL-"].update(visible=False)
                window["-CAMERA-PANEL-"].update(visible=True)
                window["-STATUS-"].update("Photo discarded. Tap to try again.", text_color="red")
                window["-REVIEW_TEXT-"].update("")

            elif event == "Save":
                if captured_item and temp_path:
                    try:
                        save_item_to_category_file(captured_item, temp_path)
                        window["-STATUS-"].update("Saved!", text_color="green")
                    except Exception as e:
                        window["-STATUS-"].update(f"Save failed: {e}", text_color="red")

                else:
                    window["-STATUS-"].update("No valid item to save.", text_color="red")

                temp_path = None
                captured_item = None
                captured_frame_bgr = None

                review_mode_active = False

                window["-REVIEW-PANEL-"].update(visible=False)
                window["-CAMERA-PANEL-"].update(visible=True)
                window["-REVIEW_TEXT-"].update("")

    cap.release()
    window.close()