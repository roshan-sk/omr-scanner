from flask import Flask, render_template, request
import os
import json

from omr_detect import preprocess_and_warp, split_into_columns, manual_crop_column, process_column
from flask import send_from_directory

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "output_jsons"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

options = ['A', 'B', 'C', 'D']

@app.route("/", methods=["GET", "POST"])
def index():
    results = None

    if request.method == "POST":
        files = request.files.getlist("files")
        folder_files = request.files.getlist("folder")

        all_inputs = files + folder_files
        results = {}

        for file in all_inputs:
            if file.filename == "":
                continue

            filename = os.path.basename(file.filename)

            input_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(input_path)

            try:
                warped = preprocess_and_warp(input_path)
                columns = split_into_columns(warped)

                all_answers = []

                for i, col in enumerate(columns):
                    cleaned_col = manual_crop_column(col)
                    answers = process_column(cleaned_col, i+1)
                    all_answers.extend(answers)

                final_answers = [f"{i+1}-{options[a]}" for i, a in enumerate(all_answers)]

                output_file = os.path.join(OUTPUT_FOLDER, filename + ".json")
                with open(output_file, "w") as f:
                    json.dump(final_answers, f, indent=4)

                results[filename] = final_answers

            except Exception as e:
                results[filename] = f"Error: {str(e)}"

    return render_template("index.html", results=results)


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory('input', filename)


if __name__ == "__main__":
    app.run(debug=True)