import PySimpleGUI as sg

sg.theme('LightGreen4')

wardrobe_event_directory = {
    "Hats": "wardrobe_images/wardrobe_hats",
    "Accessories": "wardrobe_images/wardrobe_accessories",
    "Jackets": "wardrobe_images/wardrobe_jackets",
    "Dresses": "wardrobe_images/wardrobe_dresses",
    "Shirts": "wardrobe_images/wardrobe_shirts",
    "Pants": "wardrobe_images/wardrobe_pants",
    "Skirts": "wardrobe_images/wardrobe_skirts",
    "Shoes": "wardrobe_images/wardrobe_shoes",
}

def create_window():
    col1_layout = [
        [sg.Button("Hats")],
        [sg.Button("Accessories")],
        [sg.Button("Jackets")],
        [sg.Button("Dresses")],
    ]
    col2_layout = [
        [sg.Button("Shirts")],
        [sg.Button("Pants")],
        [sg.Button("Skirts")],
        [sg.Button("Shoes")],
    ]
    layout = [
        [sg.Text("What category would you like to view?")],
        [sg.Column(col1_layout), sg.Column(col2_layout)],
        [sg.Button("Back")]
    ]
    return sg.Window("Homepage", layout, 
                    no_titlebar=True, 
                    location=(0, 0), 
                    size=(800, 480), 
                    keep_on_top=True,
                    element_justification='c',
                    finalize=True)