import streamlit as st
import numpy as np
import cv2
from PIL import Image

def merge(inpainted_image, esign, height, width, left, top):
    # Check if esign is a PIL Image, if so, convert to NumPy array
    if isinstance(esign, Image.Image):
        esign = np.array(esign)

    # Convert the NumPy array to a PIL Image
    esign_pil = Image.fromarray(esign)

    # Resize the overlay image to fit the selected rectangle
    overlay_resized = esign_pil.resize((width, height), Image.LANCZOS)
    overlay_resized_np = np.array(overlay_resized)

    # Step 4: Resulting Image with Overlay
    st.header("Step 4: Resulting Image with Overlay")

    # Ensure the base image has an alpha channel
    if inpainted_image.shape[2] == 3:
        inpainted_image = cv2.cvtColor(inpainted_image, cv2.COLOR_BGR2BGRA)
    elif inpainted_image.shape[2] == 4:
        inpainted_image = cv2.cvtColor(inpainted_image, cv2.COLOR_BGRA2BGRA)

    # Create a copy of the base image to place the overlay
    result_image_np = inpainted_image.copy()

    # Extract the alpha mask of the overlay
    overlay_mask = overlay_resized_np[:, :, 3] / 255.0
    overlay_inv_mask = 1.0 - overlay_mask

    # Get the region of interest (ROI) on the base image
    roi = result_image_np[top:top + height, left:left + width]

    # Blend the overlay with the ROI
    for c in range(0, 3):
        roi[:, :, c] = (overlay_mask * overlay_resized_np[:, :, c] +
                        overlay_inv_mask * roi[:, :, c])

    # Replace the ROI on the base image with the blended result
    result_image_np[top:top + height, left:left + width] = roi

    # Convert the result back to a PIL image and display
    result_image = Image.fromarray(result_image_np)
    return result_image
