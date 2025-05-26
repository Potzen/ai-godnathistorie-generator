# Fil: routes/narrative_routes.py
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from services.ai_service import (
    get_ai_suggested_character_traits,
    generate_narrative_brief,
    draft_narrative_story_with_rag,
    edit_narrative_story  # Sørg for denne import er her
)

narrative_bp = Blueprint('narrative', __name__, url_prefix='/narrative')

@narrative_bp.route('/generate_narrative_story', methods=['POST'])
# @login_required # Stadig udkommenteret for test
def generate_narrative_story():
    original_user_inputs = request.get_json()
    if not original_user_inputs:
        current_app.logger.error("Narrative Route: Ingen JSON data modtaget.")
        return jsonify({"error": "Ingen JSON data modtaget"}), 400

    # Definer user_id_for_log her, så den er tilgængelig i hele funktionen
    user_id_for_log = current_user.id if hasattr(current_user, 'id') and current_user.is_authenticated else 'Ukendt (narrativ test)'
    current_app.logger.info(f"Narrative Route (Bruger: {user_id_for_log}): Modtaget data for /generate_narrative_story: {original_user_inputs}")

    # --- TRIN 1: Generer Narrativt Brief ---
    narrative_focus = original_user_inputs.get('narrative_focus')
    if not narrative_focus:
        current_app.logger.error(f"Bruger {user_id_for_log}: Manglende 'narrative_focus' i /generate_narrative_story.")
        return jsonify({"error": "Obligatorisk felt 'narrative_focus' mangler."}), 400

    try:
        current_app.logger.info(f"Bruger {user_id_for_log}: Starter TRIN 1 - Generering af narrativt brief...")
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
            current_app.logger.error(f"Bruger {user_id_for_log} (TRIN 1): Fejl fra generate_narrative_brief: {narrative_brief}")
            return jsonify({"error": narrative_brief, "details": "Fejl under Trin 1 (brief generering)"}), 500

        current_app.logger.info(f"Bruger {user_id_for_log}: TRIN 1 fuldført. Narrativt brief genereret.")
        current_app.logger.debug(f"Narrative Route (Bruger: {user_id_for_log}): Modtaget brief (første 200 tegn): {narrative_brief[:200]}")

        # --- TRIN 2: Udarbejd Historieudkast med RAG ---
        current_app.logger.info(f"Bruger {user_id_for_log}: Starter TRIN 2 - Udarbejdelse af historieudkast med RAG...")
        story_title_from_draft, story_content_from_draft, reflection_questions = draft_narrative_story_with_rag(
            structured_brief=narrative_brief,
            original_user_inputs=original_user_inputs,
            narrative_focus_for_rag=narrative_focus
        )

        if isinstance(story_content_from_draft, str) and story_content_from_draft.lower().startswith("fejl:"):
            current_app.logger.error(
                f"Bruger {user_id_for_log} (TRIN 2): Fejl fra draft_narrative_story_with_rag: {story_content_from_draft}")
            return jsonify({"error": story_content_from_draft, "details": "Fejl under Trin 2 (historie udarbejdelse)"}), 500

        if not story_title_from_draft or not story_content_from_draft: # Korrekt tjek
            current_app.logger.warning(
                f"Bruger {user_id_for_log} (TRIN 2): draft_narrative_story_with_rag returnerede tom titel eller indhold. Titel: '{story_title_from_draft}', Indhold OK: {bool(story_content_from_draft)}")
            return jsonify(
                {"error": "Historieudkast fra Trin 2 var ufuldstændigt.", "title_received": story_title_from_draft,
                 "content_received": bool(story_content_from_draft)}), 500

        current_app.logger.info(
            f"Bruger {user_id_for_log}: TRIN 2 fuldført. Historieudkast '{story_title_from_draft[:50]}...' og {len(reflection_questions)} spørgsmål genereret.")

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
                "reflection_questions": reflection_questions,
                "narrative_brief_for_reference": narrative_brief,
                "error_details_step3": final_story_content
            }), 200

        current_app.logger.info(f"Bruger {user_id_for_log}: TRIN 3 fuldført. Historie redigeret til '{final_story_title[:50]}...'.")

        return jsonify({
            "status": "Alle 3 trin fuldført: Endelig narrativ historie og refleksionsspørgsmål genereret.",
            "title": final_story_title,
            "story": final_story_content,
            "reflection_questions": reflection_questions,
            "narrative_brief_for_reference": narrative_brief,
            "draft_title_from_step2_for_reference": story_title_from_draft,
            "draft_content_from_step2_for_reference": story_content_from_draft[:200] + "..." if story_content_from_draft else None
        }), 200

    except Exception as e:
        current_app.logger.error(
            f"Bruger {user_id_for_log}: Uventet fejl i /generate_narrative_story endpoint: {e}\n{traceback.format_exc()}")
        return jsonify({"error": "En uventet intern serverfejl opstod under narrativ generering."}), 500

@narrative_bp.route('/suggest_character_traits', methods=['POST'])
@login_required
def suggest_character_traits():
    user_id_for_log = current_user.id if hasattr(current_user, 'id') else 'Ukendt bruger (karaktertræk login påkrævet)'
    current_app.logger.info(f"Narrative route /suggest_character_traits kaldt af bruger: {user_id_for_log}")

    if not request.is_json:
        current_app.logger.warning(f"Bruger {user_id_for_log}: Kald til /suggest_character_traits uden JSON data.")
        return jsonify({"error": "Anmodning skal være JSON."}), 415

    data = request.get_json()
    current_app.logger.debug(f"Bruger {user_id_for_log}: Modtaget rådata for /suggest_character_traits: {data}")

    narrative_focus = data.get('narrative_focus')

    if not narrative_focus or not isinstance(narrative_focus, str) or not narrative_focus.strip():
        current_app.logger.warning(f"Bruger {user_id_for_log}: 'narrative_focus' mangler eller er ugyldigt for /suggest_character_traits.")
        return jsonify({"error": "Obligatorisk felt 'narrative_focus' mangler eller er tomt."}), 400

    current_app.logger.info(f"Bruger {user_id_for_log}: narrative_focus for karaktertræk-forslag: '{narrative_focus}'")

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