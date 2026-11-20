import json
import random

#assigning the JSON databases to arrays inside the program
with open('shirts.json', 'r') as file:
        shirts = json.load(file)
with open('pants.json', 'r') as file:
        pants = json.load(file)
with open('skirts.json', 'r') as file:
        skirts = json.load(file)
with open('shoes.json', 'r') as file:
        shoes = json.load(file)
with open('hats.json', 'r') as file:
        hats = json.load(file)
with open('accessories.json', 'r') as file:
        accessories = json.load(file)
with open('dresses.json', 'r') as file:
        dresses = json.load(file)
with open('jackets.json', 'r') as file:
        jackets = json.load(file)

# this function evaluates the points comparing clothing article "candidate" against article "reference"
# currently, it just compares how many traits they have in common, but eventually it will hopefully
# evaluate them according to set of "Fashion Rules", which I do not curretnly know because I don't know fashion
# in the final product, I will probably actually put this into the main function to make the code cleaner
def evaluate_points(reference, candidate):
       # keeping track of the amount of points
        points = 0
        # if they are in the same place, it is invalid
        if reference['place'] == candidate['place']:
                return f"reference:{reference}\ncandidate:{candidate}\nInvalid!"
        # going through every trait and adding points when they are the same
        if reference['primary_color'] == candidate['primary_color']:
                points += 1
        if reference['secondary_color'] == candidate['primary_color']:
                points += 1
        if reference['pattern'] == candidate['pattern']:
                points += 1
        if reference['material'] == candidate['material']:
                points += 1
        return points 

# the actual outfit making algorithm
def make_outfit(reference, includeToggleArr=[]):
        # making a list of all categories to be searched through, this will then be randomized to make the search_order list
        search_through_list = []
        search_order = []
        #if they want to include dresses in the search, we have to make sure that it won't conflict with the reference, and later we
        #will have to make sure not to search through conflicting wardrobes
        if "dresses" in includeToggleArr:
                if reference["place"] in ("shirt", "skirt", "pants", "dress"):
                        include_dresses = False
                        print("Invalid Dress configuration, automatically changing parameter to false, cannot have a dress with a shirt, skirt, or pants. Nor can you include dresses when reference is a dress")
                else:
                        include_dresses = True
        else:
                include_dresses = False
        # this if else statement makes a dictionary of potential search through list arrays depending on the place of the reference and whether
        # we are looking for dresses, much better than brute forcing if statements
        if include_dresses == True or reference["place"] == "dress":
                order_maker_dict = {
                        #if we are searching for "dresses", then the place of the original object cannot be a dress, a shirt, pants, or a skirt
                        #as this would conflict. This has been ruled out by first if statement, and so these places will not be included
                        "dress": ["shoes"],
                        "shoes": ["dresses"],
                        "hat": ["dresses", "shoes"],
                        "accessory": ["dresses", "shoes"]
                }
        else:
                order_maker_dict = {
                        "shirt": ["pants", "skirts", "shoes"],
                        "pants": ["shirts", "shoes"],
                        "skirt": ["shirts", "shoes"],
                        "shoes": ["shirts", "skirts", "pants"],
                        "dress": ["shoes"],
                        "hat": ["shirts", "skirts", "shoes"],
                        "accessory": ["shirts", "skirts", "shoes"]
                }
        wardrobe_directory = {
                "shirts": shirts,
                "pants" : pants,
                "skirts": skirts,
                "shoes": shoes,
                "dresses": dresses,
                "hats": hats,
                "accessories": accessories
        }
        # if hats or accessories are to be searched for, add them to the search through list
        if "hats" in includeToggleArr and reference["place"] != "hat":
                search_through_list += ["hats"]
        if "accessories" in includeToggleArr and reference["place"] != "hat":
                search_through_list += ["accessories"]
        search_through_list += order_maker_dict[reference["place"]]
        # print(search_through_list)
        # the search order is randomized for temperature
        search_order = random.sample(search_through_list, len(search_through_list))

        # now that we have a search order, it is time to look through them and decide what makes the best outfit.
        # I will start by making the simplist version, it will go through each wardrobe and see which piece has the most points against the original,
        # then add that to the outfit output.
        # a future version will also check against parts of the outfit already picked out as well, and compare those values. If i have time, I will even
        # keep track of runner ups to make even more sure that the outfit is good
        if include_dresses == True or reference["place"] == "dress":
                outfit = {
                        "hat": "",
                        "dress": "",
                        "shoes": "",
                        "accessory": ""
                }
        else:
                outfit = {
                        "hat": "",
                        "top": "",
                        "bottom": "",
                        "shoes": "",
                        "accessory": ""
                }

        if reference["place"] == "hat":
                outfit["hat"] = reference
        if reference["place"] == "accessory":
                outfit["accessory"] = reference 
        if reference["place"] == "dress":
                outfit["dress"] = reference 
        if reference["place"] == "shirt":
                outfit["top"] = reference 
        if reference["place"] == ("skirt" or "pants"):
                outfit["bottom"] = reference
        
        for wardrobe in search_order:
                best_piece = {'id': 'null'}
                best_points = 0
                current_wardrobe = wardrobe_directory[wardrobe]
                # print(wardrobe)
                # print(current_wardrobe)
                for piece in current_wardrobe:
                        piece_points = evaluate_points(reference, piece)
                        # print(f"wardrobe: {wardrobe}, \n best id: {best_piece['id']}, best points: {best_points},\n\tcurrent id: {piece['id']}, current points {piece_points}")
                        if piece_points > best_points:
                                best_piece = piece
                                best_points = piece_points
                        elif piece_points == best_points:
                                random_choice = random.choice([best_piece, piece])
                                best_piece = random_choice
                        # if the current piece scores less then the reigning best, then nothing happens
                if wardrobe == "hats":
                        outfit["hat"] = best_piece
                if wardrobe == "accessories":
                        outfit["accessory"] = best_piece
                if wardrobe == "dresses":
                        outfit["dress"] = best_piece
                if wardrobe == "shirts":
                        outfit["shirt"] = best_piece
                if wardrobe == "shoes":
                        outfit["shoes"] = best_piece
                if wardrobe == ("skirts" or "pants"):
                        if outfit["bottom"] == "":
                                outfit["bottom"] = best_piece
                        elif best_points > evaluate_points(reference, outfit["bottom"]):
                                outfit["bottom"] = best_piece
                        elif best_points == evaluate_points(reference, outfit["bottom"]):
                                random_choice = random.choice(best_piece, outfit["bottom"])
                                outfit["bottom"] = random_choice
        return outfit

# i'll add comments and make the code clearer later but for right now it works

print(json.dumps(make_outfit(shirts[0], ["hats"]), indent=4))
# # deleted bits for posterity:
#  if "dresses" in includeToggleArr and reference["place] in ("shirt", "skirt", "pants", "dress"):
#                 dresses = False
#                 print("Invalid Dress configuration, automatically changing parameter to false, cannot have a dress with a shirt, skirt, or pants. Nor can you include dresses when reference is a dress")
#         if reference["place"] == "shirt":
#                 search_through_list += [pants, skirts, shoes]
#         if reference["place"] == "pants"
#                 search_through_list += [shirts, skirts, shoes]
#         if reference["place"] == "skirt"
#                 search_through_list += [shirts, shoes]
#         if reference["place"] 


