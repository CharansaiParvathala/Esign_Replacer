import streamlit as st
import cv2
import numpy as np
from PIL import Image

# Function to handle mouse events for selecting ROI
def select_roi(image):
    st.write("### Select a Region of Interest (ROI)")
    st.write("1. Click and drag to draw a rectangle.")
    st.write("2. Double-click inside the rectangle to confirm your selection.")

    # Convert image to OpenCV format
    image_cv = np.array(image)
    image_cv = cv2.cvtColor(image_cv, cv2.COLOR_RGB2BGR)

    # Initialize global variables for ROI selection
    ref_point = []
    cropping = False

    def click_and_crop(event, x, y, flags, param):
        nonlocal ref_point, cropping

        if event == cv2.EVENT_LBUTTONDOWN:
            ref_point = [(x, y)]
            cropping = True

        elif event == cv2.EVENT_LBUTTONUP:
            ref_point.append((x, y))
            cropping = False

            # Draw the rectangle on the image
            cv2.rectangle(image_cv, ref_point[0], ref_point[1], (0, 255, 0), 2)
            cv2.imshow("Image", image_cv)

        elif event == cv2.EVENT_LBUTTONDBLCLK:
            cv2.destroyAllWindows()

    # Create a named window and set the mouse callback
    cv2.namedWindow("Image")
    cv2.setMouseCallback("Image", click_and_crop)

    # Display the image and wait for ROI selection
    while True:
        cv2.imshow("Image", image_cv)
        key = cv2.waitKey(1) & 0xFF

        # Break the loop if 'q' is pressed or ROI is selected
        if key == ord("q") or len(ref_point) == 2:
            break

    cv2.destroyAllWindows()

    # Return the coordinates of the selected ROI
    if len(ref_point) == 2:
        x1, y1 = ref_point[0]
        x2, y2 = ref_point[1]
        left = min(x1, x2)
        top = min(y1, y2)
        width = abs(x2 - x1)
        height = abs(y2 - y1)
        return left, top, width, height
    else:
        return None

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
