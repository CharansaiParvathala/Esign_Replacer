import streamlit as st
import numpy as np
import cv2
from PIL import Image
import io
import base64
import fitz  # PyMuPDF
from esign_extractor import get_esign  # This should return the e-signature as a PIL image

# Function to convert PDF pages into images
def pdf_to_images(pdf_bytes):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    images = []
    for page in doc:
        pix = page.get_pixmap()
        img = Image.open(io.BytesIO(pix.tobytes("jpeg")))
        images.append(img)
    return images

# Function to convert list of images to a single PDF and allow download
def images_to_pdf(image_list, output_pdf_path):
    if not image_list:
        st.error("No processed images available to save as PDF.")
        return
    image_list[0].save(output_pdf_path, save_all=True, append_images=image_list[1:])
    st.success("PDF saved successfully!")
    with open(output_pdf_path, "rb") as f:
        st.download_button("Download Processed PDF", f, "processed_document.pdf", "application/pdf")

st.set_page_config(layout="wide")
st.title("PDF Signatures Exchanger:")

# Upload PDF file
uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])
if uploaded_file:
    images = pdf_to_images(uploaded_file.read())
    if images:
        # We'll work with the first page as a reference image
        image_pil = images[0]
        # Convert all pages to numpy arrays (RGB)
        jpg_images = [np.array(img.convert("RGB")) for img in images]

        st.subheader("Tap two points on the image to define the rectangle area (top-left and bottom-right)")

        # Use the community component to get click coordinates.
        # (Install via: pip install streamlit-image-coordinates)
        import streamlit_image_coordinates as sic

        # The component displays the image and returns the (x, y) coordinate of the tap.
        click_result = sic.clickable_image(image_pil, key="clickable_image")

        if click_result is not None:
            # We need two clicks to define a rectangle.
            if "first_click" not in st.session_state:
                st.session_state.first_click = click_result
                st.info("First point recorded. Please tap on the opposite corner of the rectangle.")
            else:
                second_click = click_result
                first_click = st.session_state.first_click

                # Compute rectangle from the two clicks
                left = min(first_click["x"], second_click["x"])
                top = min(first_click["y"], second_click["y"])
                width = abs(second_click["x"] - first_click["x"])
                height = abs(second_click["y"] - first_click["y"])

                st.write(f"Defined rectangle: left={left}, top={top}, width={width}, height={height}")

                if st.button("Apply Signature Replacement"):
                    # Extract e-signature (should return a PIL image)
                    esign = get_esign()
                    if not esign:
                        st.error("No e-signature found. Please upload a signature image.")
                    else:
                        # Resize the signature to match the selected rectangle
                        esign = esign.resize((width, height))
                        final_result = []

                        for idx, jpg in enumerate(jpg_images):
                            mask = np.zeros(jpg.shape[:2], dtype=np.uint8)
                            mask[top:top + height, left:left + width] = 255

                            # Inpaint the area to remove the original signature or mark
                            inpainted_image = cv2.inpaint(jpg, mask, inpaintRadius=3, flags=cv2.INPAINT_TELEA)

                            # Convert back to PIL image and paste the new e-signature over the inpainted area
                            inpainted_pil = Image.fromarray(inpainted_image)
                            inpainted_pil.paste(esign, (left, top), esign)
                            final_result.append(inpainted_pil)

                        if final_result:
                            st.subheader("Final Image Preview")
                            st.image(final_result[0], caption="Edited Page", use_column_width=True)
                            images_to_pdf(final_result, "output.pdf")
                        else:
                            st.error("No images were processed.")

                # Optionally, once the rectangle is defined, clear the first click for a new selection:
                if st.button("Reset Selection"):
                    del st.session_state["first_click"]
                    
