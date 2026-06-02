import traceback
from collections import defaultdict

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from sqlalchemy import or_

from extensions import db
from models import Story, ChildProfile, ProfileAttribute, ProfileRelation
from services.ai_service import (
    get_ai_suggested_character_traits,
    generate_narrative_brief,
    draft_narrative_story_with_rag,
    edit_narrative_story,
    analyze_story_for_logbook,
    generate_problem_image,
    generate_image_prompt_from_gemini,
    generate_image_with_vertexai,
    generate_reflection_questions,
)

narrative_bp = Blueprint('narrative', __name__, url_prefix='/narrative')


@narrative_bp.route('/generate_narrative_story', methods=['POST'])
@login_required
def generate_narrative_story():
    original_user_inputs = request.get_json()
    if not original_user_inputs:
        return jsonify({"error": "Ingen JSON data modtaget"}), 400

    user_id = current_user.id
    parent_story_id = original_user_inputs.get('parent_story_id')
    continuation_strategy = original_user_inputs.get('continuation_strategy')
    continuation_context = None
    root_story_title = None
    parent_story = None

    if parent_story_id and continuation_strategy:
        parent_story = db.session.get(Story, parent_story_id)
        if parent_story and parent_story.user_id == user_id:
            continuation_context = {
                'strategy': continuation_strategy,
                'problem_name': parent_story.problem_name,
                'discovered_method_name': parent_story.discovered_method_name,
            }
            root_story = parent_story
            while root_story.parent_story:
                root_story = root_story.parent_story
            root_story_title = root_story.title
        else:
            current_app.logger.warning(f"Bruger {user_id} forsøgte at fortsætte en ugyldig historie.")
            parent_story_id = None

    try:
        narrative_brief = generate_narrative_brief(original_user_inputs)
        draft_title, draft_content = draft_narrative_story_with_rag(
            structured_brief=narrative_brief,
            original_user_inputs=original_user_inputs,
            narrative_focus_for_rag=original_user_inputs.get('narrative_focus'),
            continuation_context=continuation_context,
        )
        final_title, final_content = edit_narrative_story(
            story_draft_title=draft_title,
            story_draft_content=draft_content,
            original_user_inputs=original_user_inputs,
        )

        new_story = Story(
            title=final_title,
            content=final_content,
            user_id=user_id,
            source='Narrativ Støtte',
            is_log_entry=False,
        )

        if parent_story_id and parent_story:
            new_story.parent_story_id = parent_story_id
            new_story.series_part = (parent_story.series_part or 1) + 1

        db.session.add(new_story)
        db.session.commit()

        response_data = {
            "status": "Historie genereret og gemt.",
            "story_id": new_story.id,
            "title": new_story.title,
            "story": new_story.content,
            "narrative_brief_for_reference": narrative_brief,
        }
        if root_story_title:
            response_data["root_story_title"] = root_story_title

        return jsonify(response_data), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Fejl i generate_narrative_story: {e}\n{traceback.format_exc()}")
        return jsonify({"error": "En uventet serverfejl opstod."}), 500


@narrative_bp.route('/suggest_character_traits', methods=['POST'])
@login_required
def suggest_character_traits():
    if not request.is_json:
        return jsonify({"error": "Anmodning skal være JSON."}), 415

    data = request.get_json()
    narrative_focus = data.get('narrative_focus', '').strip()

    if not narrative_focus:
        return jsonify({"error": "Feltet 'narrative_focus' er påkrævet."}), 400

    try:
        result = get_ai_suggested_character_traits(narrative_focus)
        if isinstance(result, dict) and 'error' in result:
            return jsonify(result), 500
        return jsonify(result), 200
    except Exception as e:
        current_app.logger.error(f"Fejl i suggest_character_traits: {e}\n{traceback.format_exc()}")
        return jsonify({"error": "Intern serverfejl."}), 500


