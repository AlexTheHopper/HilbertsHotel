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
            if i > 0 and j in range(4,12):

                v = hsv_array[i, j, 2]
                if v not in [40,41]:

                    hsv_array[i, j, 1] = 255  # Set S to V
                    hsv_array[i, j, 2] = 255  # Set S to V
                    hsv_array[i, j, 0] = random.choice([0, 36, 60, 120, 240])  # Set H to V
                    hsv_array[i, j, 0] = int(hsv_array[i, j, 0] / 1.41)
                    if hsv_array[i, j, 0] == 0 and random.random() < 0.5:
                        hsv_array[i, j, 1] = 0
                

    # Convert numpy array back to image
    new_hsv_image = Image.fromarray(hsv_array, 'HSV')

    # Convert back to RGB
    rgb_image = new_hsv_image.convert('RGB')

    # Save the modified image
    rgb_image.save(save_path)

def process_directory(input_directory, output_directory):
    # Ensure the output directory exists
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    # Process each image in the directory
    for filename in os.listdir(input_directory):
        if filename.endswith(('.png', '.jpg', '.jpeg')):
            image_path = os.path.join(input_directory, filename)
            save_path = os.path.join(output_directory, filename)
            process_image(image_path, save_path)
            print(f"Processed {filename}")

# Define the input and output directories
input_directory = 'C:/Users/alexe/Documents/GitHub/HilbertsHotel/scripts/imagesForChange'
output_directory = 'C:/Users/alexe/Documents/GitHub/HilbertsHotel/scripts/imagesForChange'

# Process all images in the directory
process_directory(input_directory, output_directory)