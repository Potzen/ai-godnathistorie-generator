// static/modules/api_client.js – Narrativ Støtte App

async function apiFetch(url, options = {}) {
    const response = await fetch(url, {
        headers: { 'Content-Type': 'application/json' },
        ...options,
    });
    if (!response.ok) {
        let errorMsg = `Serverfejl (${response.status})`;
        try {
            const data = await response.json();
            errorMsg = data.error || errorMsg;
        } catch (e) {}
        throw new Error(errorMsg);
    }
    return response.json();
}

export async function generateNarrativeStoryApi(data) {
    return apiFetch('/narrative/generate_narrative_story', {
        method: 'POST',
        body: JSON.stringify(data),
    });
}

export async function suggestCharacterTraitsApi(narrativeFocus) {
    return apiFetch('/narrative/suggest_character_traits', {
        method: 'POST',
        body: JSON.stringify({ narrative_focus: narrativeFocus }),
    });
}

export async function getGuidingQuestionsApi(contextData) {
    return apiFetch('/narrative/get_guiding_questions', {
        method: 'POST',
        body: JSON.stringify(contextData),
    });
}

export async function analyzeStoryForLogbookApi(storyContent) {
    return apiFetch('/narrative/analyze-for-logbook', {
        method: 'POST',
        body: JSON.stringify({ story_content: storyContent }),
    });
}

export async function saveLogbookEntryApi(storyId, data) {
    return apiFetch(`/narrative/save-log-entry/${storyId}`, {
        method: 'POST',
        body: JSON.stringify(data),
    });
}

export async function filterLogbookApi(filterData) {
    return apiFetch('/narrative/api/logbook/filter', {
        method: 'POST',
        body: JSON.stringify(filterData),
    });
}

export async function updateNoteApi(storyId, notes) {
    return apiFetch(`/narrative/api/notes/update/${storyId}`, {
        method: 'POST',
        body: JSON.stringify({ notes }),
    });
}

export async function listContinuableStoriesApi() {
    return apiFetch('/narrative/api/list-stories');
}

export async function generateNarrativeStoryImageApi(data) {
    return apiFetch('/narrative/generate_story_image', {
        method: 'POST',
        body: JSON.stringify(data),
    });
}

export async function generateProblemImageApi(data) {
    return apiFetch('/narrative/generate_problem_image', {
        method: 'POST',
        body: JSON.stringify(data),
    });
}

export async function deleteStoryApi(storyId) {
    const response = await fetch(`/narrative/api/delete/${storyId}`, { method: 'DELETE' });
    if (!response.ok) {
        const d = await response.json().catch(() => ({}));
        throw new Error(d.error || `Serverfejl: ${response.status}`);
    }
    return response.json();
}

export async function saveChildProfileApi(profileData) {
    return apiFetch('/narrative/api/profile/save', {
        method: 'POST',
        body: JSON.stringify(profileData),
    });
}

export async function listChildProfilesApi() {
    return apiFetch('/narrative/api/profiles/list');
}

export async function deleteChildProfileApi(profileId) {
    const response = await fetch(`/narrative/api/profile/delete/${profileId}`, { method: 'DELETE' });
    if (!response.ok) {
        const d = await response.json().catch(() => ({}));
        throw new Error(d.error || `Serverfejl: ${response.status}`);
    }
    return response.json();
}