@narrative_bp.route('/analyze-for-logbook', methods=['POST'])
@login_required
def analyze_for_logbook():
    if not request.is_json:
        return jsonify({"error": "Anmodning skal være JSON."}), 415

    data = request.get_json()
    story_content = data.get('story_content', '').strip()

    if not story_content:
        return jsonify({"error": "Feltet 'story_content' er påkrævet."}), 400

    try:
        result = analyze_story_for_logbook(story_content)
        if 'error' in result:
            return jsonify(result), 500
        return jsonify(result), 200
    except Exception as e:
        current_app.logger.error(f"Fejl i analyze_for_logbook: {e}\n{traceback.format_exc()}")
        return jsonify({"error": "Intern serverfejl."}), 500


@narrative_bp.route('/save-log-entry/<int:story_id>', methods=['POST'])
@login_required
def save_log_entry(story_id):
    story = db.get_or_404(Story, story_id)
    if story.user_id != current_user.id:
        return jsonify({"error": "Uautoriseret adgang."}), 403

    data = request.get_json()
    if not data:
        return jsonify({"error": "Ingen data modtaget."}), 400

    try:
        story.problem_name = data.get('problem_name')
        story.problem_category = data.get('problem_category')
        story.problem_influence = data.get('problem_influence')
        story.unique_outcome = data.get('unique_outcome')
        story.discovered_method_name = data.get('discovered_method_name')
        story.strength_type = data.get('strength_type')
        story.discovered_method_steps = data.get('discovered_method_steps')
        story.child_values = data.get('child_values')
        story.support_system = data.get('support_system')
        story.user_notes = data.get('user_notes')
        story.ai_summary = data.get('ai_summary')

        pb = data.get('progress_before')
        story.progress_before = int(pb) if pb is not None and str(pb).isdigit() else None

        pa = data.get('progress_after')
        story.progress_after = int(pa) if pa is not None and str(pa).isdigit() else None

        story.is_log_entry = True

        if story.parent_story_id and story.parent_story:
            story.root_story_id = story.parent_story.root_story_id or story.parent_story.id
        elif not story.parent_story_id:
            story.root_story_id = story.id

        db.session.commit()
        return jsonify({"success": True, "message": "Historien er gemt i din logbog."}), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Fejl ved gemning af logentry {story_id}: {e}\n{traceback.format_exc()}")
        return jsonify({"error": "Intern fejl under gemning."}), 500


@narrative_bp.route('/api/list-stories', methods=['GET'])
@login_required
def list_stories_for_continuation():
    try:
        stories = Story.query.filter_by(
            user_id=current_user.id,
            is_log_entry=True,
            source='Narrativ Støtte',
        ).order_by(Story.created_at.desc()).all()
        return jsonify([{'id': s.id, 'title': s.title} for s in stories])
    except Exception as e:
        current_app.logger.error(f"Fejl ved list_stories: {e}")
        return jsonify({"error": "Intern fejl."}), 500


