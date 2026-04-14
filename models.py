from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class OMRSheet(db.Model):
    __tablename__ = 'omr_sheet'

    id = db.Column(db.Integer, primary_key=True)

    original_file_name = db.Column(db.String(200))       # original uploaded file
    result_file = db.Column(db.String(200))      # file + roll (unique name)

    roll_number = db.Column(db.String(50))

    total_questions = db.Column(db.Integer, default=0)

    correct_answers = db.Column(db.Integer, default=0)
    wrong_answers = db.Column(db.Integer, default=0)

    percentage = db.Column(db.Float, default=0)

    uploaded_time = db.Column(db.DateTime, default=db.func.current_timestamp())

    answers = db.relationship('OMRAnswer', backref='sheet', cascade="all, delete")


class OMRAnswer(db.Model):
    __tablename__ = 'omr_answer'

    id = db.Column(db.Integer, primary_key=True)

    question_no = db.Column(db.String(10))
    selected_option = db.Column(db.String(10))
    is_correct = db.Column(db.Boolean)

    sheet_id = db.Column(
        db.Integer,
        db.ForeignKey('omr_sheet.id'),
        nullable=False
    )


class AnswerKey(db.Model):
    __tablename__ = 'answer_key'

    id = db.Column(db.Integer, primary_key=True)

    question_no = db.Column(db.String(10)) 
    correct_option = db.Column(db.String(5))