# Fil: routes/focus_routes.py
"""
Ugens fokus, ordbanken og hjemmelæsningsloggen.

Ugens fokus er den ene ting, der binder Skole og Hjemmelæsning sammen:
læreren sætter ét sæt lyde for klassen, og alle elever - og deres
forældre derhjemme - får tekster med netop dem, hver på sit eget niveau.
"""
from datetime import date, datetime

from flask import Blueprint, current_app, jsonify, request
from flask_login import current_user, login_required

from extensions import db
from models import Classroom, ClassroomStudent, HomeReadingLog, Story, WeeklyFocus
from services import wordbank_service
from services.phonics_service import POSITION_NAVNE, normaliser_fokus

focus_bp = Blueprint('focus', __name__)

GYLDIGE_POSITIONER = set(POSITION_NAVNE)


def _denne_uge():
    """(år, uge) efter ISO-kalenderen, som skoler regner i."""
    i_dag = date.today()
    aar, uge, _ = i_dag.isocalendar()
    return aar, uge


def _som_json(fokus):
    if not fokus:
        return None
    return {
        'id': fokus.id,
        'classroom_id': fokus.classroom_id,
        'aar': fokus.aar,
        'uge': fokus.uge,
        'lyde': normaliser_fokus(fokus.lyde),
        'lyde_raa': fokus.lyde or '',
        'position': fokus.position,
        'position_navn': POSITION_NAVNE.get(fokus.position, ''),
        'fokusord': [o for o in (fokus.fokusord or '').split(',') if o.strip()],
        'besked_hjem': fokus.besked_hjem or '',
    }


def _elevens_klasser(user_id):
    """De klasse-id'er, en elev er tilmeldt."""
    return [m.classroom_id for m in
            ClassroomStudent.query.filter_by(student_user_id=user_id).all()]


# ---------------------------------------------------------------------
# Læreren sætter ugens fokus
# ---------------------------------------------------------------------

@focus_bp.route('/focus/<int:classroom_id>', methods=['GET'])
@login_required
def hent_fokus(classroom_id):
    """Ugens fokus for en klasse. Både lærer og tilmeldte elever må se det."""
    klasse = db.get_or_404(Classroom, classroom_id)
    er_laerer = klasse.teacher_id == current_user.id
    er_elev = classroom_id in _elevens_klasser(current_user.id)
    if not (er_laerer or er_elev):
        return jsonify(error="Du har ikke adgang til denne klasse."), 403

    aar = request.args.get('aar', type=int)
    uge = request.args.get('uge', type=int)
    if aar is None or uge is None:
        aar, uge = _denne_uge()

    fokus = WeeklyFocus.query.filter_by(classroom_id=classroom_id, aar=aar, uge=uge).first()
    return jsonify(fokus=_som_json(fokus), aar=aar, uge=uge)


@focus_bp.route('/focus/<int:classroom_id>', methods=['POST'])
@login_required
def saet_fokus(classroom_id):
    """Opretter eller opdaterer ugens fokus. Kun klassens egen lærer."""
    klasse = db.get_or_404(Classroom, classroom_id)
    if current_user.role != 'teacher' or klasse.teacher_id != current_user.id:
        return jsonify(error="Kun klassens lærer kan sætte ugens fokus."), 403

    data = request.get_json(silent=True) or {}
    aar = data.get('aar')
    uge = data.get('uge')
    if aar is None or uge is None:
        aar, uge = _denne_uge()
    try:
        aar, uge = int(aar), int(uge)
    except (TypeError, ValueError):
        return jsonify(error="Ugyldigt år eller uge."), 400
    if not 1 <= uge <= 53:
        return jsonify(error="Ugenummer skal være mellem 1 og 53."), 400

    position = (data.get('position') or 'forlyd').strip()
    if position not in GYLDIGE_POSITIONER:
        return jsonify(error=f"Ukendt position. Vælg mellem: {', '.join(sorted(GYLDIGE_POSITIONER))}."), 400

    lyde_raa = (data.get('lyde') or '').strip()
    lyde = normaliser_fokus(lyde_raa)
    fokusord = [o.strip() for o in (data.get('fokusord') or []) if str(o).strip()]

    if not lyde and not fokusord:
        return jsonify(error="Angiv mindst én lyd eller ét fokusord."), 400

    fokus = WeeklyFocus.query.filter_by(classroom_id=classroom_id, aar=aar, uge=uge).first()
    if fokus is None:
        fokus = WeeklyFocus(classroom_id=classroom_id, aar=aar, uge=uge)
        db.session.add(fokus)

    fokus.lyde = ' '.join(lyde)
    fokus.position = position
    fokus.fokusord = ', '.join(fokusord) if fokusord else None
    fokus.besked_hjem = (data.get('besked_hjem') or '').strip()[:300] or None

    db.session.commit()
    current_app.logger.info(
        f"Lærer {current_user.id} satte fokus for klasse {classroom_id}, uge {aar}-{uge}: {fokus.lyde}")
    return jsonify(fokus=_som_json(fokus)), 200


