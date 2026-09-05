// Fil: static/modules/api_client.js
//
// Alle kald til backend'en. Tidligere gentog hver funktion den samme ~25
// linjers fetch- og fejlhaandtering; den ligger nu ét sted i request().

/**
 * Udfoerer et kald til backend'en og haandterer fejl ensartet.
 *
 * @param {string} url - Endepunktet.
 * @param {object} [options]
 * @param {string} [options.method='POST'] - HTTP-metode.
 * @param {object} [options.body] - Sendes som JSON. Udelades ved GET/DELETE.
 * @param {string} [options.label='Serverfejl'] - Tekst der indleder fejlbeskeden.
 * @param {boolean} [options.raw=false] - Returnér hele Response i stedet for JSON
 *                                        (bruges til lydstreaming).
 * @returns {Promise<object|Response>}
 * @throws {Error} Hvis serveren svarer med en fejlkode.
 */
async function request(url, { method = 'POST', body, label = 'Serverfejl', raw = false } = {}) {
    const init = { method };
    if (body !== undefined) {
        init.headers = { 'Content-Type': 'application/json' };
        init.body = JSON.stringify(body);
    }

    const response = await fetch(url, init);

    if (!response.ok) {
        let message = `${label} (${response.status})`;
        try {
            const data = await response.json();
            // Nogle endepunkter lægger fejlteksten i 'story' i stedet for 'error'.
            message = data.error || data.story || message;
        } catch {
            message = `${message} ${response.statusText || ''}`.trim();
        }
        throw new Error(message);
    }

    return raw ? response : response.json();
}

// --- Historier ---

export const generateStoryApi = (storyData) =>
    request('/story/generate', { body: storyData, label: 'Serverfejl under historiegenerering' });

export const generateLixStoryApi = (lixStoryData) =>
    request('/story/generate_lix', { body: lixStoryData, label: 'Serverfejl under Læsehest-generering' });

export const saveHojtlasningStoryApi = (storyData) =>
    request('/story/save_to_logbook', { body: storyData, label: 'Serverfejl ved gemning' });

export const generateQuizApi = (story_content, lix_score) =>
    request('/story/generate_quiz', {
        body: { story_content, lix_score },
        label: 'Serverfejl ved quiz-generering',
    });

// Returnerer hele Response-objektet, saa lyden kan streames.
export const generateAudioApi = (storyText, voiceName) =>
    request('/story/generate_audio', {
        body: { text: storyText, voice_name: voiceName },
        label: 'Serverfejl under lydgenerering',
        raw: true,
    });

// --- Billeder ---

export const generateImageApi = (dataToSend) =>
    request('/story/generate_image_from_story', { body: dataToSend, label: 'Serverfejl under billedgenerering' });

export const generateProblemImageApi = (narrativeData) =>
    request('/narrative/generate_problem_image', { body: narrativeData, label: 'Serverfejl under billedgenerering' });

export const generateNarrativeStoryImageApi = (narrativeData) =>
    request('/narrative/generate_story_image', { body: narrativeData, label: 'Serverfejl under billedgenerering' });

// --- Narrativ Stoette ---

export const suggestCharacterTraitsApi = (narrativeFocus) =>
    request('/narrative/suggest_character_traits', {
        body: { narrative_focus: narrativeFocus },
        label: 'Serverfejl ved forslag til karaktertræk',
    });

export const generateNarrativeStoryApi = (narrativeData) =>
    request('/narrative/generate_narrative_story', { body: narrativeData, label: 'Serverfejl under historiegenerering' });

export const getGuidingQuestionsApi = (contextData) =>
    request('/narrative/get_guiding_questions', { body: contextData, label: 'Serverfejl ved hentning af spørgsmål' });

export const analyzeStoryForLogbookApi = (storyContent) =>
    request('/narrative/analyze-for-logbook', {
        body: { story_content: storyContent },
        label: 'Serverfejl under analyse',
    });

// --- Logbog ---

export const saveLogbookEntryApi = (storyId, dataToSave) =>
    request(`/narrative/save-log-entry/${storyId}`, { body: dataToSave, label: 'Serverfejl ved gemning af logbogsindlæg' });

export const filterLogbookApi = (filterData) =>
    request('/narrative/api/logbook/filter', { body: filterData, label: 'Serverfejl ved filtrering' });

export const updateNoteApi = (storyId, notes) =>
    request(`/narrative/api/notes/update/${storyId}`, { body: { notes }, label: 'Serverfejl ved gemning af note' });

export const listContinuableStoriesApi = () =>
    request('/narrative/api/list-stories', { method: 'GET', label: 'Serverfejl ved hentning af historier' });

export const deleteStoryApi = (storyId) =>
    request(`/narrative/api/delete/${storyId}`, { method: 'DELETE', label: 'Serverfejl ved sletning' });

// --- Barneprofiler ---

export const saveChildProfileApi = (profileData) =>
    request('/narrative/api/profile/save', { body: profileData, label: 'Serverfejl ved gemning af profil' });

export const listChildProfilesApi = () =>
    request('/narrative/api/profiles/list', { method: 'GET', label: 'Serverfejl ved hentning af profiler' });

export const deleteChildProfileApi = (profileId) =>
    request(`/narrative/api/profile/delete/${profileId}`, { method: 'DELETE', label: 'Serverfejl ved sletning af profil' });

// --- Klasselokale ---

export const saveQuizResultApi = (data) =>
    request('/classroom/quiz_result', { body: data, label: 'Serverfejl ved gemning af quizresultat' });

export const listClassroomsApi = () =>
    request('/classroom/', { method: 'GET', label: 'Serverfejl ved hentning af klasser' });

export const createClassroomApi = (name) =>
    request('/classroom/create', { body: { name }, label: 'Serverfejl ved oprettelse af klasse' });

export const listClassroomStudentsApi = (classroomId) =>
    request(`/classroom/${classroomId}/students`, { method: 'GET', label: 'Serverfejl ved hentning af elever' });

export const joinClassroomApi = (inviteCode) =>
    request('/classroom/join', { body: { invite_code: inviteCode }, label: 'Serverfejl ved tilmelding' });

// --- Ugens fokus, ordbank og hjemmelæsning ---

export const mitUgefokusApi = () =>
    request('/focus/mit', { method: 'GET', label: 'Kunne ikke hente ugens fokus' });

export const hentKlassefokusApi = (classroomId, aar, uge) => {
    const q = (aar && uge) ? `?aar=${aar}&uge=${uge}` : '';
    return request(`/focus/${classroomId}${q}`, { method: 'GET', label: 'Kunne ikke hente ugens fokus' });
};

export const saetKlassefokusApi = (classroomId, fokus) =>
    request(`/focus/${classroomId}`, { body: fokus, label: 'Kunne ikke gemme ugens fokus' });

export const minOrdbankApi = () =>
    request('/ordbank/mit', { method: 'GET', label: 'Kunne ikke hente ordbanken' });

export const gemHjemmelaesningApi = (data) =>
    request('/hjemmelaesning/log', { body: data, label: 'Kunne ikke gemme læsningen' });

export const hentHjemmelaesningApi = () =>
    request('/hjemmelaesning/log', { method: 'GET', label: 'Kunne ikke hente læsningen' });

export const niveauForslagApi = () =>
    request('/story/niveau_forslag', { method: 'GET', label: 'Kunne ikke hente niveauforslag' });
