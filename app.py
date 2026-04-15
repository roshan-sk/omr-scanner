import os
import cv2
from flask import (
    Flask,
    render_template,
    request,
    send_from_directory,
    send_file,
    session,
    redirect,
    url_for,
    flash
)

from omr_detect import (
    preprocess_and_warp,
    split_into_columns,
    manual_crop_column,
    process_column,
    crop_answer_area,
    crop_rollno_area,
    split_rollno_columns,
    detect_rows_in_roll_column,
    crop_booklet_area,
    split_booklet_columns,
    detect_booklet_digit,
    crop_lang_code1,
    crop_lang_code2,
    process_lang_code
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

    existing_keys = {
        ak.question_no: ak.correct_option
        for ak in AnswerKey.query.all()
    }

    total_questions = max(150, len(existing_keys))

    if request.method == "POST":
        files = request.files.getlist("files")
        results = {}
        latest_sheet_ids = []

        answer_key = existing_keys

        for file in files:
            if file.filename == "":
                continue

            try:
                original_name = os.path.basename(file.filename)
                temp_path = os.path.join(UPLOAD_FOLDER, "temp_" + original_name)
                file.save(temp_path)
                
                img = cv2.imread(temp_path)

                if img is None:
                    raise Exception("Image not readable")
                
                warped_full = preprocess_and_warp(img)

                roll_area = crop_rollno_area(warped_full)
                roll_columns = split_rollno_columns(roll_area, num_digits=8)

                booklet_area = crop_booklet_area(warped_full)
                booklet_columns = split_booklet_columns(booklet_area, num_digits=7)

                lang1_img = crop_lang_code1(warped_full)
                lang2_img = crop_lang_code2(warped_full)

                lang_code_1 = process_lang_code(lang1_img)
                lang_code_2 = process_lang_code(lang2_img)

                roll_number = []

                for i, col in enumerate(roll_columns):
                    thresh, rows, digit = detect_rows_in_roll_column(col, i)

                    if digit == -1:
                        roll_number.append("X")
                    elif digit == -2:
                        roll_number.append("M")
                    else:
                        roll_number.append(str(digit))

                roll_number_str = "".join(roll_number)

                booklet_number = []

                for col in booklet_columns:
                    digit = detect_booklet_digit(col)

                    if digit == -1:
                        booklet_number.append("X")
                    elif digit == -2:
                        booklet_number.append("M")
                    else:
                        booklet_number.append(str(digit))

                booklet_number_str = "".join(booklet_number)

                valid_langs = ["M", "N", "O", "P"]
                lang_code_1 = lang_code_1 if lang_code_1 in valid_langs else None
                lang_code_2 = lang_code_2 if lang_code_2 in valid_langs else None

                name, ext = os.path.splitext(original_name)

                new_filename = f"{roll_number_str}_{name}{ext}"
                new_path = os.path.join(UPLOAD_FOLDER, new_filename)

                if os.path.exists(new_path):
                    os.remove(new_path)

                os.rename(temp_path, new_path)

                path = new_path
                filename = new_filename

                cropped = crop_answer_area(img)
                warped = preprocess_and_warp(cropped)
                columns = split_into_columns(warped)

                all_answers = []

                for i, col in enumerate(columns):
                    cleaned = manual_crop_column(col)
                    answers = process_column(cleaned, i + 1)
                    all_answers.extend(answers)

                existing_sheet = OMRSheet.query.filter_by(roll_number=roll_number_str).first()

                if existing_sheet:
                    existing_sheet.result_file = filename
                    OMRAnswer.query.filter_by(sheet_id=existing_sheet.id).delete()
                    sheet = existing_sheet
                else:
                    sheet = OMRSheet(result_file=filename)
                    db.session.add(sheet)
                    db.session.flush()

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

                correct_answers = sum(1 for a in final_answers if a["is_correct"])
                wrong_answers = len(final_answers) - correct_answers
                total_filled = len(final_answers)
                percentage = (correct_answers / len(final_answers)) * 100 if total_filled else 0

                sheet.original_file_name = original_name
                sheet.roll_number = roll_number_str
                sheet.booklet_number = booklet_number_str
                sheet.language_code_1 = lang_code_1
                sheet.language_code_2 = lang_code_2
                sheet.total_questions = len(final_answers)
                sheet.correct_answers = correct_answers
                sheet.wrong_answers = wrong_answers
                sheet.percentage = percentage

                db.session.commit()
                results[filename] = {
                    "answers": final_answers,
                    "correct": correct_answers,
                    "wrong": wrong_answers,
                    "percentage": round(percentage, 2),
                    "roll_number": roll_number_str,
                    "booklet_number": booklet_number_str,
                }
                latest_sheet_ids.append(sheet.id)

            except Exception as e:
                results[filename] = f"Error: {str(e)}"

        session["latest_sheet_ids"] = latest_sheet_ids

    return render_template(
        "index.html",
        results=results,
        total_questions=total_questions,
        existing_keys=existing_keys
    )


@app.route("/save_answer_key", methods=["POST"])
def save_answer_key():
    total = int(request.form.get("total_questions", 150))

    for i in range(1, total + 1):
        ans = request.form.get(f"q{i}")

        if ans:
            q_no = f"Q{str(i).zfill(3)}"
            ans = ans.strip().upper()

            existing = AnswerKey.query.filter_by(question_no=q_no).first()

            if existing:
                existing.correct_option = ans
            else:
                db.session.add(
                    AnswerKey(
                        question_no=q_no,
                        correct_option=ans
                    )
                )

    db.session.commit()
    flash("Answer Key Updated Successfully!", "success")
    return redirect(url_for("index"))




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

@app.route("/api/answer_key", methods=["POST"])
def api_answer_key():
    data = request.get_json()

    if not data:
        return {"error": "Invalid JSON"}, 400

    # Clear existing keys
    AnswerKey.query.delete()

    for q_no, ans in data.items():
        db.session.add(
            AnswerKey(
                question_no=q_no.upper(),
                correct_option=ans.upper()
            )
        )

    db.session.commit()

    return {
        "message": "Answer key saved successfully",
        "total": len(data)
    }, 200

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)