// Fil: static/modules/api_client.js

/**
 * Sender data til backend for at generere en historie.
 * @param {object} storyData - Objektet der indeholder alle input til historiegenerering.
 * @returns {Promise<object>} Et promise der resolver med JSON-svar fra serveren.
 * @throws {Error} Kaster en fejl hvis netværksrespons ikke er ok, eller ved andre fejl.
 */
export async function generateStoryApi(storyData) {
    console.log("DEBUG: api_client.js - generateStoryApi modtog storyData:", JSON.stringify(storyData, null, 2));
    console.log("api_client.js: generateStoryApi called with:", storyData);
    const response = await fetch('/story/generate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(storyData)
    });

    if (!response.ok) {
        let errorMsg = `Serverfejl under historiegenerering (${response.status})`;
        try {
            // Prøv at parse en JSON fejlbesked fra serveren
            const errorData = await response.json();
            errorMsg = errorData.error || errorData.story || `${errorMsg} ${response.statusText || ''}`;
        } catch (e) {
            // Hvis JSON parsing fejler, brug den rå tekstbesked
            const textError = await response.text();
            errorMsg += ` ${response.statusText || textError || '(ukendt serverfejl)'}`;
        }
        console.error("api_client.js: Server error in generateStoryApi:", errorMsg);
        throw new Error(errorMsg);
    }

    const result = await response.json();
    console.log("api_client.js: Story data received from server:", result);
    return result;
}

/**
 * Sender historietekst til backend for at generere et billede.
 * @param {string} storyText - Den aktuelle historietekst.
 * @returns {Promise<object>} Et promise der resolver med JSON-svar fra serveren (forventer image_url eller error).
 * @throws {Error} Kaster en fejl hvis netværksrespons ikke er ok, eller ved andre fejl.
 */
export async function generateImageApi(storyText) {
    console.log("api_client.js: generateImageApi called.");
    const response = await fetch('/story/generate_image_from_story', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ story_text: storyText })
    });

    if (!response.ok) {
        let errorMsg = `Serverfejl under billedgenerering (${response.status})`;
        try {
            const errorData = await response.json();
            errorMsg = errorData.error || `${errorMsg} ${response.statusText || ''}`;
        } catch (e) {
            const textError = await response.text();
            errorMsg += ` ${response.statusText || textError || '(ukendt serverfejl)'}`;
        }
        console.error("api_client.js: Server error in generateImageApi:", errorMsg);
        throw new Error(errorMsg);
    }

    const result = await response.json();
    console.log("api_client.js: Image data received from server:", result);
    return result;
}

/**
 * Sender det narrative fokus til backend for at få forslag til karaktertræk.
 * @param {string} narrativeFocus - Brugerens input for historiens centrale tema/udfordring.
 * @returns {Promise<object>} Et promise der resolver med JSON-svar fra serveren (forventer forslag eller error).
 * @throws {Error} Kaster en fejl hvis netværksrespons ikke er ok, eller ved andre fejl.
 */
export async function suggestCharacterTraitsApi(narrativeFocus) {
    console.log("api_client.js: suggestCharacterTraitsApi called with focus:", narrativeFocus);
    const response = await fetch('/narrative/suggest_character_traits', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ narrative_focus: narrativeFocus })
    });

    if (!response.ok) {
        let errorMsg = `Serverfejl under forslag til karaktertræk (${response.status})`;
        try {
            const errorData = await response.json();
            errorMsg = errorData.error || `${errorMsg} ${response.statusText || ''}`;
        } catch (e) {
            const textError = await response.text();
            errorMsg += ` ${response.statusText || textError || '(ukendt serverfejl)'}`;
        }
        console.error("api_client.js: Server error in suggestCharacterTraitsApi:", errorMsg);
        throw new Error(errorMsg);
    }

    const result = await response.json();
    console.log("api_client.js: Character trait suggestions received from server:", result);
    return result;
}

