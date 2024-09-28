from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse
from schemas import ImageUploadResponse, ErrorResponse, ImageUpload
import tensorflow as tf
import numpy as np
import os
from PIL import Image
from io import BytesIO
import torch
import utils
import exp
from torchvision import transforms
from captum.attr import *
import matplotlib.pyplot as plt
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Allowing CORS for the frontend URL
origins = ["https://healthcare-app-nine.vercel.app"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helper function to ensure valid file extension
def allowed_file_extension(filename: str):
    allowed_extensions = {"png", "jpg", "jpeg", "bmp"}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

@app.post("/upload")
async def upload_file(file: UploadFile = Form(None), email: str = Form(None)):
    if not file:
        raise HTTPException(status_code=400, detail="No file provided.")
    if not allowed_file_extension(file.filename):
        raise HTTPException(status_code=400, detail="Invalid file format. Supported formats: png, jpg, jpeg, bmp.")

    contents = await file.read()

    try:
        image = Image.open(BytesIO(contents)).convert('RGB')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing image: {str(e)}")

    user = email.split('@')[0]
    print(f"User: {user}")

    try:
        class_name, confidence = utils.predict(image, user)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

    # Save the uploaded image for future use
    image.save(f"{user}.png")

    return {"class": class_name, "confidence": confidence}


@app.post("/explanation")
async def explanation_file(email: str = Form(...)):
    user = email.split('@')[0]
    image_path = f"{user}.png"

    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="No image has been uploaded yet.")

    try:
        # Load the saved image
        with open(image_path, "rb") as img_file:
            image = Image.open(img_file)
            stored_image = image.copy()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading image: {str(e)}")

    try:
        # Generate explanation using the stored image
        explanation = exp.explanation(stored_image)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Explanation error: {str(e)}")

    return {"explanation": explanation}

