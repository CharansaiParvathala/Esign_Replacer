import streamlit as st
import numpy as np
from PIL import Image, ImageDraw
from streamlit_image_coordinates import streamlit_image_coordinates
import fitz
import io
import cv2

# Page configuration
st.set_page_config(layout="wide")
st.title("PDF Signatures Exchanger")

# Hide default Streamlit elements
hide_st_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
"""
st.markdown(hide_st_style, unsafe_allow_html=True)

# --- Utility Functions ---
def pdf_to_images(pdf_bytes):
    """Convert PDF to a list of PIL images."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    return [page.get_pixmap().tobytes("jpeg") for page in doc]

def draw_rectangles(image, rectangles):
    """Draw rectangles on an image."""
    img = Image.open(io.BytesIO(image))
    draw = ImageDraw.Draw(img)
    for rect in rectangles:
        draw.rectangle(rect, outline="red", width=2)
    return img

# --- Session State Initialization ---
if "current_page" not in st.session_state:
    st.session_state.update({
        "current_page": 0,
        "rectangles": {},
        "temp_point": None,
        "prev_point": None,
        "original_images": None,
        "processed_images": None,
        "last_rectangle": None  # Stores the last selected rectangle
    })

# --- File Upload & Mode Selection ---
uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])
mode = st.radio("Select mode", ["Each Page", "All Pages"])

if uploaded_file:
    # Initialize PDF images once
    if st.session_state.original_images is None:
        st.session_state.original_images = pdf_to_images(uploaded_file.read())

    total_pages = len(st.session_state.original_images)
    current_page = st.session_state.current_page

    # --- Annotation Interface ---
    st.subheader(f"Page {current_page + 1} of {total_pages}")

    # Display the current image with annotations
    current_image = st.session_state.original_images[current_page]
    annotated_image = draw_rectangles(current_image, st.session_state.rectangles.get(current_page, []))

    # Get click coordinates
    value = streamlit_image_coordinates(
        annotated_image,
        key=f"coord_{current_page}",
        width=Image.open(io.BytesIO(current_image)).size[0],
        height=Image.open(io.BytesIO(current_image)).size[1]
    )

    # Handle clicks
    if value is not None:
        new_point = (value["x"], value["y"])
        if st.session_state.prev_point != new_point:
            st.session_state.prev_point = new_point

            if st.session_state.temp_point is None:
                # First click - store the point
                st.session_state.temp_point = new_point
            else:
                # Second click - create a rectangle
                x1, y1 = st.session_state.temp_point
                x2, y2 = new_point
                rect = [(min(x1, x2), min(y1, y2)), (max(x1, x2), max(y1, y2))]

                # Store the rectangle
                if current_page not in st.session_state.rectangles:
                    st.session_state.rectangles[current_page] = []
                st.session_state.rectangles[current_page].append(rect)

                # Update the last selected rectangle
                st.session_state.last_rectangle = rect

                # Reset temporary points
                st.session_state.temp_point = None
                st.session_state.prev_point = None

                # Automatically advance to the next page
                if current_page < total_pages - 1:
                    st.session_state.current_page += 1

    # --- Apply to All Pages ---
    if mode == "All Pages" and st.session_state.last_rectangle is not None:
        if st.button("Apply to All Pages"):
            for pg in range(current_page, total_pages):
                if pg not in st.session_state.rectangles:
                    st.session_state.rectangles[pg] = []
                st.session_state.rectangles[pg].append(st.session_state.last_rectangle)
            st.success(f"Last rectangle applied to pages {current_page + 1} to {total_pages}!")

    # --- Signature Processing ---
    esign_file = st.sidebar.file_uploader("Upload e-signature", type=["png", "jpg"])
    if esign_file:
        esign = Image.open(esign_file).convert("RGBA")
        processed_images = []

        for idx in range(total_pages):
            if idx in st.session_state.rectangles:
                img_array = np.array(Image.open(io.BytesIO(st.session_state.original_images[idx])))
                for rect in st.session_state.rectangles[idx]:
                    left, top = rect[0]
                    right, bottom = rect[1]
                    w, h = right - left, bottom - top

                    # Inpainting
                    mask = np.zeros(img_array.shape[:2], dtype=np.uint8)
                    mask[top:bottom, left:right] = 255
                    inpainted = cv2.inpaint(img_array, mask, 3, cv2.INPAINT_TELEA)

                    # Paste signature
                    sig_resized = esign.resize((w, h))
                    pil_img = Image.fromarray(inpainted)
                    pil_img.paste(sig_resized, (left, top), sig_resized)
                    processed_images.append(pil_img)

        st.session_state.processed_images = processed_images

    # --- Preview & Download ---
    if st.session_state.processed_images:
        st.sidebar.subheader("Preview")
        st.sidebar.image(st.session_state.processed_images[0], use_column_width=True)
        if st.button("Download Processed PDF"):
            output_path = "signed_document.pdf"
            st.session_state.processed_images[0].save(output_path, save_all=True, append_images=st.session_state.processed_images[1:])
            with open(output_path, "rb") as f:
                st.download_button("Download PDF", f, "signed_document.pdf", "application/pdf")
