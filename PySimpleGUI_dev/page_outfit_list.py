import PySimpleGUI as sg

sg.theme('LightGreen4')

def create_window():
    layout = [
            [sg.Text("THIS IS A PLACEHOLDER, CHANGE LATER")],
            [sg.Button("Home")]
        ]
    return sg.Window("View Outfits", layout, 
        no_titlebar=True,
        location=(0, 0), 
        size=(800, 480), 
        keep_on_top=True,
        element_justification='c',
        finalize=True)
