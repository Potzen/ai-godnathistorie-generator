# Fil: routes/narrative_routes.py
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from models import Story
from extensions import db
from sqlalchemy import or_
from services.ai_service import (
    get_ai_suggested_character_traits,
    generate_narrative_brief,
    draft_narrative_story_with_rag,
    edit_narrative_story,
    generate_reflection_questions_step4,
    analyze_story_for_logbook
)
import traceback


narrative_bp = Blueprint('narrative', __name__, url_prefix='/narrative')


@narrative_bp.route('/generate_narrative_story', methods=['POST'])
@login_required
def generate_narrative_story():
    if current_user.role != 'premium':
        return jsonify({"error": "Adgang nægtet. Denne funktion kræver et premium abonnement."}), 403

    original_user_inputs = request.get_json()
    if not original_user_inputs:
        return jsonify({"error": "Ingen JSON data modtaget"}), 400

    user_id_for_log = current_user.id
    current_app.logger.info(f"Narrative Route (Bruger: {user_id_for_log}): Modtaget anmodning om historiegenerering.")

    # NYT: Hent data for fortsættelse
    parent_story_id = original_user_inputs.get('parent_story_id')
    continuation_strategy = original_user_inputs.get('continuation_strategy')
    continuation_context = None

    if parent_story_id and continuation_strategy:
        current_app.logger.info(
            f"Dette er en fortsættelse af historie ID {parent_story_id} med strategi '{continuation_strategy}'.")
        parent_story = Story.query.get(parent_story_id)
        if parent_story and parent_story.user_id == current_user.id:
            continuation_context = {
                'strategy': continuation_strategy,
                'problem_name': parent_story.problem_name,
                'discovered_method_name': parent_story.discovered_method_name
                # Vi kan tilføje flere felter her senere om nødvendigt
            }
        else:
            current_app.logger.warning(
                f"Bruger {user_id_for_log} forsøgte at fortsætte en ugyldig eller uautoriseret historie (ID: {parent_story_id}).")
            # Ignorer fortsættelsen, men generer stadig en normal historie for at undgå fejl i frontend
            parent_story_id = None

    try:
        # VI SKAL OPDATERE DISSE KALD SENERE TIL AT BRUGE 'continuation_context'
        # For nu lader vi dem være, så appen ikke crasher.
        # Send nu den nye kontekst med i kaldene
        narrative_brief = generate_narrative_brief(original_user_inputs)
        story_title_from_draft, story_content_from_draft = draft_narrative_story_with_rag(
            structured_brief=narrative_brief,
            original_user_inputs=original_user_inputs,
            narrative_focus_for_rag=original_user_inputs.get('narrative_focus'),
            continuation_context=continuation_context  # <--- VIGTIG TILFØJELSE
        )
        final_story_title, final_story_content = edit_narrative_story(
            story_draft_title=story_title_from_draft,
            story_draft_content=story_content_from_draft,
            original_user_inputs=original_user_inputs
        )

        # Gem den nye historie
        new_story = Story(
            title=final_story_title,
            content=final_story_content,
            user_id=current_user.id,
            source='Narrativ Støtte',
            is_log_entry=False
        )

        # NYT: Sæt parent_id og series_part, hvis det er en fortsættelse
        if parent_story_id and parent_story:
            new_story.parent_story_id = parent_story_id
            new_story.series_part = parent_story.series_part + 1

        db.session.add(new_story)
        db.session.commit()
        current_app.logger.info(
            f"Bruger {user_id_for_log}: Ny historie (ID: {new_story.id}) gemt. Parent ID: {new_story.parent_story_id}.")

        return jsonify({
            "status": "Historie genereret og gemt succesfuldt.",
            "story_id": new_story.id,
            "title": new_story.title,
            "story": new_story.content,
            "narrative_brief_for_reference": narrative_brief
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Bruger {user_id_for_log}: Uventet fejl i /generate_narrative_story: {e}\n{traceback.format_exc()}")
        return jsonify({"error": "En uventet serverfejl opstod."}), 500

@narrative_bp.route('/get_guiding_questions', methods=['POST'])
@login_required
def get_guiding_questions():
    if current_user.role != 'premium':
        current_app.logger.warning(
            f"Uautoriseret forsøg på adgang til '/get_guiding_questions' af bruger: "
            f"{current_user.email} (Rolle: {current_user.role})"
        )
        return jsonify({"error": "Adgang nægtet. Denne funktion kræver et premium abonnement."}), 403

    user_id_for_log = current_user.id
    current_app.logger.info(
        f"Narrative Route (Bruger: {user_id_for_log}, E-mail: {current_user.email}): Modtaget anmodning til /get_guiding_questions."
    )

    if not request.is_json:
        current_app.logger.error(f"Bruger {user_id_for_log}: Anmodning til /get_guiding_questions er ikke JSON.")
        return jsonify({"error": "Anmodning skal være JSON."}), 415

    data = request.get_json()
    current_app.logger.debug(f"Bruger {user_id_for_log}: Modtaget data for /get_guiding_questions: {str(data)[:500]}...") # Log kun starten af data

    final_story_title = data.get('final_story_title')
    final_story_content = data.get('final_story_content')
    narrative_brief = data.get('narrative_brief')
    original_user_inputs = data.get('original_user_inputs') # Bruges til barnets alder etc.

    if not all([final_story_title, final_story_content, narrative_brief, original_user_inputs]):
        missing_fields = [
            field for field, value in {
                "final_story_title": final_story_title,
                "final_story_content": final_story_content,
                "narrative_brief": narrative_brief,
                "original_user_inputs": original_user_inputs
            }.items() if not value
        ]
        current_app.logger.error(
            f"Bruger {user_id_for_log}: Manglende felter i anmodning til /get_guiding_questions: {', '.join(missing_fields)}"
        )
        return jsonify({"error": f"Manglende nødvendige felter i anmodningen: {', '.join(missing_fields)}"}), 400

    try:
        current_app.logger.info(f"Bruger {user_id_for_log}: Kalder ai_service for at generere refleksionsspørgsmål (Trin 4)...")
        questions = generate_reflection_questions_step4(
            final_story_title=final_story_title,
            final_story_content=final_story_content,
            narrative_brief=narrative_brief,
            original_user_inputs=original_user_inputs
        )

        if questions: # Hvis listen ikke er tom
            current_app.logger.info(f"Bruger {user_id_for_log}: {len(questions)} refleksionsspørgsmål genereret succesfuldt.")
            return jsonify({"reflection_questions": questions}), 200
        else:
            current_app.logger.warning(f"Bruger {user_id_for_log}: Ingen refleksionsspørgsmål genereret af ai_service (Trin 4).")
            return jsonify({"reflection_questions": [], "message": "Ingen specifikke spørgsmål kunne genereres på baggrund af denne historie, eller AI-kaldet returnerede ingen."}), 200

    except Exception as e:
        current_app.logger.error(
            f"Bruger {user_id_for_log}: Uventet fejl i /get_guiding_questions endpoint: {e}\n{traceback.format_exc()}"
        )
        return jsonify({"error": "En uventet intern serverfejl opstod under generering af refleksionsspørgsmål."}), 500


@narrative_bp.route('/suggest_character_traits', methods=['POST'])
@login_required  # Tilføjet/aktiveret
def suggest_character_traits():
    # Tjek om brugeren har 'premium' rolle
    if current_user.role != 'premium':
        current_app.logger.warning(
            f"Uautoriseret forsøg på adgang til '/suggest_character_traits' af bruger: "
            f"{current_user.email} (Rolle: {current_user.role})"
        )
        return jsonify({"error": "Adgang nægtet. Denne funktion kræver et premium abonnement."}), 403  # Forbidden

    user_id_for_log = current_user.id # <--- DENNE LINJE ER TILFØJET/FLYTET KORREKT

    current_app.logger.info(
        f"Narrative route /suggest_character_traits kaldt af bruger: {current_user.email} (ID: {user_id_for_log})") # Nu kan user_id_for_log bruges her

    if not request.is_json:
        current_app.logger.warning(f"Bruger {current_user.email}: Kald til /suggest_character_traits uden JSON data.") # Overvej også at bruge user_id_for_log her for konsistens
        return jsonify({"error": "Anmodning skal være JSON."}), 415

    data = request.get_json()
    # current_app.logger.debug(f"Bruger {current_user.email}: Modtaget rådata for /suggest_character_traits: {data}") # Overvej om denne er nødvendig, da vi logger den næste

    narrative_focus = data.get('narrative_focus')

    if not narrative_focus or not isinstance(narrative_focus, str) or not narrative_focus.strip():
        current_app.logger.warning(
            f"Bruger {current_user.email}: 'narrative_focus' mangler eller er ugyldigt for /suggest_character_traits.")
        return jsonify({"error": "Obligatorisk felt 'narrative_focus' mangler eller er tomt."}), 400

    current_app.logger.info(
        f"Bruger {current_user.email}: narrative_focus for karaktertræk-forslag: '{narrative_focus}'")

    try:
        current_app.logger.info(f"Bruger {user_id_for_log}: Kalder ai_service for at få forslag til karaktertræk.")
        suggested_traits_data = get_ai_suggested_character_traits(narrative_focus)

        if isinstance(suggested_traits_data, dict) and 'error' in suggested_traits_data:
            current_app.logger.error(
                f"Bruger {user_id_for_log}: Fejl fra ai_service (karaktertræk): {suggested_traits_data.get('error')}")
            return jsonify(suggested_traits_data), 500

        current_app.logger.info(
            f"Bruger {user_id_for_log}: Modtaget forslag til karaktertræk fra ai_service (delvis): {str(suggested_traits_data)[:200]}...")
        return jsonify(suggested_traits_data), 200

    except Exception as e:
        current_app.logger.error(
            f"Bruger {user_id_for_log}: Uventet fejl i /suggest_character_traits efter validering: {e}\n{traceback.format_exc()}")
        return jsonify({"error": "En uventet intern serverfejl opstod under forslag til karaktertræk."}), 500


@narrative_bp.route('/analyze-for-logbook', methods=['POST'])
@login_required
def analyze_for_logbook():
    """
    API-endepunkt der modtager en historie og returnerer en AI-genereret
    analyse med henblik på at oprette en logbogs-indtastning.
    """
    if current_user.role != 'premium':
        return jsonify({"error": "Adgang nægtet. Denne funktion kræver et premium abonnement."}), 403

    if not request.is_json:
        return jsonify({"error": "Anmodning skal være JSON."}), 415

    data = request.get_json()
    story_content = data.get('story_content')

    if not story_content:
        return jsonify({"error": "Feltet 'story_content' mangler."}), 400

    try:
        analysis_data = analyze_story_for_logbook(story_content)
        if 'error' in analysis_data:
            # Hvis ai_service selv fangede en fejl, returneres den
            return jsonify(analysis_data), 500

        return jsonify(analysis_data), 200

    except Exception as e:
        current_app.logger.error(f"Route /analyze-for-logbook: Uventet fejl: {e}\n{traceback.format_exc()}")
        return jsonify({"error": "En uventet serverfejl opstod."}), 500

@narrative_bp.route('/save-log-entry/<int:story_id>', methods=['POST'])
@login_required
def save_log_entry(story_id):
    """
    API-endepunkt der modtager de udfyldte data fra dokumentations-formularen
    og gemmer dem på den specifikke historie i databasen.
    """
    if current_user.role != 'premium':
        return jsonify({"error": "Adgang nægtet."}), 403

    # Find den eksisterende historie, der blev oprettet ved generering
    story = Story.query.get_or_404(story_id)

    # Sikkerhedstjek: Sørg for at brugeren ejer historien
    if story.user_id != current_user.id:
        current_app.logger.warning(
            f"Bruger {current_user.id} forsøgte at gemme logbogsdata for en andens historie (ID: {story_id}).")
        return jsonify({"error": "Uautoriseret adgang."}), 403

    data = request.get_json()
    if not data:
        return jsonify({"error": "Ingen data modtaget."}), 400

    current_app.logger.info(f"Modtager logbogsdata for historie {story_id}: {data}")

    try:
        # Opdater Story-objektet med alle data fra formularen
        story.problem_name = data.get('problem_name')
        story.problem_influence = data.get('problem_influence')
        story.unique_outcome = data.get('unique_outcome')
        story.discovered_method_name = data.get('discovered_method_name')
        story.discovered_method_steps = data.get('discovered_method_steps')
        story.child_values = data.get('child_values')
        story.support_system = data.get('support_system')
        story.user_notes = data.get('user_notes')

        # Håndter tal-inputs, der kan være tomme strenge
        progress_before = data.get('progress_before')
        story.progress_before = int(progress_before) if progress_before and progress_before.isdigit() else None

        progress_after = data.get('progress_after')
        story.progress_after = int(progress_after) if progress_after and progress_after.isdigit() else None

        # VIGTIGT: Markér historien som en logbogs-indtastning
        story.is_log_entry = True

        db.session.commit()
        current_app.logger.info(
            f"Historie {story_id} er succesfuldt opdateret og markeret som logbogs-indtastning.")

        return jsonify({"success": True, "message": "Historien er gemt i din logbog."}), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Fejl under gemning af logbogsdata for historie {story_id}: {e}\n{traceback.format_exc()}")
        return jsonify({"error": "En intern fejl opstod under gemning."}), 500


@narrative_bp.route('/api/logbook/filter', methods=['POST'])
@login_required
def filter_logbook():
    """
    API-endepunkt til dynamisk at filtrere og sortere logbogs-historier.
    """
    data = request.get_json()

    source = data.get('source')
    search_term = data.get('searchTerm')
    sort_by = data.get('sortBy')

    # Start med en basisforespørgsel
    query = Story.query.filter_by(user_id=current_user.id, is_log_entry=True)

    # Tilføj filter for kilde
    if source and source != 'all':
        query = query.filter(Story.source == source)

    # Tilføj filter for søgeterm
    if search_term:
        query = query.filter(or_(
            Story.title.ilike(f'%{search_term}%'),
            Story.content.ilike(f'%{search_term}%')
        ))

    # Tilføj sortering
    if sort_by == 'oldest':
        query = query.order_by(Story.created_at.asc())
    elif sort_by == 'title_asc':
        query = query.order_by(Story.title.asc())
    elif sort_by == 'title_desc':
        query = query.order_by(Story.title.desc())
    else:  # Default til nyeste først
        query = query.order_by(Story.created_at.desc())

    filtered_stories = query.all()

    # Konverter historierne til et format, der kan sendes som JSON
    stories_list = []
    for story in filtered_stories:
        stories_list.append({
            'id': story.id,
            'title': story.title,
            'content': story.content,
            'source': story.source,
            'created_at': story.created_at.strftime('%d. %b %Y'),
            'problem_name': story.problem_name,
            'problem_influence': story.problem_influence,
            'unique_outcome': story.unique_outcome,
            'discovered_method_name': story.discovered_method_name,
            'discovered_method_steps': story.discovered_method_steps,
            'child_values': story.child_values,
            'support_system': story.support_system,
            'user_notes': story.user_notes
        })

    return jsonify(stories_list)


@narrative_bp.route('/api/notes/update/<int:story_id>', methods=['POST'])
@login_required
def update_note(story_id):
    """
    API-endepunkt til specifikt at opdatere user_notes for en given historie.
    Dette er en letvægts-operation designet til hurtige 'auto-save' eller 'gem'-kald.
    """
    story = Story.query.get_or_404(story_id)

    # Sikkerhedstjek: Sørg for at brugeren ejer historien
    if story.user_id != current_user.id:
        return jsonify({"error": "Uautoriseret adgang."}), 403

    data = request.get_json()
    if not data or 'notes' not in data:
        return jsonify({"error": "Manglende 'notes' felt i anmodning."}), 400

    try:
        story.user_notes = data['notes']
        db.session.commit()
        current_app.logger.info(f"Noter for historie {story_id} opdateret for bruger {current_user.id}.")
        return jsonify({"success": True, "message": "Noter er gemt."})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Fejl under opdatering af noter for historie {story_id}: {e}")
        return jsonify({"error": "Intern fejl ved gemning af noter."}), 500


@narrative_bp.route('/api/list-stories', methods=['GET'])
@login_required
def list_stories_for_continuation():
    """
    API-endepunkt der returnerer en simpel liste af brugerens gemte
    "Narrativ Støtte"-historier, som kan bruges som forældre-historier.
    """
    if current_user.role != 'premium':
        return jsonify({"error": "Adgang nægtet."}), 403

    try:
        # Find alle historier fra den loggede bruger, som er gemt i logbogen
        # og som stammer fra "Narrativ Støtte".
        continuable_stories = Story.query.filter_by(
            user_id=current_user.id,
            is_log_entry=True,
            source='Narrativ Støtte'
        ).order_by(Story.created_at.desc()).all()

        # Formater outputtet til kun at indeholde id og titel
        stories_data = [{'id': story.id, 'title': story.title} for story in continuable_stories]

        return jsonify(stories_data)

    except Exception as e:
        current_app.logger.error(f"Fejl under hentning af historieliste for bruger {current_user.id}: {e}")
        return jsonify({"error": "Intern fejl ved hentning af historieliste."}), 500