import os
import cv2
from flask import (
    Flask,
    render_template,
    request,
    send_from_directory,
    send_file,
    session
)

from omr_detect import (
    preprocess_and_warp,
    split_into_columns,
    manual_crop_column,
    process_column,
    crop_answer_area
)

from models import db, OMRSheet, OMRAnswer, AnswerKey
from helpers import build_excel

app = Flask(__name__)
app.secret_key = "omr-secret-key"


app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///omr.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

options = ["A", "B", "C", "D"]


@app.route("/", methods=["GET", "POST"])
def index():
    results = None
    total_questions = max(150, AnswerKey.query.count())

    if request.method == "POST":
        files = request.files.getlist("files")
        results = {}
        latest_sheet_ids = []
        answer_keys= AnswerKey.query.all()

        answer_key = {
            ak.question_no: ak.correct_option
            for ak in answer_keys
        }

        for file in files:
            if file.filename == "":
                continue

            filename = os.path.basename(file.filename)
            path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(path)

            try:
                img = cv2.imread(path)

                if img is None:
                    raise Exception("Image not readable")

                cropped = crop_answer_area(img)
                warped = preprocess_and_warp(cropped)
                columns = split_into_columns(warped)

                all_answers = []

                for i, col in enumerate(columns):
                    cleaned = manual_crop_column(col)
                    answers = process_column(cleaned, i + 1)
                    all_answers.extend(answers)

                sheet = OMRSheet(sheet_name=filename)
                db.session.add(sheet)
                db.session.commit()

                latest_sheet_ids.append(sheet.id)

                final_answers = []

                for i, a in enumerate(all_answers):
                    q_no = f"Q{str(i+1).zfill(3)}"

                    if a == -1:
                        selected = "Empty"
                    elif a == -2:
                        selected = "Multiple"
                    else:
                        selected = options[a]

                    correct = answer_key.get(q_no)
                    is_correct = selected == correct

                    db.session.add(
                        OMRAnswer(
                            question_no=q_no,
                            selected_option=selected,
                            is_correct=is_correct,
                            sheet_id=sheet.id
                        )
                    )

                    final_answers.append({
                        "value": selected,
                        "is_correct": is_correct
                    })

                db.session.commit()
                results[filename] = final_answers

            except Exception as e:
                results[filename] = f"Error: {str(e)}"

        session["latest_sheet_ids"] = latest_sheet_ids

    return render_template(
        "index.html",
        results=results,
        total_questions=total_questions
    )


@app.route("/save_answer_key", methods=["POST"])
def save_answer_key():
    AnswerKey.query.delete()

    total = int(request.form.get("total_questions", 150))

    for i in range(1, total + 1):
        ans = request.form.get(f"q{i}")

        if ans:
            q_no = f"Q{str(i).zfill(3)}"

            db.session.add(
                AnswerKey(
                    question_no=q_no,
                    correct_option=ans.strip().upper()
                )
            )

    db.session.commit()
    return "Answer Key Saved Successfully!"



@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)



@app.route("/export_latest_excel")
def export_latest_excel():
    ids = session.get("latest_sheet_ids", [])

    if not ids:
        return "No Latest Upload Found"

    data = build_excel(sheet_ids=ids, latest_only=True)

    if not data:
        return "No Data Found"

    output, filename = data

    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )



if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)