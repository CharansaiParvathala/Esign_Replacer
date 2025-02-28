from rembg import remove
import streamlit as st
from io import BytesIO
from PIL import Image


def get_esign(msg):
    """Uploads an e-signature image, removes the background, and returns a transparent PIL image."""
    rawsign = st.file_uploader(msg, type=["jpg", "jpeg", "png"])

    if rawsign:
        img_bytes = rawsign.read()
        esign_bytes = remove(img_bytes)
        esign = Image.open(BytesIO(esign_bytes)).convert("RGBA")  #transparency

        st.image(esign, caption="Processed E-Signature", width=200)
        return esign

    return None 