/**
 * Sender alle data for en narrativ historie til backend for generering.
 * @param {object} narrativeData - Objektet der indeholder alle input til den narrative historie.
 * @returns {Promise<object>} Et promise der resolver med JSON-svar fra serveren (forventer historie, titel, spørgsmål eller error).
 * @throws {Error} Kaster en fejl hvis netværksrespons ikke er ok, eller ved andre fejl.
 */
export async function generateNarrativeStoryApi(narrativeData) {
    console.log("api_client.js: generateNarrativeStoryApi called with data:", narrativeData);
    const response = await fetch('/narrative/generate_narrative_story', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(narrativeData)
    });

    if (!response.ok) {
        let errorMsg = `Serverfejl under generering af narrativ historie (${response.status})`;
        try {
            const errorData = await response.json();
            errorMsg = errorData.error || errorData.story || `${errorMsg} ${response.statusText || ''}`;
        } catch (e) {
            const textError = await response.text();
            errorMsg += ` ${response.statusText || textError || '(ukendt serverfejl)'}`;
        }
        console.error("api_client.js: Server error in generateNarrativeStoryApi:", errorMsg);
        throw new Error(errorMsg);
    }

    const result = await response.json();
    console.log("api_client.js: Narrative story data received from server:", result);
    return result;
}

/**
 * Henter vejledende refleksionsspørgsmål fra backend.
 * @param {object} contextData - Objekt indeholdende final_story_title, final_story_content, narrative_brief, og original_user_inputs.
 * @returns {Promise<object>} Et promise der resolver med JSON-svar fra serveren (forventer reflection_questions eller error).
 * @throws {Error} Kaster en fejl hvis netværksrespons ikke er ok, eller ved andre fejl.
 */
export async function getGuidingQuestionsApi(contextData) {
    console.log("api_client.js: getGuidingQuestionsApi called with context data:", contextData);
    const response = await fetch('/narrative/get_guiding_questions', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(contextData)
    });

    if (!response.ok) {
        let errorMsg = `Serverfejl under hentning af refleksionsspørgsmål (${response.status})`;
        try {
            const errorData = await response.json();
            errorMsg = errorData.error || `${errorMsg} ${response.statusText || ''}`;
        } catch (e) {
            const textError = await response.text();
            errorMsg += ` ${response.statusText || textError || '(ukendt serverfejl)'}`;
        }
        console.error("api_client.js: Server error in getGuidingQuestionsApi:", errorMsg);
        throw new Error(errorMsg);
    }

    const result = await response.json();
    console.log("api_client.js: Guiding questions received from server:", result);
    return result;
}

/**
 * Sender historietekst og stemmevalg til backend for at generere lyd.
 * @param {string} storyText - Den historie, der skal læses højt.
 * @param {string} voiceName - Navnet på den valgte stemme.
 * @returns {Promise<Response>} Et promise der resolver med den streamede lydrespons.
 * @throws {Error} Kaster en fejl hvis netværksrespons ikke er ok, eller ved andre fejl (f.eks. 403 Forbidden).
 */
export async function generateAudioApi(storyText, voiceName) {
    console.log(`api_client.js: generateAudioApi called for text (first 50 chars): '${storyText.substring(0, 50)}...' with voice: ${voiceName}`);
    const response = await fetch('/story/generate_audio', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ text: storyText, voice_name: voiceName })
    });

    if (!response.ok) {
        let errorMsg = `Serverfejl under lydgenerering (${response.status})`;
        try {
            const errorData = await response.json();
            errorMsg = errorData.error || `${errorMsg} ${response.statusText || ''}`;
        } catch (e) {
            const textError = await response.text();
            errorMsg += ` ${response.statusText || textError || '(ukendt serverfejl)'}`;
        }
        console.error("api_client.js: Server error in generateAudioApi:", errorMsg);
        throw new Error(errorMsg);
    }

    console.log("api_client.js: Audio stream response received.");
    return response; // Returnerer hele respons-objektet for streaming
}

