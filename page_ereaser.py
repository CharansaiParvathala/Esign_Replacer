import streamlit as st
from PIL import Image
import numpy as np

# Function to handle ROI selection using Streamlit
def select_roi(image):
    st.write("### Select a Region of Interest (ROI)")
    st.write("1. Click and drag to draw a rectangle.")
    st.write("2. Double-click inside the rectangle to confirm your selection.")

    # Convert image to numpy array
    image_np = np.array(image)

    # Use Streamlit's image component with a custom key
    st.image(image, caption="Draw a rectangle on the image", use_column_width=True)

    # Use Streamlit's file uploader to simulate ROI selection
    roi_coords = st.text_input("Enter ROI coordinates (left, top, width, height):", "0, 0, 100, 100")
    left, top, width, height = map(int, roi_coords.split(","))

    return left, top, width, height

# Streamlit app
def main():
    st.title("Interactive ROI Selection")
    st.write("Upload an image and select a region of interest (ROI) to get its coordinates.")

    # Upload image
    uploaded_file = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Image", use_column_width=True)

        # Select ROI
        roi_coords = select_roi(image)

        if roi_coords:
            left, top, width, height = roi_coords
            st.write("### Selected ROI Coordinates:")
            st.write(f"Left: {left}, Top: {top}, Width: {width}, Height: {height}")

            # Display the cropped region
            cropped_image = image.crop((left, top, left + width, top + height))
            st.image(cropped_image, caption="Cropped Region", use_column_width=True)

if __name__ == "__main__":
    main()
