from rembg import remove
import streamlit as st
from io import BytesIO
from PIL import Image

def get_esign():
    rawsign = st.file_uploader('Signature Image', type=["jpg", "jpeg", "png"])
    if rawsign:
        img_bytes = rawsign.read()
        esign_bytes = remove(img_bytes)
        esign = Image.open(BytesIO(esign_bytes))
        return esign
