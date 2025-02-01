import streamlit as st
import numpy as np
import cv2
from PIL import Image
from streamlit_drawable_canvas import st_canvas
import fitz  # PyMuPDF
import io
from esign_extractor import get_esign  # Import your function

st.set_page_config(layout="wide")

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
st.title("PDF Signatures Exchanger:")

jpg_images = []  # Store extracted images from PDF
final_result = []  # Store edited images


def pdf_to_images(pdf_bytes):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    images = []

    for page in doc:
        pix = page.get_pixmap()
        img = Image.open(io.BytesIO(pix.tobytes("jpeg")))
        images.append(img)

    return images


def images_to_pdf(image_list, output_pdf_path):
    """ Convert list of PIL images into a single PDF file. """
    if not image_list:
        st.error("No processed images available to save as PDF.")
        return

    image_list[0].save(output_pdf_path, save_all=True, append_images=image_list[1:])

    st.success("PDF saved successfully!")

    with open(output_pdf_path, "rb") as f:
        st.download_button("Download Processed PDF", f, "processed_document.pdf", "application/pdf")


uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])
if uploaded_file:
    images = pdf_to_images(uploaded_file.read())  # Convert PDF to images
    if images:
        jpg_images = [np.array(img.convert("RGB")) for img in images]
        image_pil = images[0]

        height, width = jpg_images[0].shape[:2]
        st.subheader("Draw a Rectangle to Erase")

        canvas_result = st_canvas(
            fill_color="rgba(255, 255, 255, 0.5)",  # Transparent overlay
            stroke_width=2,
            stroke_color="red",
            background_image=image_pil,
            update_streamlit=True,
            height=height,
            width=width,
            drawing_mode="rect",
            key="canvas",
        )

        if canvas_result.json_data is not None:
            for obj in canvas_result.json_data["objects"]:
                if obj["type"] == "rect":
                    left, top = int(obj["left"]), int(obj["top"])
                    w, h = int(obj["width"]), int(obj["height"])

                    # Extract e-signature
                    esign = get_esign()

                    if esign:
                        esign = esign.resize((w, h))  # Resize to match erased area

                        for idx, jpg in enumerate(jpg_images):
                            mask = np.zeros(jpg.shape[:2], dtype=np.uint8)
                            mask[top:top + h, left:left + w] = 255

                            inpainted_image = cv2.inpaint(jpg, mask, inpaintRadius=3, flags=cv2.INPAINT_TELEA)

                            # Merge signature
                            inpainted_pil = Image.fromarray(inpainted_image)
                            inpainted_pil.paste(esign, (left, top), esign)

                            final_result.append(inpainted_pil)

                        st.subheader("Final Image Preview")
                        st.image(final_result[0], caption="Edited Page", use_column_width=True)

                        images_to_pdf(final_result, "output.pdf")
