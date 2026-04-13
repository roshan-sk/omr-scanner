from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class OMRSheet(db.Model):
    __tablename__ = 'omr_sheet'

    id = db.Column(db.Integer, primary_key=True)

    sheet_name = db.Column(db.String(200))
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