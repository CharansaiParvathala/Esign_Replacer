import streamlit as st
import numpy as np
from PIL import Image, ImageDraw
from streamlit_image_coordinates import streamlit_image_coordinates
import fitz
import io
import cv2
from esign_extractor import get_esign  # Import the e-signature extraction function

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
if "rectangles" not in st.session_state:
    st.session_state.update({
        "rectangles": [],  # Stores rectangles for all pages
        "temp_point": None,  # Temporary point for rectangle selection
        "prev_point": None,  # Previous point to avoid duplicate clicks
        "original_images": None,  # Stores the original PDF images
        "processed_images": None  # Stores the processed images with signatures
    })

# --- File Upload ---
uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])

if uploaded_file:
    # Initialize PDF images once
    if st.session_state.original_images is None:
        st.session_state.original_images = pdf_to_images(uploaded_file.read())

    # Display the first page for rectangle selection
    st.subheader("Select the signature area on the first page (applied to all pages)")
    first_page_image = st.session_state.original_images[0]
    annotated_image = draw_rectangles(first_page_image, st.session_state.rectangles)

    # Get click coordinates
    value = streamlit_image_coordinates(
        annotated_image,
        key="coord",
        width=Image.open(io.BytesIO(first_page_image)).size[0],
        height=Image.open(io.BytesIO(first_page_image)).size[1]
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
                st.session_state.rectangles = [rect]  # Apply to all pages

                # Reset temporary points
                st.session_state.temp_point = None
                st.session_state.prev_point = None

    # --- E-Signature Upload ---
    esign_file = st.sidebar.file_uploader("Upload e-signature", type=["png", "jpg"])
    if esign_file:
        # Extract the e-signature using the provided function
        esign = get_esign(esign_file)

        if esign:
            # Process all pages with the selected rectangle and e-signature
            processed_images = []
            for img_bytes in st.session_state.original_images:
                img_array = np.array(Image.open(io.BytesIO(img_bytes)))

                # Apply the rectangle to each page
                for rect in st.session_state.rectangles:
                    left, top = rect[0]
                    right, bottom = rect[1]
                    w, h = right - left, bottom - top

                    # Inpainting to remove the existing content
                    mask = np.zeros(img_array.shape[:2], dtype=np.uint8)
                    mask[top:bottom, left:right] = 255
                    inpainted = cv2.inpaint(img_array, mask, 3, cv2.INPAINT_TELEA)

                    # Resize and paste the e-signature
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
