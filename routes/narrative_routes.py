# Fil: routes/narrative_routes.py
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from services.ai_service import generate_narrative_story_step1_generator_ai
from services.ai_service import get_ai_suggested_character_traits, generate_narrative_brief, draft_narrative_story_with_rag


narrative_bp = Blueprint('narrative', __name__, url_prefix='/narrative') # Allerede defineret

@narrative_bp.route('/generate_narrative_story', methods=['POST'])
# @login_required # Stadig udkommenteret for test
def generate_narrative_story():
    original_user_inputs = request.get_json()  # Gem de originale input
    if not original_user_inputs:
        current_app.logger.error("Narrative Route: Ingen JSON data modtaget.")
        return jsonify({"error": "Ingen JSON data modtaget"}), 400

    current_app.logger.info(f"Narrative Route: Modtaget data for /generate_narrative_story: {original_user_inputs}")

    # --- TRIN 1: Generer Narrativt Brief ---
    narrative_focus = original_user_inputs.get('narrative_focus')
    if not narrative_focus:
        current_app.logger.error("Narrative Route: Manglende 'narrative_focus' i anmodning.")
        return jsonify({"error": "Obligatorisk felt 'narrative_focus' mangler."}), 400

    try:
        current_app.logger.info("Narrative Route: Starter TRIN 1 - Generering af narrativt brief...")
        narrative_brief = generate_narrative_brief(
            narrative_focus=narrative_focus,
            story_goal=original_user_inputs.get('story_goal', ''),
            child_name=original_user_inputs.get('child_name', ''),
            child_age=original_user_inputs.get('child_age', ''),
            child_strengths=original_user_inputs.get('child_strengths', []),
            child_values=original_user_inputs.get('child_values', []),
            child_motivation=original_user_inputs.get('child_motivation', ''),
            child_typical_reaction=original_user_inputs.get('child_typical_reaction', ''),
            important_relations=original_user_inputs.get('important_relations', []),
            main_character_description=original_user_inputs.get('main_character_description'),
            story_place=original_user_inputs.get('story_place'),
            story_plot_elements=original_user_inputs.get('story_plot_elements'),
            negative_prompt=original_user_inputs.get('negative_prompt')
        )

        if isinstance(narrative_brief, str) and narrative_brief.lower().startswith("fejl:"):
            current_app.logger.error(f"Narrative Route (TRIN 1): Fejl fra generate_narrative_brief: {narrative_brief}")
            return jsonify({"error": narrative_brief, "details": "Fejl under Trin 1 (brief generering)"}), 500

        current_app.logger.info("Narrative Route: TRIN 1 fuldført. Narrativt brief genereret.")
        current_app.logger.debug(f"Narrative Route: Modtaget brief (første 200 tegn): {narrative_brief[:200]}")

        # --- TRIN 2: Udarbejd Historieudkast med RAG ---
        current_app.logger.info("Narrative Route: Starter TRIN 2 - Udarbejdelse af historieudkast med RAG...")

        # narrative_focus_for_rag er den rå streng fra brugeren, som er god til RAG søgning
        story_title, story_content, reflection_questions = draft_narrative_story_with_rag(
            structured_brief=narrative_brief,
            original_user_inputs=original_user_inputs,  # Send alle originale input med videre
            narrative_focus_for_rag=narrative_focus  # Brug det centrale 'narrative_focus' til RAG
        )

        if isinstance(story_content, str) and story_content.lower().startswith("fejl:"):
            current_app.logger.error(
                f"Narrative Route (TRIN 2): Fejl fra draft_narrative_story_with_rag: {story_content}")
            return jsonify({"error": story_content, "details": "Fejl under Trin 2 (historie udarbejdelse)"}), 500

        current_app.logger.info("Narrative Route: TRIN 2 fuldført. Historieudkast og spørgsmål genereret.")

        # Her vil Trin 3 (Redaktør AI) komme senere.
        # For nu returnerer vi resultatet fra Trin 2.

        return jsonify({
            "status": "Trin 1 & 2 fuldført: Historieudkast og refleksionsspørgsmål genereret",
            "title": story_title,
            "story": story_content,
            "reflection_questions": reflection_questions,
            "narrative_brief_for_reference": narrative_brief  # Valgfrit: send brief med tilbage for debug/UI
        }), 200

    except Exception as e:
        current_app.logger.error(
            f"Narrative Route: Uventet fejl i /generate_narrative_story endpoint: {e}\n{traceback.format_exc()}")
        return jsonify({"error": "En uventet intern serverfejl opstod under narrativ generering."}), 500

@narrative_bp.route('/suggest_character_traits', methods=['POST'])
@login_required
def suggest_character_traits():
    """
    Endpoint til at få AI-assisterede forslag til karaktertræk
    baseret på et narrativt fokus.
    Kræver login.
    Modtager 'narrative_focus' via JSON.
    """
    user_id_for_log = current_user.id if hasattr(current_user, 'id') else 'Ukendt bruger'
    current_app.logger.info(f"Narrative route /suggest_character_traits kaldt af bruger: {user_id_for_log}")

    if not request.is_json:
        current_app.logger.warning(f"Bruger {user_id_for_log}: Kald til /suggest_character_traits uden JSON data.")
        return jsonify({"error": "Anmodning skal være JSON."}), 415

    data = request.get_json()
    current_app.logger.info(f"Bruger {user_id_for_log}: Modtaget rådata for /suggest_character_traits: {data}")

    narrative_focus = data.get('narrative_focus')

    if not narrative_focus or not isinstance(narrative_focus, str) or not narrative_focus.strip():
        current_app.logger.warning(f"Bruger {user_id_for_log}: 'narrative_focus' mangler eller er ugyldigt for /suggest_character_traits.")
        return jsonify({"error": "Obligatorisk felt 'narrative_focus' mangler eller er tomt."}), 400

    current_app.logger.info(f"Bruger {user_id_for_log}: narrative_focus for karaktertræk-forslag: '{narrative_focus}'")

    try:
        current_app.logger.info(f"Bruger {user_id_for_log}: Kalder ai_service for at få forslag til karaktertræk.")
        suggested_traits_data = get_ai_suggested_character_traits(narrative_focus)

        # Tjek om ai_service returnerede en fejl
        if isinstance(suggested_traits_data, dict) and 'error' in suggested_traits_data:
            current_app.logger.error(
                f"Bruger {user_id_for_log}: Fejl fra ai_service (karaktertræk): {suggested_traits_data.get('error')}")
            # Returner fejlen fra AI-servicen, men med en 500-status, da det er en server-side fejl i AI-laget
            return jsonify(suggested_traits_data), 500

        current_app.logger.info(
            f"Bruger {user_id_for_log}: Modtaget forslag til karaktertræk fra ai_service: {suggested_traits_data}")
        return jsonify(suggested_traits_data), 200

    except Exception as e:
        current_app.logger.error(
            f"Bruger {user_id_for_log}: Uventet fejl i /suggest_character_traits efter validering: {e}\n{traceback.format_exc()}")
        return jsonify({"error": "En uventet intern serverfejl opstod under forslag til karaktertræk."}), 500

# Flere narrative routes vil blive tilføjet her senere, f.eks.:
# @narrative_bp.route('/suggest_character_traits', methods=['POST'])
# @login_required
# def suggest_character_traits():
#     # ... logik ...
#     return jsonify({"message": "Suggest character traits endpoint"}), 200

# @narrative_bp.route('/get_guiding_questions', methods=['POST'])
# @login_required
# def get_guiding_questions():
#     # ... logik ...
#     return jsonify({"message": "Get guiding questions endpoint"}), 200