@narrative_bp.route('/api/logbook/filter', methods=['POST'])
@login_required
def filter_logbook():
    data = request.get_json() or {}
    search_term = data.get('searchTerm', '').strip()
    sort_by = data.get('sortBy', 'newest')

    RootStory = db.aliased(Story)

    query = db.session.query(
        Story,
        RootStory.title.label('root_story_title')
    ).outerjoin(
        RootStory, Story.root_story_id == RootStory.id
    ).filter(
        Story.user_id == current_user.id,
        Story.is_log_entry == True
    )

    if search_term:
        query = query.filter(or_(
            Story.title.ilike(f'%{search_term}%'),
            Story.content.ilike(f'%{search_term}%'),
            Story.problem_name.ilike(f'%{search_term}%'),
        ))

    if sort_by == 'oldest':
        query = query.order_by(Story.created_at.asc())
    elif sort_by == 'title_asc':
        query = query.order_by(Story.title.asc())
    elif sort_by == 'title_desc':
        query = query.order_by(Story.title.desc())
    else:
        query = query.order_by(Story.created_at.desc())

    results = query.all()

    stories_list = []
    for story, root_title in results:
        stories_list.append({
            'id': story.id,
            'title': story.title,
            'content': story.content,
            'created_at': story.created_at.strftime('%d. %b %Y'),
            'problem_name': story.problem_name,
            'problem_category': story.problem_category,
            'problem_influence': story.problem_influence,
            'unique_outcome': story.unique_outcome,
            'discovered_method_name': story.discovered_method_name,
            'strength_type': story.strength_type,
            'discovered_method_steps': story.discovered_method_steps,
            'child_values': story.child_values,
            'support_system': story.support_system,
            'user_notes': story.user_notes,
            'ai_summary': story.ai_summary,
            'progress_before': story.progress_before,
            'progress_after': story.progress_after,
            'series_part': story.series_part,
            'strategy_used': story.strategy_used,
            'root_story_title': root_title if story.id != story.root_story_id else None,
        })

    return jsonify(stories_list)


@narrative_bp.route('/api/notes/update/<int:story_id>', methods=['POST'])
@login_required
def update_note(story_id):
    story = db.get_or_404(Story, story_id)
    if story.user_id != current_user.id:
        return jsonify({"error": "Uautoriseret."}), 403

    data = request.get_json()
    if not data or 'notes' not in data:
        return jsonify({"error": "Manglende 'notes' felt."}), 400

    try:
        story.user_notes = data['notes']
        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Intern fejl."}), 500


@narrative_bp.route('/api/profile/save', methods=['POST'])
@login_required
def save_child_profile():
    data = request.get_json()
    if not data or not data.get('name'):
        return jsonify({"error": "Profilnavn er påkrævet."}), 400

    profile_id = data.get('id')

    try:
        if profile_id:
            profile = db.get_or_404(ChildProfile, profile_id)
            if profile.user_id != current_user.id:
                return jsonify({"error": "Uautoriseret."}), 403
            profile.name = data.get('name')
            profile.age = data.get('age')
            ProfileAttribute.query.filter_by(profile_id=profile_id).delete()
            ProfileRelation.query.filter_by(profile_id=profile_id).delete()
        else:
            profile = ChildProfile(user_id=current_user.id, name=data.get('name'), age=data.get('age'))
            db.session.add(profile)
            db.session.flush()

        for attr_type, key in [('strength', 'strengths'), ('value', 'values'),
                                ('motivation', 'motivations'), ('reaction', 'reactions')]:
            for content in data.get(key, []):
                if content:
                    db.session.add(ProfileAttribute(profile_id=profile.id, type=attr_type, content=content))

        for rel in data.get('relations', []):
            if rel.get('name') or rel.get('type'):
                db.session.add(ProfileRelation(profile_id=profile.id, name=rel.get('name'),
                                               relation_type=rel.get('type')))

        db.session.commit()
        return jsonify({"success": True, "profile_id": profile.id}), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Fejl ved save_child_profile: {e}\n{traceback.format_exc()}")
        return jsonify({"error": "Intern fejl."}), 500


@narrative_bp.route('/api/profiles/list', methods=['GET'])
@login_required
def list_child_profiles():
    try:
        profiles = ChildProfile.query.filter_by(user_id=current_user.id).order_by(
            ChildProfile.created_at.desc()).all()

        if not profiles:
            return jsonify([]), 200

        profile_ids = [p.id for p in profiles]
        all_attrs = ProfileAttribute.query.filter(ProfileAttribute.profile_id.in_(profile_ids)).all()
        attrs_by_profile = defaultdict(lambda: defaultdict(list))
        for attr in all_attrs:
            attrs_by_profile[attr.profile_id][attr.type].append(attr.content)

        all_rels = ProfileRelation.query.filter(ProfileRelation.profile_id.in_(profile_ids)).all()
        rels_by_profile = defaultdict(list)
        for rel in all_rels:
            rels_by_profile[rel.profile_id].append({"name": rel.name, "type": rel.relation_type})

        return jsonify([
            {
                "id": p.id, "name": p.name, "age": p.age,
                "strengths": attrs_by_profile[p.id].get('strength', []),
                "values": attrs_by_profile[p.id].get('value', []),
                "motivations": attrs_by_profile[p.id].get('motivation', []),
                "reactions": attrs_by_profile[p.id].get('reaction', []),
                "relations": rels_by_profile[p.id],
            }
            for p in profiles
        ]), 200

    except Exception as e:
        current_app.logger.error(f"Fejl ved list_child_profiles: {e}\n{traceback.format_exc()}")
        return jsonify({"error": "Intern fejl."}), 500


