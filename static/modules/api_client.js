// Fil: static/modules/api_client.js

/**
 * Sender data til backend for at generere en historie.
 * @param {object} storyData - Objektet der indeholder alle input til historiegenerering.
 * @returns {Promise<object>} Et promise der resolver med JSON-svar fra serveren.
 * @throws {Error} Kaster en fejl hvis netværksrespons ikke er ok, eller ved andre fejl.
 */
export async function generateStoryApi(storyData) {
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


// Flere API-funktioner vil blive tilføjet her senere (f.eks. for billeder, lyd, narrativ støtte)