/**
 * Sender data til backend for at generere en LIX-styret historie.
 * @param {object} lixStoryData - Objektet der indeholder alle input til Læsehesten.
 * @returns {Promise<object>} Et promise der resolver med JSON-svar fra serveren.
 * @throws {Error} Kaster en fejl hvis netværksrespons ikke er ok.
 */
export async function generateLixStoryApi(lixStoryData) {
    console.log("api_client.js: generateLixStoryApi called with:", lixStoryData);
    const response = await fetch('/story/generate_lix', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(lixStoryData)
    });

    if (!response.ok) {
        let errorMsg = `Serverfejl under generering af Læsehest-historie (${response.status})`;
        try {
            const errorData = await response.json();
            errorMsg = errorData.error || `${errorMsg} - ${response.statusText}`;
        } catch (e) {
            errorMsg += ` - ${response.statusText}`;
        }
        console.error("api_client.js: Server error in generateLixStoryApi:", errorMsg);
        throw new Error(errorMsg);
    }

    const result = await response.json();
    console.log("api_client.js: LIX Story data received from server:", result);
    return result;
}

// ... eksisterende kode i api_client.js
// Sørg for at denne funktion tilføjes til filen.
// Den kan placeres efter den sidste eksisterende funktion.

export async function analyzeStoryForLogbookApi(storyContent) {
    console.log("api_client.js: analyzeStoryForLogbookApi called.");
    const response = await fetch('/narrative/analyze-for-logbook', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ story_content: storyContent })
    });

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: "Serverfejl med ugyldigt svarformat." }));
        throw new Error(errorData.error || `Serverfejl: ${response.status}`);
    }

    return await response.json();
}

export async function saveLogbookEntryApi(storyId, dataToSave) {
    console.log(`api_client.js: saveLogbookEntryApi called for story ID: ${storyId}`);
    const response = await fetch(`/narrative/save-log-entry/${storyId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(dataToSave)
    });

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: "Serverfejl ved gem." }));
        throw new Error(errorData.error || `Serverfejl: ${response.status}`);
    }

    return await response.json();
}

export async function filterLogbookApi(filterData) {
    console.log("api_client.js: filterLogbookApi called with:", filterData);
    // VIGTIGT: Sørg for at URL'en matcher den route, vi har defineret i narrative_routes.py
    const response = await fetch('/narrative/api/logbook/filter', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(filterData)
    });

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: "Serverfejl ved filtrering." }));
        throw new Error(errorData.error || `Serverfejl: ${response.status}`);
    }

    return await response.json();
}

export async function updateNoteApi(storyId, notes) {
    console.log(`api_client.js: updateNoteApi called for story ID: ${storyId}`);
    // VIGTIGT: Sørg for at URL'en matcher den route, vi har defineret i narrative_routes.py
    const response = await fetch(`/narrative/api/notes/update/${storyId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ notes: notes })
    });

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: "Serverfejl ved opdatering af note." }));
        throw new Error(errorData.error || `Serverfejl: ${response.status}`);
    }

    return await response.json();
}

export async function listContinuableStoriesApi() {
    console.log("api_client.js: listContinuableStoriesApi called.");
    const response = await fetch('/narrative/api/list-stories', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    });

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: "Serverfejl ved hentning af historieliste." }));
        throw new Error(errorData.error || `Serverfejl: ${response.status}`);
    }

    return await response.json();
}

export async function generateProblemImageApi(narrativeData) {
    console.log("api_client.js: generateProblemImageApi called.");
    const response = await fetch('/narrative/generate_problem_image', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(narrativeData)
    });

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: "Serverfejl ved generering af problem-billede." }));
        throw new Error(errorData.error || `Serverfejl: ${response.status}`);
    }

    return await response.json();
}