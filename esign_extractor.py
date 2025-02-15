import streamlit as st
from io import BytesIO
from PIL import Image
import cv2
import numpy as np

def remove_background(image):
    """Remove background from a signature image using OpenCV."""
    # Convert PIL image to OpenCV format
    image = np.array(image.convert("RGB"))

    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

    # Apply thresholding to create a binary mask
    _, binary = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)

    # Convert back to PIL image
    return Image.fromarray(binary)

def get_esign():
    rawsign = st.file_uploader('Signature Image', type=["jpg", "jpeg", "png"])
    if rawsign:
        image = Image.open(rawsign)
        esign = remove_background(image)
        return esign
