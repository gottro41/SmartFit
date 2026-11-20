import PySimpleGUI as sg

sg.theme("DarkRed")

layout = [
    [sg.VPush()],
    [sg.Push(), sg.Text("Loading...", font=("PySimpleGUI_dev/Technology-Bold.ttf", 50)), sg.Push()],
    [sg.VPush()]
]

window = sg.Window(
        "Loading Screen",
        layout,
        location=(0, 0),
        size=(800, 480),
        keep_on_top=True,
        element_justification="c",
        finalize=True,
    )
window.maximize()

while True:
        event, values = window.read()