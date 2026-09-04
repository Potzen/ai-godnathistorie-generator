import json
from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user
from extensions import db
from models import Classroom, ClassroomStudent, QuizResult, Story, User

classroom_bp = Blueprint('classroom', __name__)


def _require_teacher():
    if current_user.role != 'teacher':
        return jsonify(error="Kun lærere har adgang til denne funktion."), 403
    return None


@classroom_bp.route('/classroom/', methods=['GET'])
@login_required
def list_classrooms():
    err = _require_teacher()
    if err:
        return err
    classrooms = Classroom.query.filter_by(teacher_id=current_user.id).order_by(Classroom.created_at.desc()).all()

    # Tael medlemmer for alle klasser i én forespoergsel i stedet for én COUNT pr. klasse.
    counts_by_classroom = dict(
        db.session.query(ClassroomStudent.classroom_id, db.func.count(ClassroomStudent.id))
        .filter(ClassroomStudent.classroom_id.in_([c.id for c in classrooms] or [None]))
        .group_by(ClassroomStudent.classroom_id)
        .all()
    ) if classrooms else {}

    result = []
    for c in classrooms:
        member_count = counts_by_classroom.get(c.id, 0)
        result.append({
            'id': c.id,
            'name': c.name,
            'invite_code': c.invite_code,
            'created_at': c.created_at.isoformat(),
            'member_count': member_count,
        })
    return jsonify(classrooms=result)


@classroom_bp.route('/classroom/create', methods=['POST'])
@login_required
def create_classroom():
    err = _require_teacher()
    if err:
        return err
    data = request.get_json(silent=True) or {}
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify(error="Klassenavnet må ikke være tomt."), 400
    invite_code = Classroom.generate_invite_code()
    classroom = Classroom(teacher_id=current_user.id, name=name, invite_code=invite_code)
    db.session.add(classroom)
    db.session.commit()
    current_app.logger.info(f"Lærer {current_user.id} oprettede klasse '{name}' (kode: {invite_code})")
    return jsonify(id=classroom.id, name=classroom.name, invite_code=classroom.invite_code), 201


@classroom_bp.route('/classroom/<int:classroom_id>/students', methods=['GET'])
@login_required
def list_students(classroom_id):
    err = _require_teacher()
    if err:
        return err
    classroom = db.get_or_404(Classroom, classroom_id)
    if classroom.teacher_id != current_user.id:
        return jsonify(error="Ikke din klasse."), 403

    members = classroom.members.all()
    student_ids = [m.student_user_id for m in members]

    if not student_ids:
        return jsonify(classroom_id=classroom_id, classroom_name=classroom.name, students=[])

    # Hent kun de kolonner vi bruger. Story.content er et stort tekstfelt, og
    # en klasse med mange elever ville ellers traekke hele historieteksten med
    # hjem, alene for at lave en LIX-graf.
    all_stories = db.session.query(
        Story.user_id, Story.created_at, Story.lix_score_stored
    ).filter(
        Story.user_id.in_(student_ids),
        Story.lix_score_stored.isnot(None)
    ).order_by(Story.created_at).all()

    all_quiz = db.session.query(
        QuizResult.user_id, QuizResult.score, QuizResult.total_questions
    ).filter(QuizResult.user_id.in_(student_ids)).all()

    # Slaa alle elevnavne op i én forespoergsel i stedet for én pr. elev.
    names_by_id = dict(
        db.session.query(User.id, User.name).filter(User.id.in_(student_ids)).all()
    )

    stories_by_student = {}
    for s in all_stories:
        stories_by_student.setdefault(s.user_id, []).append({
            'date': s.created_at.date().isoformat(),
            'lix': s.lix_score_stored,
        })

    quiz_by_student = {}
    for q in all_quiz:
        if q.total_questions:
            quiz_by_student.setdefault(q.user_id, []).append(q.score / q.total_questions)

    result = []
    for member in members:
        uid = member.student_user_id
        lix_series = stories_by_student.get(uid, [])
        quiz_scores = quiz_by_student.get(uid, [])
        avg_quiz = round(sum(quiz_scores) / len(quiz_scores) * 100) if quiz_scores else None
        latest_lix = lix_series[-1]['lix'] if lix_series else None
        prev_lix = lix_series[-2]['lix'] if len(lix_series) >= 2 else None
        if latest_lix and prev_lix:
            trend = 'up' if latest_lix > prev_lix else ('down' if latest_lix < prev_lix else 'same')
        else:
            trend = None
        result.append({
            'user_id': uid,
            'name': names_by_id.get(uid) or 'Ukendt',
            'latest_lix': latest_lix,
            'lix_trend': trend,
            'lix_series': lix_series,
            'avg_quiz_pct': avg_quiz,
            'story_count': len(lix_series),
            'joined_at': member.joined_at.isoformat(),
        })
    return jsonify(classroom_id=classroom_id, classroom_name=classroom.name, students=result)


@classroom_bp.route('/classroom/join', methods=['POST'])
@login_required
def join_classroom():
    data = request.get_json(silent=True) or {}
    code = (data.get('invite_code') or '').strip().upper()
    if not code:
        return jsonify(error="Invitationskode mangler."), 400
    classroom = Classroom.query.filter_by(invite_code=code).first()
    if not classroom:
        return jsonify(error="Ukendt invitationskode."), 404
    existing = ClassroomStudent.query.filter_by(
        classroom_id=classroom.id, student_user_id=current_user.id
    ).first()
    if existing:
        return jsonify(error="Du er allerede tilmeldt denne klasse."), 409
    membership = ClassroomStudent(classroom_id=classroom.id, student_user_id=current_user.id)
    db.session.add(membership)
    db.session.commit()
    current_app.logger.info(f"Elev {current_user.id} tilmeldte sig klasse {classroom.id} ('{classroom.name}')")
    return jsonify(message=f"Du er nu tilmeldt '{classroom.name}'.", classroom_id=classroom.id), 201


@classroom_bp.route('/classroom/leave/<int:classroom_id>', methods=['POST'])
@login_required
def leave_classroom(classroom_id):
    membership = ClassroomStudent.query.filter_by(
        classroom_id=classroom_id, student_user_id=current_user.id
    ).first()
    if not membership:
        return jsonify(error="Du er ikke tilmeldt denne klasse."), 404
    db.session.delete(membership)
    db.session.commit()
    return jsonify(message="Du har forladt klassen.")


@classroom_bp.route('/classroom/quiz_result', methods=['POST'])
@login_required
def save_quiz_result():
    data = request.get_json(silent=True) or {}
    score = data.get('score')
    total = data.get('total_questions', 4)
    story_id = data.get('story_id')
    answers = data.get('answers')
    if score is None:
        return jsonify(error="'score' er påkrævet."), 400
    result = QuizResult(
        user_id=current_user.id,
        story_id=story_id,
        score=int(score),
        total_questions=int(total),
        answers_json=json.dumps(answers) if answers is not None else None,
    )
    db.session.add(result)
    db.session.commit()
    current_app.logger.info(f"QuizResult gemt: bruger {current_user.id}, score {score}/{total}")
    return jsonify(id=result.id, message="Quizresultat gemt."), 201
