from flask import Flask, render_template, request, send_from_directory
import os
import json
import cv2

from omr_detect import (
    preprocess_and_warp,
    split_into_columns,
    manual_crop_column,
    process_column,
    crop_answer_area   # ✅ added
)

from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///omr.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "output_jsons"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


class OMRFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200))
    answers = db.relationship('OMRAnswer', backref='file', uselist=False)


class OMRAnswer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    answers_json = db.Column(db.Text)
    file_id = db.Column(db.Integer, db.ForeignKey('omr_file.id'), nullable=False)


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
                # ✅ Read image
                full_img = cv2.imread(input_path)

                # ✅ Crop answer area (NEW)
                cropped_img = crop_answer_area(full_img)

                # ✅ Warp image
                warped = preprocess_and_warp(cropped_img)

                # ✅ Split columns
                columns = split_into_columns(warped)

                all_answers = []

                for i, col in enumerate(columns):
                    cleaned_col = manual_crop_column(col)
                    answers = process_column(cleaned_col, i + 1)
                    all_answers.extend(answers)

                # ✅ Handle Empty & Multiple
                final_answers = []
                for i, a in enumerate(all_answers):
                    if a == -1:
                        final_answers.append(f"{i+1}-Empty")
                    elif a == -2:
                        final_answers.append(f"{i+1}-Multiple")
                    else:
                        final_answers.append(f"{i+1}-{options[a]}")

                # ✅ Save to DB
                omr_file = OMRFile(filename=filename)
                db.session.add(omr_file)
                db.session.commit()

                omr_answer = OMRAnswer(
                    answers_json=json.dumps(final_answers),
                    file_id=omr_file.id
                )

                db.session.add(omr_answer)
                db.session.commit()

                # ✅ Save JSON file
                output_file = os.path.join(OUTPUT_FOLDER, filename + ".json")
                with open(output_file, "w") as f:
                    json.dump(final_answers, f, indent=4)

                results[filename] = final_answers

            except Exception as e:
                results[filename] = f"Error: {str(e)}"

    return render_template("index.html", results=results)


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)