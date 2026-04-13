# OMR Detection

This project is OMR (Optical Mark Recognition) system built using Flask and OpenCV. It allows users to upload OMR sheet images and automatically extracts marked answers. The extracted results are displayed on the interface and, the system processes the sheets, evaluates results using a database answer key, and displays the final score on the interface.

## Features
- Upload single or multiple OMR sheet images
- Bulk upload using folder selection
- Extract answers (1-A, 2-C, etc.)
- Image preprocessing and perspective correction
- JSON output for each uploaded file
- Detect filled bubbles
- Identify empty questions (no bubble marked)
- Detect multiple marked bubbles in a question
- Store results in database
- Compare answers with database answer key
- Calculate score automatically
- Export OMR results to Excel


## Tech Stack
- Python
- Flask
- OpenCV
- NumPy
- SQLite (Database)

## Output Features
- Extracted answers displayed in UI
- Results stored in database
- Score calculation based on correct answers
- Export results to Excel format


## Output Video
You can watch the working demo of the project her.

Google Drive Video Link : https://drive.google.com/file/d/1yRrX6nyzG4F2f1TJRni3cgrjznJnk6WK/view?usp=sharing


## Run Locally

```bash
pip install -r requirements.txt
python app.py

Open in browser: http://127.0.0.1:5000
