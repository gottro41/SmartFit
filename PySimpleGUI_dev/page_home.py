import PySimpleGUI as sg

sg.theme("DarkRed")


def create_window():
    layout = [
        [sg.VPush()],
        [sg.Text("Welcome to SmartFit", font=("Helvetica", 26, "bold"))],
        [sg.Text("Your AI wardrobe assistant", font=("Helvetica", 16))],
        [sg.Button("View Wardrobe", size=(18, 2))],
        #[sg.Button("View Outfits", size=(18, 2))],
        [sg.Button("Add An Article", size=(18, 2))],
        [sg.Button("Make An Outfit", size=(18, 2))],
        #[sg.Button("Exit", size=(18, 2))],
        [sg.VPush()]
    ]

    return sg.Window(
        "SmartFit",
        layout,
        location=(0, 0),
        size=(800, 480),
        keep_on_top=True,
        element_justification="c",
        finalize=True,
    )