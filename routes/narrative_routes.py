# Fil: routes/narrative_routes.py
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from services.ai_service import (
    get_ai_suggested_character_traits,
    generate_narrative_brief,
    draft_narrative_story_with_rag,
    edit_narrative_story,
    generate_reflection_questions_step4
)
import traceback

narrative_bp = Blueprint('narrative', __name__, url_prefix='/narrative')


@narrative_bp.route('/generate_narrative_story', methods=['POST'])
@login_required  # Nu aktiv
def generate_narrative_story():
    # Tjek om brugeren har 'premium' rolle
    if current_user.role != 'premium':
        current_app.logger.warning(
            f"Uautoriseret forsøg på adgang til '/generate_narrative_story' af bruger: "
            f"{current_user.email} (Rolle: {current_user.role})"
        )
        return jsonify({"error": "Adgang nægtet. Denne funktion kræver et premium abonnement."}), 403  # Forbidden

    original_user_inputs = request.get_json()
    if not original_user_inputs:
        current_app.logger.error("Narrative Route: Ingen JSON data modtaget.")
        return jsonify({"error": "Ingen JSON data modtaget"}), 400

    # Definer user_id_for_log her, så den er tilgængelig i hele funktionen
    # user_id_for_log defineres allerede nedenfor, så vi behøver ikke ændre den del
    user_id_for_log = current_user.id  # Kan nu bruge current_user.id direkte her, da brugeren er logget ind
    current_app.logger.info(
        f"Narrative Route (Bruger: {user_id_for_log}, E-mail: {current_user.email}): Modtaget data for /generate_narrative_story: {original_user_inputs}")

    # --- TRIN 1: Generer Narrativt Brief ---
    narrative_focus = original_user_inputs.get('narrative_focus')
    if not narrative_focus:
        current_app.logger.error(f"Bruger {user_id_for_log}: Manglende 'narrative_focus' i /generate_narrative_story.")
        return jsonify({"error": "Obligatorisk felt 'narrative_focus' mangler."}), 400

    try:
        current_app.logger.info(f"Bruger {user_id_for_log}: Starter TRIN 1 - Generering af narrativt brief...")
        narrative_brief = generate_narrative_brief(original_user_inputs)

        if isinstance(narrative_brief, str) and narrative_brief.lower().startswith("fejl:"):
            current_app.logger.error(f"Bruger {user_id_for_log} (TRIN 1): Fejl fra generate_narrative_brief: {narrative_brief}")
            return jsonify({"error": narrative_brief, "details": "Fejl under Trin 1 (brief generering)"}), 500

        current_app.logger.info(f"Bruger {user_id_for_log}: TRIN 1 fuldført. Narrativt brief genereret.")
        current_app.logger.debug(f"Narrative Route (Bruger: {user_id_for_log}): Modtaget brief (første 200 tegn): {narrative_brief[:200]}")

        # --- TRIN 2: Udarbejd Historieudkast med RAG ---
        current_app.logger.info(f"Bruger {user_id_for_log}: Starter TRIN 2 - Udarbejdelse af historieudkast med RAG...")
        story_title_from_draft, story_content_from_draft = draft_narrative_story_with_rag(
            # Fjernet reflection_questions her
            structured_brief=narrative_brief,
            original_user_inputs=original_user_inputs,
            narrative_focus_for_rag=narrative_focus
        )

        if isinstance(story_content_from_draft, str) and story_content_from_draft.lower().startswith("fejl:"):
            current_app.logger.error(
                f"Bruger {user_id_for_log} (TRIN 2): Fejl fra draft_narrative_story_with_rag: {story_content_from_draft}")
            return jsonify({"error": story_content_from_draft, "details": "Fejl under Trin 2 (historie udarbejdelse)"}), 500

        if not story_title_from_draft or not story_content_from_draft:  # Korrekt tjek
            current_app.logger.warning(
                f"Bruger {user_id_for_log} (TRIN 2): draft_narrative_story_with_rag returnerede tom titel eller indhold. Titel: '{story_title_from_draft}', Indhold OK: {bool(story_content_from_draft)}")
            return jsonify(
                {"error": "Historieudkast fra Trin 2 var ufuldstændigt.", "title_received": story_title_from_draft,
                 "content_received": bool(story_content_from_draft)}), 500

        current_app.logger.info(  # <--- OPDATERET LINJE
            f"Bruger {user_id_for_log}: TRIN 2 fuldført. Historieudkast '{story_title_from_draft[:50]}...' genereret. (Spørgsmål genereres i Trin 4)")

        # --- TRIN 3: Rediger Historieudkast ---
        current_app.logger.info(f"Bruger {user_id_for_log}: Starter TRIN 3 - Redigering af historieudkast...")
        final_story_title, final_story_content = edit_narrative_story(
            story_draft_title=story_title_from_draft,
            story_draft_content=story_content_from_draft,
            original_user_inputs=original_user_inputs
        )

        if isinstance(final_story_content, str) and final_story_content.lower().startswith("fejl:"):
            current_app.logger.error(
                f"Bruger {user_id_for_log} (TRIN 3): Fejl fra edit_narrative_story: {final_story_content}")
            return jsonify({
                "status": "Trin 1 & 2 fuldført, men Trin 3 (Redigering) fejlede.",
                "warning": "Historien nedenfor er et uredigeret udkast, da den endelige redigering mislykkedes.",
                "title": story_title_from_draft,
                "story": story_content_from_draft,
                # "reflection_questions": reflection_questions,
                "narrative_brief_for_reference": narrative_brief,
                "error_details_step3": final_story_content
            }), 200

        current_app.logger.info(f"Bruger {user_id_for_log}: TRIN 3 fuldført. Historie redigeret til '{final_story_title[:50]}...'.")

        return jsonify({
            "status": "Alle 3 historiegenereringstrin fuldført. Endelig narrativ historie er klar. Refleksionsspørgsmål hentes separat.",
            "title": final_story_title,
            "story": final_story_content,
            # "reflection_questions": reflection_questions, <-- FJERNET
            "narrative_brief_for_reference": narrative_brief,
            "draft_title_from_step2_for_reference": story_title_from_draft,
            "draft_content_from_step2_for_reference": story_content_from_draft[:200] + "..." if story_content_from_draft else None
        }), 200

    except Exception as e:
        current_app.logger.error(
            f"Bruger {user_id_for_log}: Uventet fejl i /generate_narrative_story endpoint: {e}\n{traceback.format_exc()}")
        return jsonify({"error": "En uventet intern serverfejl opstod under narrativ generering."}), 500

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

# Kommentar: Den gamle step1 generator funktion er fjernet fra imports og brug,
# da den er erstattet af det nye 3-trins flow.