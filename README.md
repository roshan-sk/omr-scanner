# OMR Detection

This project is OMR (Optical Mark Recognition) system built using Flask and OpenCV. It allows users to upload OMR sheet images and automatically extracts marked answers. The extracted results are displayed on the interface and saved in JSON format for further use.

## Features
- Upload single or multiple OMR sheet images
- Image preprocessing and perspective correction
- Automatic OMR bubble detection using OpenCV
- Extract answers (1-A, 2-C, etc.)
- Extract roll number from OMR sheet
- Auto evaluation with:
  - Correct answers count
  - Wrong answers count
  - Percentage score
-Detects:
  - Empty answers
  - Multiple marked answers
- Stores results in SQLite database
- Export results to Excel
- View uploaded sheet preview in UI 
- JSON output for each uploaded file
- Detect filled bubbles
- Identify empty questions (no bubble marked)
- Detect multiple marked bubbles in a question


## Tech Stack
- Python
- Flask
- OpenCV
- NumPy
- SQLite

## Output Features

Each OMR sheet generates:
- Roll Number
- Total Questions
- Correct Answers
- Wrong Answers
- Percentage Score
- Detailed answer-wise result

## 🧠 System Workflow

1. Upload OMR sheet image
2. Image preprocessing (resize, grayscale, thresholding)
3. Perspective correction
4. Detect:
   - Roll number section
   - Answer bubbles
5. Evaluate answers using stored answer key
6. Store results in database
7. Display results in UI
8. Export to Excel

## Output Video
You can watch the working demo of the project her.

Google Drive Video Link : https://drive.google.com/file/d/1yRrX6nyzG4F2f1TJRni3cgrjznJnk6WK/view?usp=sharing


## Run Locally

```bash
pip install -r requirements.txt
python app.py

Open in browser: http://127.0.0.1:5000
