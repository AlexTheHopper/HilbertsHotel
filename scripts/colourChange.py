import os
from PIL import Image
import random

# Define the direct_ory containing the .png files
direct_ory = 'C:/Users/alexe/Documents/GitHub/HilbertsHotel/scripts/imagesForChange'
count = 0
colours = [(255, 255, 255), (255, 255, 0), (255, 0, 0), (255, 153, 0), (0, 0, 255), (0, 204, 0)]
# Loop through all files in the direct_ory
for filename in os.listdir(direct_ory):
    if filename.endswith('.png'):
        file_path = os.path.join(direct_ory, filename)
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
            # Change all black (also checking for transparency) pixels to white
            if item[:3] == (255, 127, 0):
                new_data.append((255, 61, 74) if random.random() < 0.5 else (153, 248, 255)) 
            # elif item[:3] == (130, 238, 255):
            #     new_data.append((255, 71, 30)) 

            # elif item[:3] == (153, 101, 0):
            #     new_data.append((84, 20, 28)) 
            # elif item[:3] == (109, 73, 0):
            #     new_data.append((63, 15, 21)) 

            # elif item[:3] == (20, 16, 32):
            #     new_data.append((114, 27, 39)) 
            # elif item[:3] == (255, 136, 45):
            #     new_data.append((84, 20, 28)) 

            else:
                new_data.append(item)
        
        # Update the image data with the new data
        img.putdata(new_data)
        
        # Save the modified image back to the same file
        img.save(file_path)

print("All pixels have been changed in all",count ,".png files in the 'imagesForChange' folder.")
