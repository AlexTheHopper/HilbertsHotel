import os
from PIL import Image
import numpy as np
import random

def process_image(image_path, save_path):
    # Load the image
    image = Image.open(image_path)

    # Convert image to HSV
    hsv_image = image.convert('HSV')

    # Convert image to numpy array
    hsv_array = np.array(hsv_image)

    # Iterate through each pixel and change H and S to the V value
    for i in range(hsv_array.shape[0]):
        for j in range(hsv_array.shape[1]):
            if i > 0 and j in range(7,9):

                diff = hsv_array[i, j, 2] - 79
                new = 79 - diff
                hsv_array[i, j, 2] = new

                
                

    # Convert numpy array back to image
    new_hsv_image = Image.fromarray(hsv_array, 'HSV')

    # Convert back to RGB
    rgb_image = new_hsv_image.convert('RGB')

    # Save the modified image
    rgb_image.save(save_path)

def process_direct_ory(input_direct_ory, output_direct_ory):
    # Ensure the output direct_ory exists
    if not os.path.exists(output_direct_ory):
        os.makedirs(output_direct_ory)

    # Process each image in the direct_ory
    for filename in os.listdir(input_direct_ory):
        if filename.endswith(('.png', '.jpg', '.jpeg')):
            image_path = os.path.join(input_direct_ory, filename)
            save_path = os.path.join(output_direct_ory, filename)
            process_image(image_path, save_path)
            print(f"Processed {filename}")

# Define the input and output direct_ories
input_direct_ory = 'C:/Users/alexe/Documents/GitHub/HilbertsHotel/scripts/imagesForChange'
output_direct_ory = 'C:/Users/alexe/Documents/GitHub/HilbertsHotel/scripts/imagesForChange'

# Process all images in the direct_ory
process_direct_ory(input_direct_ory, output_direct_ory)