import streamlit as st
import numpy as np
import cv2
from PIL import Image
from streamlit_drawable_canvas import st_canvas
import fitz  # PyMuPDF
import io
from esign_extractor import get_esign  # Import your function

# Set page config
st.set_page_config(layout="wide")

# Hide Streamlit style elements
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            MainMenu {visibility: hidden}
            .reportview-container .main footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# Title of the application
st.title("PDF Signatures Exchanger:")

# Store extracted images and final result
jpg_images = []  # Store extracted images from PDF
final_result = []  # Store edited images

# Function to convert PDF to images
def pdf_to_images(pdf_bytes):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    images = []

    for page in doc:
        pix = page.get_pixmap()
        img = Image.open(io.BytesIO(pix.tobytes("jpeg")))
        images.append(img)

    return images

# Function to convert list of images to PDF
def images_to_pdf(image_list, output_pdf_path):
    """ Convert list of PIL images into a single PDF file. """
    if not image_list:
        st.error("No processed images available to save as PDF.")
        return

    image_list[0].save(output_pdf_path, save_all=True, append_images=image_list[1:])
    st.success("PDF saved successfully!")

    with open(output_pdf_path, "rb") as f:
        st.download_button("Download Processed PDF", f, "processed_document.pdf", "application/pdf")

# Function to process canvas and extract signature
def get_canvas_result(image_pil):
    # Convert PIL image to numpy array (for canvas)
    img_np = np.array(image_pil)

    # Create the canvas
    canvas_result = st_canvas(
        fill_color="rgba(255, 255, 255, 0.5)",  # Transparent overlay
        stroke_width=2,
        stroke_color="red",
        background_image=img_np,  # Use numpy array as background
        update_streamlit=True,
        height=img_np.shape[0],  # Image height
        width=img_np.shape[1],  # Image width
        drawing_mode="rect",  # Drawing mode as rectangle
        key="canvas",
    )
    return canvas_result

# Upload the PDF file
uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])

if uploaded_file:
    images = pdf_to_images(uploaded_file.read())  # Convert PDF to images
    if images:
        jpg_images = [np.array(img.convert("RGB")) for img in images]
        image_pil = images[0]

        height, width = jpg_images[0].shape[:2]
        st.subheader("Draw a Rectangle to Erase")

        # Get the result of the canvas drawing
        canvas_result = get_canvas_result(image_pil)

        if canvas_result.json_data is not None:
            for obj in canvas_result.json_data["objects"]:
                if obj["type"] == "rect":
                    left, top = int(obj["left"]), int(obj["top"])
                    w, h = int(obj["width"]), int(obj["height"])

                    # Extract e-signature using your function
                    esign = get_esign()

                    if esign:
                        esign = esign.resize((w, h))  # Resize to match erased area

                        for idx, jpg in enumerate(jpg_images):
                            mask = np.zeros(jpg.shape[:2], dtype=np.uint8)
                            mask[top:top + h, left:left + w] = 255

                            # Inpainting to fill the erased area
                            inpainted_image = cv2.inpaint(jpg, mask, inpaintRadius=3, flags=cv2.INPAINT_TELEA)

                            # Merge signature if inpainting was successful
                            inpainted_pil = Image.fromarray(inpainted_image)
                            inpainted_pil.paste(esign, (left, top), esign)

                            final_result.append(inpainted_pil)

                        # Check if final_result has images before showing them
                        if final_result:
                            st.subheader("Final Image Preview")
                            st.image(final_result[0], caption="Edited Page", use_column_width=True)

                            # Convert the final result to PDF
                            images_to_pdf(final_result, "output.pdf")
                        else:
                            st.error("No images to save in the final result.")
                    else:
                        st.error("No e-signature found. Please upload a signature image.")
