# OMR Detection

This project is OMR (Optical Mark Recognition) system built using Flask and OpenCV. It allows users to upload OMR sheet images and automatically extracts marked answers. The extracted results are displayed on the interface and saved in JSON format for further use.

## Features
- Upload single or multiple OMR sheet images
- Bulk upload using folder selection
- Extract answers (1-A, 2-C, etc.)
- Image preprocessing and perspective correction
- JSON output for each uploaded file
- Detect filled bubbles
- Identify empty questions (no bubble marked)
- Detect multiple marked bubbles in a question


## Tech Stack
- Python
- Flask
- OpenCV
- NumPy


## Output Video
You can watch the working demo of the project her.

Google Drive Video Link : https://drive.google.com/file/d/1yRrX6nyzG4F2f1TJRni3cgrjznJnk6WK/view?usp=sharing


## Run Locally

```bash
pip install -r requirements.txt
python app.py

Open in browser: http://127.0.0.1:5000
