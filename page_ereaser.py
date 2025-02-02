import streamlit as st
import numpy as np
import cv2
from PIL import Image
from streamlit_drawable_canvas import st_canvas
import fitz  # PyMuPDF
import io
from esign_extractor import get_esign  # Make sure this is the function that extracts the e-signature

# Hide Streamlit's default menu and footer
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

st.set_page_config(layout="wide")
st.title("PDF Signatures Exchanger:")

jpg_images = []  # Store extracted images from PDF
final_result = []  # Store edited images

# Function to convert PDF pages into images
def pdf_to_images(pdf_bytes):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    images = []
    for page in doc:
        pix = page.get_pixmap()  # Render page as image
        img = Image.open(io.BytesIO(pix.tobytes("jpeg")))  # Convert bytes to image
        images.append(img)
    return images

# Function to convert list of images to a single PDF
def images_to_pdf(image_list, output_pdf_path):
    if not image_list:
        st.error("No processed images available to save as PDF.")
        return
    image_list[0].save(output_pdf_path, save_all=True, append_images=image_list[1:])
    st.success("PDF saved successfully!")

    # Allow user to download the processed PDF
    with open(output_pdf_path, "rb") as f:
        st.download_button("Download Processed PDF", f, "processed_document.pdf", "application/pdf")

# Function to handle canvas drawing and process image
def get_canvas_result(image_pil):
    img_np = np.array(image_pil)  # Convert PIL image to numpy array

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

# Upload PDF file
uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])
if uploaded_file:
    images = pdf_to_images(uploaded_file.read())  # Convert PDF to images
    if images:
        jpg_images = [np.array(img.convert("RGB")) for img in images]  # Convert images to numpy arrays
        image_pil = images[0]  # Use the first page as reference image

        height, width = jpg_images[0].shape[:2]
        st.subheader("Draw a Rectangle to Erase")

        # Get the canvas result for drawing a rectangle
        canvas_result = get_canvas_result(image_pil)

        # Process the canvas drawing data
        if canvas_result.json_data is not None:
            for obj in canvas_result.json_data["objects"]:
                if obj["type"] == "rect":
                    left, top = int(obj["left"]), int(obj["top"])
                    w, h = int(obj["width"]), int(obj["height"])

                    # Extract e-signature
                    esign = get_esign()  # Ensure this returns a valid signature

                    if esign:
                        esign = esign.resize((w, h))  # Resize the e-signature to match the erased area

                        # Process each image on the PDF
                        for idx, jpg in enumerate(jpg_images):
                            mask = np.zeros(jpg.shape[:2], dtype=np.uint8)
                            mask[top:top + h, left:left + w] = 255

                            # Inpainting to replace erased area with the signature
                            inpainted_image = cv2.inpaint(jpg, mask, inpaintRadius=3, flags=cv2.INPAINT_TELEA)

                            # Merge signature if inpainting was successful
                            inpainted_pil = Image.fromarray(inpainted_image)
                            inpainted_pil.paste(esign, (left, top), esign)  # Paste signature

                            final_result.append(inpainted_pil)  # Append to final result

                        # Check if final_result has images before showing them
                        if final_result:
                            st.subheader("Final Image Preview")
                            st.image(final_result[0], caption="Edited Page", use_column_width=True)

                            # Save and allow user to download the edited PDF
                            images_to_pdf(final_result, "output.pdf")
                        else:
                            st.error("No images to save in the final result.")
                    else:
                        st.error("No e-signature found. Please upload a signature image.")
