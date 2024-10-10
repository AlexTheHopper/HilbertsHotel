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
            if item[:3] == (155, 155, 155):
                new_data.append((91, 129, 150)) 
            elif item[:3] == (178, 178, 178):
                new_data.append((111, 158, 183)) 
            elif item[:3] == (198, 198, 198):
                new_data.append((121, 171, 199)) 
            elif item[:3] == (226, 226, 226):
                new_data.append((136, 192, 224)) 

            else:
                new_data.append(item)
        
        # Update the image data with the new data
        img.putdata(new_data)
        
        # Save the modified image back to the same file
        img.save(file_path)

print("All pixels have been changed in all",count ,".png files in the 'imagesForChange' folder.")
