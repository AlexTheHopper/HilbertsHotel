import os
from PIL import Image

# Define the directory containing the .png files
directory = 'C:/Users/alexe/Documents/GitHub/HilbertsHotel/scripts/imagesForChange'
count = 0

# Function to convert Hex to RGB
def hex_to_rgb(hex_value):
    hex_value = hex_value.lstrip('#')
    return tuple(int(hex_value[i:i+2], 16) for i in (0, 2, 4))

# Define a dictionary for RGB-to-Hex mappings for color replacement
# RGB keys and hex values for replacements
#Hilbert:
color_replacements = {
    (68, 68, 68): '#007700',        # Hat top
    (48, 48, 48): '#0000CC',        # Hat brim

    (175, 168, 151): '#afa897',     # Skin
    (2, 2, 2): '#020202',           # Eye
    (137, 132, 119): '#898477',     # Eye - blink

    (114, 49, 206): '#020202',      # Tie
    (76, 33, 137): '#020202',       # Belt - main
    (57, 26, 104): '#020202',       # Belt - trim

    (38, 36, 58): '#331400',        # Body - light
    (20, 16, 32): '#260F00'         # Body - dark
}

#GunGuy:
color_replacements = {
    (45, 9, 19): '#5E2559',        # Hair

    (196, 44, 54): '#9B3693',      # Shirt 
    (56, 14, 15): '#30092D',       # Vest / pants dark
    (79, 20, 21): '#4C0E48',       # Pants light
}

# Loop through all files in the directory
for filename in os.listdir(directory):
    if filename.endswith('.png'):
        file_path = os.path.join(directory, filename)
        count += 1
        
        # Open the image
        img = Image.open(file_path)
        
        # Convert the image to RGBA if it's not already in that mode
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # Load the image data
        data = img.getdata()
        
        # Create a new list to hold the modified image data
        new_data = []
        
        # Loop through each pixel in the image data
        for item in data:
            rgb_value = item[:3]  # Extract the RGB value
            
            if rgb_value in color_replacements:
                # Convert hex to RGB for replacement
                new_rgb = hex_to_rgb(color_replacements[rgb_value])
                #print(f"Replacing {rgb_value} with {color_replacements[rgb_value]}")
                new_data.append(new_rgb + (item[3],))  # Append the new RGB and keep the alpha value
            else:
                new_data.append(item)
        
        # Update the image data with the new data
        img.putdata(new_data)
        
        # Save the modified image back to the same file
        img.save(file_path)

print(f"All pixels have been changed in all {count} .png files in the 'imagesForChange' folder.")