@focus_bp.route('/focus/mit', methods=['GET'])
@login_required
def mit_fokus():
    """Elevens eget ugefokus, samlet fra de klasser vedkommende er i.

    Bruges af både Læsehesten og Hjemmelæsning: barnet skal ikke vide,
    hvilken klasse fokusset kommer fra - kun hvad der øves i denne uge.
    """
    aar, uge = _denne_uge()
    klasser = _elevens_klasser(current_user.id)
    if not klasser:
        return jsonify(fokus=None, aar=aar, uge=uge)

    fokus = (WeeklyFocus.query
             .filter(WeeklyFocus.classroom_id.in_(klasser),
                     WeeklyFocus.aar == aar, WeeklyFocus.uge == uge)
             .order_by(WeeklyFocus.id.desc()).first())
    return jsonify(fokus=_som_json(fokus), aar=aar, uge=uge)


# ---------------------------------------------------------------------
# Ordbanken
# ---------------------------------------------------------------------

@focus_bp.route('/ordbank/mit', methods=['GET'])
@login_required
def min_ordbank():
    """Overblik over de ord, brugeren har mødt."""
    return jsonify(
        statistik=wordbank_service.statistik(current_user.id),
        vaklende=wordbank_service.vaklende_ord(current_user.id),
    )


# ---------------------------------------------------------------------
# Hjemmelæsning
# ---------------------------------------------------------------------

@focus_bp.route('/hjemmelaesning/log', methods=['POST'])
@login_required
def gem_hjemmelaesning():
    """Kvittering for læsning derhjemme. Ét tryk, ikke et skema."""
    data = request.get_json(silent=True) or {}

    dato_tekst = (data.get('dato') or '').strip()
    try:
        dag = datetime.fromisoformat(dato_tekst).date() if dato_tekst else date.today()
    except ValueError:
        return jsonify(error="Ugyldig dato."), 400

    minutter = data.get('minutter')
    if minutter is not None:
        try:
            minutter = int(minutter)
        except (TypeError, ValueError):
            return jsonify(error="'minutter' skal være et tal."), 400
        if not 0 < minutter <= 600:
            return jsonify(error="Antal minutter virker ikke rigtigt."), 400

    laest_af = (data.get('laest_af') or '').strip().lower() or None
    if laest_af and laest_af not in ('barn', 'sammen', 'voksen'):
        return jsonify(error="'laest_af' skal være barn, sammen eller voksen."), 400

    story_id = data.get('story_id')
    if story_id is not None:
        historie = db.session.get(Story, story_id)
        if historie is None or historie.user_id != current_user.id:
            return jsonify(error="Ukendt historie."), 404

    post = HomeReadingLog(
        user_id=current_user.id,
        story_id=story_id,
        dato=dag,
        minutter=minutter,
        laest_af=laest_af,
        kommentar=(data.get('kommentar') or '').strip()[:300] or None,
    )
    db.session.add(post)
    db.session.commit()
    return jsonify(id=post.id, message="Tak - det er noteret."), 201


@focus_bp.route('/hjemmelaesning/log', methods=['GET'])
@login_required
def hent_hjemmelaesning():
    """De seneste kvitteringer, nyeste først."""
    poster = (HomeReadingLog.query
              .filter_by(user_id=current_user.id)
              .order_by(HomeReadingLog.dato.desc(), HomeReadingLog.id.desc())
              .limit(60).all())
    return jsonify(log=[{
        'id': p.id,
        'dato': p.dato.isoformat(),
        'minutter': p.minutter,
        'laest_af': p.laest_af,
        'kommentar': p.kommentar,
        'story_id': p.story_id,
    } for p in poster])
