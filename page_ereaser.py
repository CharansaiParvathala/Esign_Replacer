import streamlit as st
import numpy as np
import cv2
from PIL import Image, ImageDraw
from streamlit_image_coordinates import streamlit_image_coordinates
import fitz
import io
from esign_extractor import get_esign

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
    images = pdf_to_images(uploaded_file.read())
    if images:
        jpg_images = [np.array(img.convert("RGB")) for img in images]
        image_pil = images[0]

        img_width, img_height = image_pil.size

        if "rectangles" not in st.session_state:
            st.session_state["rectangles"] = []
        if "temp_point" not in st.session_state:
            st.session_state["temp_point"] = None

        def draw_rectangles(image, rectangles):
            draw = ImageDraw.Draw(image)
            for rect in rectangles:
                draw.rectangle(rect, outline="red", width=2)
            return image

        img_with_rectangles = draw_rectangles(image_pil.copy(), st.session_state["rectangles"])

        value = streamlit_image_coordinates(
            img_with_rectangles,
            key="pil",
            width=img_width,
            height=img_height,
        )

        if value is not None:
            point = (value["x"], value["y"])

            if st.session_state["temp_point"] is None:
                # Store first point
                st.session_state["temp_point"] = point
            else:
                # Second point defines opposite corner of rectangle
                x1, y1 = st.session_state["temp_point"]
                x2, y2 = point

                # Ensure the rectangle has positive width and height
                if x1 != x2 and y1 != y2:
                    rect = [(min(x1, x2), min(y1, y2)), (max(x1, x2), max(y1, y2))]
                    st.session_state["rectangles"].append(rect)
                    st.session_state["temp_point"] = None
                else:
                    st.warning("Please select two different points for the rectangle.")

        # Inpainting and signature replacement logic
        if st.session_state["rectangles"]:
            # Extract e-signature
            esign = get_esign()

            if esign is not None:
                # Loop over rectangles and replace them with e-signature
                for idx, jpg in enumerate(jpg_images):
                    for rect in st.session_state["rectangles"]:
                        left, top = rect[0]
                        right, bottom = rect[1]
                        width, height = right - left, bottom - top

                        # Ensure width and height are positive
                        if width > 0 and height > 0:
                            esign_resized = esign.resize((width, height))

                            # Create mask for inpainting
                            mask = np.zeros(jpg.shape[:2], dtype=np.uint8)
                            mask[top:bottom, left:right] = 255

                            inpainted_image = cv2.inpaint(jpg, mask, inpaintRadius=3, flags=cv2.INPAINT_TELEA)

                            # Paste signature on the inpainted image
                            inpainted_pil = Image.fromarray(inpainted_image)
                            inpainted_pil.paste(esign_resized, (left, top), esign_resized)
                            final_result.append(inpainted_pil)

                # Check if final_result has images before showing them
                if final_result:
                    st.subheader("Final Image Preview")
                    st.image(final_result[0], caption="Edited Page", use_column_width=True)

                    images_to_pdf(final_result, "output.pdf")
                else:
                    st.error("No images to save in the final result.")
            else:
                st.info("Upload e-signature.")
