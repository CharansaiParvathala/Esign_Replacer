import streamlit as st
from streamlit_image_coordinates import streamlit_image_coordinates
from PIL import Image, ImageDraw

# Load image
img = st.file_uploader("Img",type=["jpg","png","jpeg"])
img = Image.open(img)

# Initialize session state for storing rectangles
if "rectangles" not in st.session_state:
    st.session_state["rectangles"] = []
if "temp_point" not in st.session_state:
    st.session_state["temp_point"] = None


# Function to draw rectangles
def draw_rectangles(image, rectangles):
    draw = ImageDraw.Draw(image)
    for rect in rectangles:
        draw.rectangle(rect, outline="red", width=2)
    return image


# Display image with drawn rectangles
img = draw_rectangles(img.copy(), st.session_state["rectangles"])


# Capture new clicks on the image
value = streamlit_image_coordinates(img, key="pil")

if value is not None:
    point = (value["x"], value["y"])

    if st.session_state["temp_point"] is None:
        # Store first point
        st.session_state["temp_point"] = point
    else:
        # Second point defines opposite corner of rectangle
        x1, y1 = st.session_state["temp_point"]
        x2, y2 = point
        rect = [(min(x1, x2), min(y1, y2)), (max(x1, x2), max(y1, y2))]
        st.session_state["rectangles"].append(rect)
        st.session_state["temp_point"] = None
        st.rerun()
