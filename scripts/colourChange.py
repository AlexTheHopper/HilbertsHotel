import os
from PIL import Image

# Define the directory containing the .png files
directory = 'C:/Users/alexe/Documents/GitHub/HilbertsHotel/scripts/imagesForChange'
count = 0
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
            # Change all black (also checking for transparency) pixels to white
            if item[:3] == (127, 29, 116):
                new_data.append((0, 132, 188, item[3]))  # Preserve the alpha channel
            elif item[:3] == (99, 22, 90):
                new_data.append((0, 88, 188, item[3]))  # Preserve the alpha channel

            else:
                new_data.append(item)
        
        # Update the image data with the new data
        img.putdata(new_data)
        
        # Save the modified image back to the same file
        img.save(file_path)

print("All pixels have been changed in all",count ,".png files in the 'imagesForChange' folder.")
