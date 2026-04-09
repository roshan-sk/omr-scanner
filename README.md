# OMR Detection

This project is OMR (Optical Mark Recognition) system built using Flask and OpenCV. It allows users to upload OMR sheet images and automatically extracts marked answers. The extracted results are displayed on the interface and saved in JSON format for further use.

## Features
- Upload single or multiple OMR sheet images
- Bulk upload using folder selection
- Extract answers (1-A, 2-C, etc.)
- Image preprocessing and perspective correction
- JSON output for each uploaded file


## Tech Stack
- Python
- Flask
- OpenCV
- NumPy

## Project Structure
project/
│── app.py                # Main Flask application
│── omr_detect.py        # OMR processing logic
│── uploads/             # Uploaded images
│── output_jsons/        # Extracted results (JSON)
│── templates/
│    └── index.html      # Frontend UI

## Output Video
You can watch the working demo of the project here:
Google Drive Link : https://drive.google.com/file/d/1miuxDDyot-OxA_imJgDtFd860WUeDELa/view?usp=drive_link


## Run Locally

```bash
pip install -r requirements.txt
python app.py

Open in browser: http://127.0.0.1:5000