@narrative_bp.route('/api/profile/delete/<int:profile_id>', methods=['DELETE'])
@login_required
def delete_child_profile(profile_id):
    profile = db.get_or_404(ChildProfile, profile_id)
    if profile.user_id != current_user.id:
        return jsonify({"error": "Uautoriseret."}), 403
    try:
        db.session.delete(profile)
        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Intern fejl."}), 500


@narrative_bp.route('/api/delete/<int:story_id>', methods=['DELETE'])
@login_required
def delete_story(story_id):
    story = db.get_or_404(Story, story_id)
    if story.user_id != current_user.id:
        return jsonify({"error": "Uautoriseret."}), 403
    try:
        Story.query.filter_by(parent_story_id=story_id).update(
            {'parent_story_id': None}, synchronize_session='fetch'
        )
        db.session.delete(story)
        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Intern fejl."}), 500


@narrative_bp.route('/get_guiding_questions', methods=['POST'])
@login_required
def get_guiding_questions():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Mangler data."}), 400
    try:
        questions = generate_reflection_questions(
            final_story_title=data.get('final_story_title', ''),
            final_story_content=data.get('final_story_content', ''),
            narrative_brief=data.get('narrative_brief', ''),
            original_user_inputs=data.get('original_user_inputs', {}),
        )
        return jsonify({"reflection_questions": questions})
    except Exception as e:
        current_app.logger.error(f"Fejl i get_guiding_questions: {e}")
        return jsonify({"error": "Intern fejl."}), 500


@narrative_bp.route('/generate_problem_image', methods=['POST'])
@login_required
def generate_problem_image_route():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Mangler data."}), 400
    try:
        result = generate_problem_image(data)
        if "error" in result:
            return jsonify(result), 500
        return jsonify(result), 200
    except Exception as e:
        current_app.logger.error(f"Fejl i generate_problem_image: {e}\n{traceback.format_exc()}")
        return jsonify({"error": "Intern fejl."}), 500


@narrative_bp.route('/generate_story_image', methods=['POST'])
@login_required
def generate_story_image():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Mangler data."}), 400

    story_text = data.get('storyContent', '')
    chars = data.get('main_characters', [])
    places = data.get('places', [])

    if not story_text:
        return jsonify({"error": "Mangler 'storyContent'."}), 400

    char_descs = [
        f"{c.get('description', '')} ved navn {c.get('name', '')}".strip()
        for c in chars if c.get('description')
    ]
    karakter_str = ", ".join(char_descs) or "en uspecificeret karakter"
    sted_str = ", ".join(filter(None, places)) or "et uspecificeret sted"

    try:
        image_prompt = generate_image_prompt_from_gemini(story_text, karakter_str, sted_str)
        image_url = generate_image_with_vertexai(image_prompt)
        if image_url:
            return jsonify({"image_url": image_url, "image_prompt_used": image_prompt})
        return jsonify({"error": "Kunne ikke generere billede."}), 500
    except Exception as e:
        current_app.logger.error(f"Fejl i generate_story_image: {e}\n{traceback.format_exc()}")
        return jsonify({"error": "Intern fejl."}), 500
