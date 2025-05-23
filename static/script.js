// Kør først koden, når hele HTML dokumentet er færdigindlæst og klar
document.addEventListener('DOMContentLoaded', () => {
    console.log("DOMContentLoaded event fired. Initializing Read Me A Story script.");

// HJÆLPEFUNKTION TIL AT SPORE GOOGLE ANALYTICS HÆNDELSER
function trackGAEvent(action, category, label, value) {
    const consentStatus = localStorage.getItem('cookieConsent');
    if (consentStatus === 'accepted' && typeof gtag === 'function') {
        // Log til konsollen for at bekræfte, at hændelsen forsøges sendt
        console.log(`GA Event: Action='${action}', Category='${category}', Label='${label}'` + (value !== undefined ? `, Value=${value}` : ''));

        gtag('event', action, {
            'event_category': category,
            'event_label': label,
            'value': value // 'value' er valgfri og skal være et heltal
            // 'non_interaction': true // Sæt til true hvis hændelsen ikke skal påvirke afvisningsprocenten
        });
    } else if (consentStatus !== 'accepted') {
        console.log(`GA Event not sent (consent not accepted): Action='${action}', Category='${category}', Label='${label}'`);
    } else if (typeof gtag !== 'function') {
        console.warn(`GA Event not sent (gtag function not found): Action='${action}', Category='${category}', Label='${label}'`);
    }
}

    // === Hent referencer til HTML elementer ===
    // --- Historie Generator Elementer ---
    const generateButton = document.getElementById('generate-button');
    const resetButton = document.getElementById('reset-button'); // Bemærk: Denne er nu inde i story-share-buttons

    const generateImageButton = document.getElementById('generate-image-button');
    const imageSection = document.getElementById('billede-til-historien-sektion');
    const imageLoadingIndicator = document.getElementById('image-loading-indicator');
    const storyImageDisplay = document.getElementById('story-image-display');
    const imageGenerationError = document.getElementById('image-generation-error');
    const storyDisplay = document.getElementById('story-display');
    const storySectionHeading = document.getElementById('story-section-heading'); // Til opdatering af historietitel
    const generatorSection = document.getElementById('generator');
    const laengdeSelect = document.getElementById('laengde-select');
    const moodSelect = document.getElementById('mood-select');

    // Input field containers/specific inputs for historie
    const listenerContainer = document.getElementById('listener-container');
    const addListenerButton = document.getElementById('add-listener-button');
    const karakterContainer = document.getElementById('karakter-container');
    const addKarakterButton = document.getElementById('add-karakter-button');
    const førsteKarakterDescInput = document.getElementById('karakter-desc-1');
    const førsteKarakterNavnInput = document.getElementById('karakter-navn-1');
    const førsteStedInput = document.getElementById('sted-input-1');
    const førstePlotInput = document.getElementById('plot-input-1');
    const stedContainer = document.getElementById('sted-container');
    const plotContainer = document.getElementById('plot-container');
    const negativePromptInput = document.getElementById('negative-prompt-input');
    const interactiveCheckbox = document.getElementById('interactive-checkbox'); // Selvom skjult, behold reference

    // Knapper i generator
    const autofillButton = document.getElementById('autofill-button');
    const readAloudButton = document.getElementById('read-aloud-button');

    // Lyd-elementer for historie
    const audioLoadingDiv = document.getElementById('audio-loading');
    const audioErrorDiv = document.getElementById('audio-error');
    const audioPlayer = document.getElementById('audio-player');
    const loginPromptAudio = document.getElementById('login-prompt-audio'); // For at vise/skjule login prompt for lyd

    // Billed-elementer (hvis de bruges - pt. ikke aktivt)
    // const imageControlsDiv = document.getElementById('image-controls');
    // const generateImageButton = document.getElementById('generate-image-button');
    // const storyImageTag = document.getElementById('story-image');
    // const imageErrorDiv = document.getElementById('image-error');

    // Feedback sektion
    const toggleFeedbackButton = document.getElementById('toggle-feedback-button');
    const feedbackEmbedContainer = document.getElementById('feedback-embed-container');

    // Cookie Consent Banner elementer
    const cookieConsentBanner = document.getElementById('cookie-consent-banner');
    const acceptCookiesButton = document.getElementById('accept-cookies-button');

    // Historie-dele knapper
    const storyShareButtonsContainer = document.getElementById('story-share-buttons');
    const shareStoryFacebookButton = document.getElementById('share-story-facebook-button');
    const copyStoryButton = document.getElementById('copy-story-button');
    // resetButton er allerede defineret, men er en del af denne container nu.

    // --- NYT: Sangtekst Sektion Elementer ---
    const sangDropdown = document.getElementById('sang-dropdown');
    const sangtekstTitel = document.getElementById('sangtekst-titel'); // Overskriften for sangteksten
    const sangtekstVisning = document.getElementById('sangtekst-visning'); // Hvor selve teksten vises
    let allSongsData = []; // Global variabel til at gemme sangdata

    console.log("DOM references obtained for all sections.");

    // === Eksempeldata til Autoudfyld (Historie) ===
    const exampleListeners = [ { name: "Alma", age: "5" }, { name: "Oscar", age: "7" }, { name: "Sofus", age: "3"}, { name: "Mie", age: "6" }, { name: "Noah", age: "4" }, { name: "Freja", age: "8" }, { name: "Viggo", age: "5" } ];
    const exampleCharacters = [ { description: "en drilsk nisse", name: "Pip" }, { description: "en meget søvnig bjørn", name: "" }, { description: "et flyvende tæppe", name: "" }, { description: "en robot der elsker kage", name: "Kaptajn Kiks" }, { description: "en fe der har mistet sin tryllestav", name: "Flora" } ];
    const examplePlaces = [ "i en skov lavet af slik", "på en øde ø med talende papegøjer", "i et omvendt hus hvor alt er på loftet", "på månen hvor ostene gror", "dybt under jorden i en krystalgrotte" ];
    const examplePlots = [ "skulle finde en forsvundet stjerne", "byggede en fantastisk maskine", "holdt en overraskelsesfest", "mødte et dyr de aldrig havde set før", "lærte at trylle med farver", "'at dele er en god ting'", "'man skal være modig'", "'ærlighed varer længst'" ];
    // console.log("Example data for story autofill defined.");


    // === Logik for Cookie Consent Banner ===
    function triggerAnalyticsPageView() {
        if (typeof gtag === 'function') {
            console.log('Analytics: Triggering page_view for path:', window.location.pathname);
            gtag('event', 'page_view', {
                page_path: window.location.pathname,
                page_location: window.location.href,
                page_title: document.title
            });
        } else {
            console.warn('Analytics: gtag function not found. Page_view not sent.');
        }
    }

    if (cookieConsentBanner && acceptCookiesButton) {
        const consentStatus = localStorage.getItem('cookieConsent');
        // console.log('Cookie consent status from localStorage:', consentStatus);
        if (consentStatus === 'accepted') {
            triggerAnalyticsPageView(); // Send page view hvis allerede accepteret
        } else if (consentStatus !== 'rejected') { // Vis kun hvis ikke eksplicit afvist
            cookieConsentBanner.classList.remove('hidden');
        }
        acceptCookiesButton.addEventListener('click', () => {
            localStorage.setItem('cookieConsent', 'accepted');
            cookieConsentBanner.classList.add('hidden');
            triggerAnalyticsPageView(); // Send page view ved accept
            console.log("Cookie consent accepted and banner hidden.");
        });
    } else {
        console.warn('Cookie consent banner or accept button not found in the DOM.');
    }

    // === Hjælpefunktioner (Generelle) ===
    function getRandomElement(arr) {
        if (!arr || arr.length === 0) { console.warn("getRandomElement called with empty or null array"); return null; }
        return arr[Math.floor(Math.random() * arr.length)];
     }

    // === Dynamiske Inputfelter for Historie ===
    function addInputField(containerId, placeholder, inputName) {
        const container = document.getElementById(containerId);
        if (!container) { console.error(`Container med ID '${containerId}' blev ikke fundet.`); return; }
        const inputGroup = document.createElement('div'); inputGroup.className = 'input-group';
        const newInput = document.createElement('input'); newInput.type = 'text'; newInput.name = inputName; newInput.placeholder = placeholder;
        const removeButton = document.createElement('button'); removeButton.type = 'button'; removeButton.textContent = '-'; removeButton.className = 'remove-button';
        removeButton.addEventListener('click', () => { inputGroup.remove(); });
        inputGroup.appendChild(newInput); inputGroup.appendChild(removeButton); container.appendChild(inputGroup);
    }

    let karakterCounter = 1; // Holder styr på unikke ID'er for karakterfelter
    function addCharacterGroup() {
        karakterCounter++;
        const characterGroup = document.createElement('div'); characterGroup.className = 'character-group';
        // Beskrivelsesfelt
        const descPair = document.createElement('div'); descPair.className = 'input-pair';
        const descLabel = document.createElement('label'); descLabel.htmlFor = `karakter-desc-${karakterCounter}`; descLabel.className = 'sr-only'; descLabel.textContent = 'Beskrivelse';
        const descInput = document.createElement('input'); descInput.type = 'text'; descInput.name = 'karakter_desc'; descInput.id = `karakter-desc-${karakterCounter}`; descInput.placeholder = 'Beskrivelse (f.eks. en klog ugle)';
        descPair.appendChild(descLabel); descPair.appendChild(descInput);
        // Navnefelt
        const namePair = document.createElement('div'); namePair.className = 'input-pair';
        const nameLabel = document.createElement('label'); nameLabel.htmlFor = `karakter-navn-${karakterCounter}`; nameLabel.className = 'sr-only'; nameLabel.textContent = 'Navn';
        const nameInput = document.createElement('input'); nameInput.type = 'text'; nameInput.name = 'karakter_navn'; nameInput.id = `karakter-navn-${karakterCounter}`; nameInput.placeholder = 'Navn (valgfrit)';
        namePair.appendChild(nameLabel); namePair.appendChild(nameInput);
        // Fjern-knap
        const removeButton = document.createElement('button'); removeButton.type = 'button'; removeButton.textContent = '-'; removeButton.className = 'remove-button';
        removeButton.addEventListener('click', () => { characterGroup.remove(); });
        // Saml gruppen
        characterGroup.appendChild(descPair); characterGroup.appendChild(namePair); characterGroup.appendChild(removeButton);
        if (karakterContainer) {
             karakterContainer.appendChild(characterGroup);
        } else { console.error("Karakter container (#karakter-container) not found for adding new group.");}
    }

    let listenerCounter = 1; // Holder styr på unikke ID'er for lytterfelter
    function addListenerGroup() {
        listenerCounter++;
        const listenerGroup = document.createElement('div'); listenerGroup.className = 'listener-group';
        // Navnefelt
        const namePair = document.createElement('div'); namePair.className = 'input-pair';
        const nameLabel = document.createElement('label'); nameLabel.htmlFor = `listener-name-${listenerCounter}`; nameLabel.className = 'sr-only'; nameLabel.textContent = 'Navn';
        const nameInput = document.createElement('input'); nameInput.type = 'text'; nameInput.name = 'listener_name_single'; nameInput.id = `listener-name-${listenerCounter}`; nameInput.placeholder = 'Barnets Navn';
        namePair.appendChild(nameLabel); namePair.appendChild(nameInput);
        // Alderfelt
        const agePair = document.createElement('div'); agePair.className = 'input-pair';
        const ageLabel = document.createElement('label'); ageLabel.htmlFor = `listener-age-${listenerCounter}`; ageLabel.className = 'sr-only'; ageLabel.textContent = 'Alder';
        const ageInput = document.createElement('input'); ageInput.type = 'text'; ageInput.name = 'listener_age_single'; ageInput.id = `listener-age-${listenerCounter}`; ageInput.placeholder = 'Alder (f.eks. 5)';
        agePair.appendChild(ageLabel); agePair.appendChild(ageInput);
        // Fjern-knap
        const removeButton = document.createElement('button'); removeButton.type = 'button'; removeButton.textContent = '-'; removeButton.className = 'remove-button';
        removeButton.addEventListener('click', () => {
            listenerGroup.remove();
            saveCurrentListeners(); // Gem efter fjernelse
        });
        // Saml gruppen
        listenerGroup.appendChild(namePair); listenerGroup.appendChild(agePair); listenerGroup.appendChild(removeButton);
        if (listenerContainer) {
             listenerContainer.appendChild(listenerGroup);
        } else { console.error("Listener container (#listener-container) not found for adding new group.");}
        return listenerGroup; // Returner gruppen så den kan bruges af loadAndDisplaySavedListeners
    }

    // === LocalStorage for Lyttere ===
    function saveCurrentListeners() {
        // console.log("Attempting to save listeners to LocalStorage...");
        const currentListeners = [];
        if (!listenerContainer) { console.error("Cannot save listeners: Listener container not found."); return; }
        listenerContainer.querySelectorAll('.listener-group').forEach(group => {
            const nameInput = group.querySelector('input[name="listener_name_single"]');
            const ageInput = group.querySelector('input[name="listener_age_single"]');
            const name = nameInput ? nameInput.value.trim() : '';
            const age = ageInput ? ageInput.value.trim() : '';
            if (name || age) { // Gem kun hvis mindst et felt er udfyldt
                currentListeners.push({ name: name, age: age });
            }
        });
        try {
            if (currentListeners.length > 0) {
                localStorage.setItem('savedListeners', JSON.stringify(currentListeners));
                // console.log("Listeners saved to LocalStorage:", JSON.stringify(currentListeners));
            } else {
                localStorage.removeItem('savedListeners'); // Fjern hvis ingen lyttere er tilbage
                // console.log("No listener data to save; removed saved listeners from LocalStorage.");
            }
        } catch (e) { console.error("Error saving listeners to LocalStorage:", e); }
    }

    function loadAndDisplaySavedListeners() {
        // console.log("Attempting to load listeners from LocalStorage...");
        const savedListenersJSON = localStorage.getItem('savedListeners');
        if (savedListenersJSON) {
            // console.log("Found saved listeners in LocalStorage:", savedListenersJSON);
            try {
                const savedListeners = JSON.parse(savedListenersJSON);
                if (Array.isArray(savedListeners) && savedListeners.length > 0) {
                    if (!listenerContainer) { console.error("Cannot display listeners: Listener container not found."); return false; }

                    // Ryd eksisterende lytter-grupper udover den første
                    const existingGroups = listenerContainer.querySelectorAll('.listener-group');
                    for (let i = existingGroups.length - 1; i > 0; i--) {
                        existingGroups[i].remove();
                    }

                    // Udfyld den første (statiske) gruppe
                    const firstGroup = listenerContainer.querySelector('.listener-group'); // Skulle altid være der
                    if (!firstGroup) {
                        console.error("Initial listener group not found for loading! This should not happen.");
                        return false;
                    }
                    const firstListenerNameInput = firstGroup.querySelector('input[name="listener_name_single"]');
                    const firstListenerAgeInput = firstGroup.querySelector('input[name="listener_age_single"]');

                    if(firstListenerNameInput) firstListenerNameInput.value = savedListeners[0].name || '';
                    if(firstListenerAgeInput) firstListenerAgeInput.value = savedListeners[0].age || '';
                    // console.log("Populated first listener group with:", savedListeners[0]);

                    // Tilføj og udfyld yderligere grupper hvis der er flere gemte lyttere
                    if (savedListeners.length > 1) {
                        for (let i = 1; i < savedListeners.length; i++) {
                            const listenerData = savedListeners[i];
                            const newGroup = addListenerGroup(); // addListenerGroup tilføjer selv til DOM
                            if (newGroup) { // Sikrer at gruppen blev oprettet
                                const newNameInput = newGroup.querySelector('input[name="listener_name_single"]');
                                const newAgeInput = newGroup.querySelector('input[name="listener_age_single"]');
                                if(newNameInput) newNameInput.value = listenerData.name || '';
                                if(newAgeInput) newAgeInput.value = listenerData.age || '';
                                // console.log(`Added and populated listener group ${i+1} with:`, listenerData);
                            }
                        }
                    }
                    // console.log("Finished loading and displaying listeners.");
                    return true; // Indikerer at lyttere blev loadet
                }
            } catch (e) {
                console.error("Error parsing saved listeners from LocalStorage:", e);
                localStorage.removeItem('savedListeners'); // Ryd ugyldige data
            }
        } else {
            // console.log("No saved listeners found in LocalStorage.");
        }
        return false; // Indikerer at ingen lyttere blev loadet
    }

    // === Autoudfyld for Historie ===
     function autofillFields() {
        console.log("Autofill: Started");
        // Nulstil først alle felter (inkl. fjernelse af ekstra grupper og lyttere)
        try {
             handleResetClick(false); // false for ikke at rydde LocalStorage for lyttere under autofill
             console.log("Autofill: handleResetClick(false) completed.");
        } catch(e) {
            console.error("Autofill: Error during handleResetClick:", e);
        }

        // Udfyld lytter (den første gruppe)
        const randomListener = getRandomElement(exampleListeners);
        if (randomListener && listenerContainer) {
            const firstListenerNameInput = listenerContainer.querySelector('#listener-name-1');
            const firstListenerAgeInput = listenerContainer.querySelector('#listener-age-1');
            if (firstListenerNameInput) firstListenerNameInput.value = randomListener.name;
            if (firstListenerAgeInput) firstListenerAgeInput.value = randomListener.age;
        }

        // Udfyld karakter (den første gruppe)
        const randomCharacter = getRandomElement(exampleCharacters);
        if (randomCharacter && karakterContainer) {
            const firstCharDescInput = karakterContainer.querySelector('#karakter-desc-1');
            const firstCharNameInput = karakterContainer.querySelector('#karakter-navn-1');
            if (firstCharDescInput) firstCharDescInput.value = randomCharacter.description;
            if (firstCharNameInput) firstCharNameInput.value = randomCharacter.name;
        }

        // Udfyld sted (det første input)
        const randomPlace = getRandomElement(examplePlaces);
        const firstStedInputElem = document.querySelector('#sted-container input[name="sted"]');
        if (randomPlace && firstStedInputElem) {
            firstStedInputElem.value = randomPlace;
        }

        // Udfyld plot (det første input)
        const randomPlot = getRandomElement(examplePlots);
        const firstPlotInputElem = document.querySelector('#plot-container input[name="plot"]');
        if (randomPlot && firstPlotInputElem) {
            firstPlotInputElem.value = randomPlot;
        }

        if(negativePromptInput) negativePromptInput.value = ''; // Sørg for at negativ prompt er ryddet
        console.log("Autofill: Fields populated.");
    }

    // === Feedback Sektion Toggle ===
    function toggleFeedbackEmbed() {
        if (feedbackEmbedContainer) {
            feedbackEmbedContainer.classList.toggle('hidden');
            // console.log("Feedback embed toggled. Is hidden:", feedbackEmbedContainer.classList.contains('hidden'));
        } else {
            console.error("Feedback embed container (#feedback-embed-container) not found!");
        }
    }

    // === Historie Generering & Håndtering ===
    function getStoryInputsForSharing() { // Bruges til Facebook deling og kopiering
        const inputs = {
            titel: "Jeres historie", // Default titel hvis ingen er genereret
            karakterBeskrivelse: '',
            karakterNavn: '',
            sted: '',
            plot: '',
            stemning: ''
        };

        // Hent den aktuelle titel fra h2-elementet
        if (storySectionHeading && storySectionHeading.textContent !== "Jeres historie" && storySectionHeading.textContent.trim() !== "") {
            inputs.titel = storySectionHeading.textContent.trim();
        }

        if (førsteKarakterDescInput) inputs.karakterBeskrivelse = førsteKarakterDescInput.value.trim();
        if (førsteKarakterNavnInput && førsteKarakterNavnInput.value.trim()) inputs.karakterNavn = førsteKarakterNavnInput.value.trim();
        if (førsteStedInput) inputs.sted = førsteStedInput.value.trim();
        if (førstePlotInput) inputs.plot = førstePlotInput.value.trim();
        if (moodSelect && moodSelect.selectedIndex >= 0) inputs.stemning = moodSelect.options[moodSelect.selectedIndex].text;

        return inputs;
    }

    async function handleGenerateClick(event) {
        event.preventDefault();
        console.log("Story Generation: Started");

        // Indsaml data fra inputfelter
        const karakterer = [];
        if(karakterContainer) { karakterContainer.querySelectorAll('.character-group').forEach(group => { const descInput = group.querySelector('input[name="karakter_desc"]'); const nameInput = group.querySelector('input[name="karakter_navn"]'); const description = descInput ? descInput.value.trim() : ''; const name = nameInput ? nameInput.value.trim() : ''; if (description) { karakterer.push({ description: description, name: name }); } }); }
        const steder = []; document.querySelectorAll('#sted-container .input-group input[name="sted"]').forEach(input => { const v = input.value.trim(); if(v) steder.push(v); });
        const plots = []; document.querySelectorAll('#plot-container .input-group input[name="plot"]').forEach(input => { const v = input.value.trim(); if(v) plots.push(v); });
        const listeners = [];
        if(listenerContainer) { listenerContainer.querySelectorAll('.listener-group').forEach(group => { const nameInput = group.querySelector('input[name="listener_name_single"]'); const ageInput = group.querySelector('input[name="listener_age_single"]'); const name = nameInput ? nameInput.value.trim() : ''; const age = ageInput ? ageInput.value.trim() : ''; if (name || age) { listeners.push({ name: name, age: age }); } }); }

        const selectedLaengde = laengdeSelect ? laengdeSelect.value : 'kort';
        const selectedMoodValue = moodSelect ? moodSelect.value : 'neutral';
        const isInteractive = interactiveCheckbox ? interactiveCheckbox.checked : false; // Selvom skjult, læs værdien
        const negativePromptText = negativePromptInput ? negativePromptInput.value.trim() : '';

        saveCurrentListeners(); // Gem lytter-data før API kald
        const dataToSend = { karakterer, steder, plots, laengde: selectedLaengde, mood: selectedMoodValue, listeners, interactive: isInteractive, negative_prompt: negativePromptText };
        // console.log("Story Generation: Data prepared for sending to /generate:", dataToSend);

        // UI Opdatering: Loading State
        if(generateButton) { generateButton.disabled = true; generateButton.textContent = 'Laver historie...'; }
        if(storyDisplay) storyDisplay.textContent = 'Historien genereres... Vent venligst.';
        if(storySectionHeading) storySectionHeading.textContent = 'Jeres historie'; // Nulstil titel
        if(resetButton && storyShareButtonsContainer) storyShareButtonsContainer.querySelector('#reset-button').style.display = 'none'; // Skjul reset knap i dele-container
        if (storyShareButtonsContainer) storyShareButtonsContainer.classList.add('hidden');

        // Nulstil lyd/billede elementer
        if(audioPlayer) { audioPlayer.pause(); audioPlayer.src = ''; audioPlayer.classList.add('hidden'); }
        if(audioLoadingDiv) audioLoadingDiv.classList.add('hidden');
        if(audioErrorDiv) { audioErrorDiv.textContent = ''; audioErrorDiv.classList.add('hidden'); }
        if(loginPromptAudio) loginPromptAudio.classList.add('hidden');
        // Nulstil evt. billeder her hvis relevant

        try {
            // console.log("Story Generation: Initiating fetch call to /generate...");
            const response = await fetch('/generate', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(dataToSend) });
            // console.log("Story Generation: Fetch response received. Status:", response.status);

            if (!response.ok) {
                 let errorMsg = `Serverfejl (${response.status})`;
                 try { const errorData = await response.json(); errorMsg = errorData.error || errorData.story || `${errorMsg} ${response.statusText}`; } catch (e) { errorMsg += ` ${response.statusText || await response.text()}`; }
                 throw new Error(errorMsg);
            }
            const result = await response.json();
            // console.log("Story Generation: JSON parsed successfully:", result);

            if(storyDisplay) storyDisplay.textContent = result.story || "Modtog en tom historie fra serveren.";
            if(storySectionHeading) storySectionHeading.textContent = result.title || "Jeres historie"; // Opdater med titel fra backend

            if(resetButton && storyShareButtonsContainer) storyShareButtonsContainer.querySelector('#reset-button').style.display = 'inline-block'; // Vis reset knap igen
            if (storyShareButtonsContainer && result.story && result.story.trim() !== "") {
                storyShareButtonsContainer.classList.remove('hidden');
            }

            // NY KODE (uden login tjek for billedknap)
            if (result.story && result.story.trim() !== "" && generateImageButton) {
                generateImageButton.disabled = false; // Aktiver altid knappen hvis der er en historie
                generateImageButton.removeAttribute('title'); // Fjern evt. gammel title-attribut
                console.log("Generer Billede knap aktiveret.");
            } else if (generateImageButton) {
                generateImageButton.disabled = true;
            }

        } catch (error) {
             console.error('Story Generation: Error during generation (catch block):', error);
             if(storyDisplay) storyDisplay.textContent = `Ups! Noget gik galt: ${error.message}. Prøv igen.`;
             if(storySectionHeading) storySectionHeading.textContent = "Fejl ved generering";
             if(resetButton && storyShareButtonsContainer) storyShareButtonsContainer.querySelector('#reset-button').style.display = 'inline-block';
        } finally {
             // console.log("Story Generation: Executing finally block...");
             if(generateButton) { generateButton.disabled = false; generateButton.textContent = 'Skab Historie'; }
             // console.log("Story Generation: Loading state removed.");
        }
        console.log("Story Generation: Finished");
    }

    // === Lyd Generering (TTS) ===
    async function handleReadAloudClick() {
        console.log("Read Aloud: Started");

        if (!readAloudButton.classList.contains('disabled-button')) { // Tjek om knappen er aktiv (bruger logget ind)
            if (!storyDisplay || !storyDisplay.textContent || storyDisplay.textContent.trim() === '' || storyDisplay.textContent.includes('Historien genereres...') || storyDisplay.textContent.includes('Ups!')) {
                console.warn("Read Aloud: No valid story text found.");
                if(audioErrorDiv) {
                    audioErrorDiv.textContent = "Ingen historie at læse højt.";
                    audioErrorDiv.classList.remove('hidden');
                    setTimeout(() => audioErrorDiv.classList.add('hidden'), 3000);
                }
                return;
            }

            if (!audioLoadingDiv || !audioErrorDiv || !audioPlayer) {
                 console.error("Read Aloud: Critical audio elements missing from DOM.");
                 if(audioErrorDiv) { audioErrorDiv.textContent = "Fejl: Lyd-elementer mangler (kontakt support)."; audioErrorDiv.classList.remove('hidden'); }
                 return;
            }

            const storyText = storyDisplay.textContent;

            // UI Opdatering: Loading State for lyd
            if(audioLoadingDiv) audioLoadingDiv.classList.remove('hidden');
            if(audioErrorDiv) { audioErrorDiv.textContent = ''; audioErrorDiv.classList.add('hidden');}
            if(audioPlayer) { audioPlayer.pause(); audioPlayer.src = ''; audioPlayer.classList.add('hidden');}
            if(readAloudButton) { readAloudButton.disabled = true; readAloudButton.textContent = 'Genererer Lyd...'; }

            try {
                // console.log("Read Aloud: Initiating fetch call to /generate_audio...");
                const response = await fetch('/generate_audio', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text: storyText }) });
                // console.log("Read Aloud: Fetch response received for audio. Status:", response.status);

                if (!response.ok) {
                    let errorMsg = `Serverfejl (${response.status})`;
                    try { const errorData = await response.json(); errorMsg = errorData.error || `${errorMsg} ${response.statusText}`; } catch (e) { errorMsg += ` ${response.statusText}`; }
                    throw new Error(errorMsg);
                }
                const contentType = response.headers.get("content-type");
                if (!contentType || !contentType.includes("audio/mpeg")) {
                     throw new Error(`Uventet svar fra server (type: ${contentType}). Forventede lydfil.`);
                }
                // console.log("Read Aloud: Audio data received. Creating Blob URL...");
                const audioBlob = await response.blob();
                const audioUrl = URL.createObjectURL(audioBlob);
                if(audioPlayer) {
                    audioPlayer.src = audioUrl;
                    audioPlayer.classList.remove('hidden');
                    // console.log("Read Aloud: Audio player ready with new audio.");
                } else {
                     console.error("Read Aloud: Audio player element not found when trying to set source!");
                     throw new Error("Intern fejl: Lyd-afspiller element ikke fundet.");
                }
            } catch (error) {
                console.error("Read Aloud: Error during audio generation:", error);
                if(audioErrorDiv) {
                    audioErrorDiv.textContent = `Lydfejl: ${error.message}`;
                    audioErrorDiv.classList.remove('hidden');
                }
                if(audioPlayer) audioPlayer.classList.add('hidden');
            } finally {
                if(audioLoadingDiv) audioLoadingDiv.classList.add('hidden');
                if(readAloudButton) {
                    readAloudButton.disabled = false;
                    readAloudButton.textContent = 'Læs Historien Højt';
                }
                // console.log("Read Aloud: Finished processing.");
            }
        } else {
            console.log("Read Aloud: Button is disabled (user likely not logged in).");
            if (loginPromptAudio) { // Vis prompt hvis knappen er deaktiveret
                loginPromptAudio.classList.remove('hidden');
                setTimeout(() => loginPromptAudio.classList.add('hidden'), 5000); // Skjul efter 5 sek
            }
        }
    }

async function handleGenerateImageFromStoryClick() { // Bemærk navnet
    console.log("--> handleGenerateImageFromStoryClick startet");

    // Sørg for at disse referencer er defineret øverst i din script.js fil:
    // const storyDisplay = document.getElementById('story-display');
    // const imageSection = document.getElementById('billede-til-historien-sektion');
    // const imageLoadingIndicator = document.getElementById('image-loading-indicator');
    // const storyImageDisplay = document.getElementById('story-image-display');
    // const imageGenerationError = document.getElementById('image-generation-error');
    // const generateImageButton = document.getElementById('generate-image-button');

    if (!storyDisplay || !storyDisplay.textContent.trim()) {
        // Vis en mere brugervenlig besked, hvis muligt, i stedet for alert
        if(imageGenerationError) {
            imageGenerationError.textContent = "Generer venligst en historie først, før du prøver at lave et billede.";
            if(imageSection) imageSection.classList.remove('hidden'); // Vis sektionen for at vise fejlen
            imageGenerationError.classList.remove('hidden');
        } else {
            alert("Generer venligst en historie først, før du prøver at lave et billede.");
        }
        return;
    }

    const currentStoryText = storyDisplay.textContent.trim();

    // Vis UI elementer for billedgenerering
    if (imageSection) imageSection.classList.remove('hidden');
    if (imageLoadingIndicator) imageLoadingIndicator.classList.remove('hidden');
    if (storyImageDisplay) {
        storyImageDisplay.classList.add('hidden'); // Skjul evt. gammelt billede
        storyImageDisplay.src = '#';
    }
    if (imageGenerationError) {
        imageGenerationError.textContent = ''; // Ryd gamle fejl
        imageGenerationError.classList.add('hidden'); // Skjul fejlbesked initialt
    }
    if (generateImageButton) generateImageButton.disabled = true; // Deaktiver knap under kørsel

    try {
        console.log("Sender historietekst til /generate_image_from_story");
        const response = await fetch('/generate_image_from_story', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ story_text: currentStoryText })
        });

        // Vi fjerner det specifikke 401 tjek her, da login ikke er påkrævet for nu
        // if (response.status === 401) {
        //      throw new Error("Login er påkrævet, eller din session er udløbet. Log venligst ind igen.");
        // }

        if (!response.ok) { // Håndterer alle andre HTTP fejl (400, 500, etc.)
            let errorMsg = `Serverfejl (${response.status})`;
            try {
                const errorData = await response.json();
                errorMsg = errorData.error || `${errorMsg} ${response.statusText || 'Ukendt serverfejl'}`;
            } catch (e) {
                const textError = await response.text();
                errorMsg += `. Server respons: ${textError || '(tom respons)'}`;
            }
            throw new Error(errorMsg);
        }

        const result = await response.json();
        console.log("Svar fra /generate_image_from_story:", result);

        if (result.image_url) {
            if (storyImageDisplay) {
                storyImageDisplay.src = result.image_url;
                storyImageDisplay.classList.remove('hidden');
            }
        } else if (result.message && result.status === "Under udvikling") {
            if (imageGenerationError) {
                imageGenerationError.textContent = result.message; // Viser kun hovedbeskeden fra backend
                imageGenerationError.classList.remove('hidden');
            }
            console.log("Billedgenerering er under udvikling, som forventet fra stub.");
        } else if (result.error) {
            throw new Error(result.error);
        } else {
            throw new Error("Uventet svar fra serveren under billedgenerering.");
        }

    } catch (error) {
        console.error("Fejl under billedgenerering (catch):", error);
        if (imageGenerationError) {
            imageGenerationError.textContent = `Fejl: ${error.message}`;
            imageGenerationError.classList.remove('hidden');
        }
        if (storyImageDisplay) storyImageDisplay.classList.add('hidden');
    } finally {
        if (imageLoadingIndicator) imageLoadingIndicator.classList.add('hidden');
        if (generateImageButton) generateImageButton.disabled = false;
        console.log("--> handleGenerateImageFromStoryClick færdig");
    }
}

    // === Nulstil Funktion (Reset) ===
    function handleResetClick(clearLocalStorageForListeners = true) {
        console.log("Reset: Started. Clear LocalStorage for listeners:", clearLocalStorageForListeners);
        if(generatorSection) {
            generatorSection.querySelectorAll('input[type="text"], textarea').forEach(input => {
                // Tjek om inputtet er inde i listener-containeren
                if (!input.closest('#listener-container')) {
                    input.value = ''; // Ryd kun hvis det IKKE er et lytter-input
                }
            });
        }
        if(interactiveCheckbox) interactiveCheckbox.checked = false;
        // console.log("Reset: Cleared text inputs and textarea.");

        const removeExtraGroups = (containerId, groupSelector) => {
            const container = document.getElementById(containerId);
            if (container) {
                const groups = container.querySelectorAll(groupSelector);
                for (let i = groups.length - 1; i > 0; i--) { groups[i].remove(); }
            }
        };
       if (clearLocalStorageForListeners) { // Kun fjern ekstra lytter-grupper hvis vi laver et "fuldt" reset
            removeExtraGroups('listener-container', '.listener-group');
        }
        removeExtraGroups('karakter-container', '.character-group');
        removeExtraGroups('sted-container', '.input-group');
        removeExtraGroups('plot-container', '.input-group');
        // console.log("Reset: Removed extra dynamic groups.");

        if(storyDisplay) storyDisplay.textContent = '';
        if(storySectionHeading) storySectionHeading.textContent = 'Jeres historie'; // Nulstil titel
        if(resetButton && storyShareButtonsContainer) storyShareButtonsContainer.querySelector('#reset-button').style.display = 'none';
        if (storyShareButtonsContainer) storyShareButtonsContainer.classList.add('hidden');

        // Nulstil lyd/billede
        if(audioPlayer) { audioPlayer.pause(); audioPlayer.src = ''; audioPlayer.classList.add('hidden'); }
        if(audioLoadingDiv) audioLoadingDiv.classList.add('hidden');
        if(audioErrorDiv) { audioErrorDiv.textContent = ''; audioErrorDiv.classList.add('hidden'); }
        if(loginPromptAudio) loginPromptAudio.classList.add('hidden');

        if(laengdeSelect) laengdeSelect.value = 'kort';
        if(moodSelect) moodSelect.value = 'neutral';
        // console.log("Reset: Dropdowns reset.");

        if (clearLocalStorageForListeners) {
            try {
                localStorage.removeItem('savedListeners');
                console.log("Reset: Removed saved listeners from LocalStorage.");
            } catch (e) {
                console.error("Reset: Error removing listeners from LocalStorage:", e);
            }
        } else {
            // console.log("Reset: Skipped clearing LocalStorage for listeners (likely due to autofill).");
        }
        console.log("Reset: Finished.");
    }


    // === Historie Dele Funktioner ===
    if (shareStoryFacebookButton) {
        shareStoryFacebookButton.addEventListener('click', () => {
            const storyData = getStoryInputsForSharing(); // Henter titel, inputs etc.
            const storyText = storyDisplay.textContent || "";
            const appURL = window.location.origin; // F.eks. "https://readmeastory.dk"

            let quoteParts = [];
            quoteParts.push(`Jeg har lige lavet en historie: "${storyData.titel}"`);
            if (storyData.karakterBeskrivelse) {
                let karakter = storyData.karakterBeskrivelse;
                if (storyData.karakterNavn) karakter += ` ved navn ${storyData.karakterNavn}`;
                quoteParts.push(`Hovedperson: ${karakter}.`);
            }
            if (storyData.sted) quoteParts.push(`Sted: ${storyData.sted}.`);
            // Begræns længden af uddrag for Facebook
            const snippet = storyText.substring(0, 120) + (storyText.length > 120 ? "..." : "");
            if (snippet) quoteParts.push(`Uddrag: "${snippet}"`);
            quoteParts.push(`Prøv selv på Read Me A Story!`);

            const quote = encodeURIComponent(quoteParts.join(' '));
            const encodedAppURL = encodeURIComponent(appURL);
            const facebookShareURL = `https://www.facebook.com/sharer/sharer.php?u=${encodedAppURL}&quote=${quote}&hashtag=%23ReadMeAStory`;

            // console.log("Sharing to Facebook. URL:", facebookShareURL);
            // console.log("Decoded Quote:", decodeURIComponent(quote));
            window.open(facebookShareURL, '_blank', 'width=600,height=400,noopener,noreferrer');
        });
    }

    if (copyStoryButton) {
        copyStoryButton.addEventListener('click', async () => {
            const storyData = getStoryInputsForSharing();
            const storyText = storyDisplay.textContent || "";
            const appURL = window.location.origin;

            let textToCopyParts = [`Min Godnathistorie: "${storyData.titel}"`, "---"];
            if (storyData.karakterBeskrivelse) {
                let karakter = storyData.karakterBeskrivelse;
                if (storyData.karakterNavn) karakter += ` ved navn ${storyData.karakterNavn}`;
                textToCopyParts.push(`Hovedperson: ${karakter}`);
            }
            if (storyData.sted) textToCopyParts.push(`Sted: ${storyData.sted}`);
            if (storyData.plot) textToCopyParts.push(`Plot/Morale: ${storyData.plot}`);
            if (storyData.stemning && storyData.stemning !== "Neutral / Blandet") textToCopyParts.push(`Stemning: ${storyData.stemning}`);
            textToCopyParts.push("---");

            if (storyText) {
                textToCopyParts.push("Historie:");
                textToCopyParts.push(storyText);
            }
            textToCopyParts.push("---");
            textToCopyParts.push(`Skabt med Read Me A Story (${appURL})`);

            const textToCopy = textToCopyParts.join('\n\n'); // Dobbelt linjeskift mellem sektioner

            try {
                await navigator.clipboard.writeText(textToCopy);
                const originalText = copyStoryButton.textContent;
                copyStoryButton.textContent = 'Kopieret!';
                copyStoryButton.disabled = true;
                setTimeout(() => {
                    copyStoryButton.textContent = originalText;
                    copyStoryButton.disabled = false;
                }, 2000);
                // console.log('Story copied to clipboard');
            } catch (err) {
                console.error('Failed to copy story to clipboard: ', err);
                // Overvej en mere brugervenlig fejlmeddelelse her, f.eks. en lille popup/modal
                alert('Kunne ikke kopiere automatisk. Prøv evt. at markere og kopiere teksten manuelt.');
            }
        });
    }

    // === NYT: Sangtekst Funktionalitet ===
    async function loadSongs() {
        console.log("Songs: Attempting to load songs.json...");
        if (!sangDropdown || !sangtekstVisning || !sangtekstTitel) {
            console.error("Songs: Dropdown or display elements for songs not found in DOM.");
            return;
        }
        try {
            const response = await fetch('static/songs.json'); // Stien er relativ til HTML-filens placering
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status} when fetching songs.json`);
            }
            allSongsData = await response.json();
            // console.log("Songs: songs.json loaded and parsed:", allSongsData);
            populateSongDropdown();
        } catch (error) {
            console.error("Songs: Failed to load or parse songs.json:", error);
            if (sangDropdown) sangDropdown.innerHTML = '<option value="">Kunne ikke hente sange</option>';
            if (sangtekstVisning) sangtekstVisning.textContent = "Fejl: Kunne ikke indlæse sanglisten. Prøv at genindlæse siden.";
        }
    }

    function populateSongDropdown() {
        // console.log("Songs: Populating dropdown.");
        if (!sangDropdown || !allSongsData.length) {
            // console.log("Songs: Dropdown element not found or no song data to populate.");
            return;
        }
        // Behold den første "-- Vælg en sang --" option
        sangDropdown.innerHTML = '<option value="">-- Vælg en sang --</option>';

        allSongsData.forEach((song, index) => {
            const option = document.createElement('option');
            option.value = index; // Brug index som værdi for nemmere opslag
            option.textContent = song.title;
            sangDropdown.appendChild(option);
        });
        // console.log("Songs: Dropdown populated.");
    }

    function displaySelectedSong() {
        // console.log("Songs: Dropdown selection changed.");
        if (!sangDropdown || !sangtekstVisning || !sangtekstTitel) {
            console.error("Songs: Cannot display song, critical elements missing.");
            return;
        }

        const selectedIndex = sangDropdown.value;
        if (selectedIndex === "" || !allSongsData[selectedIndex]) { // Hvis "-- Vælg en sang --" er valgt eller index er ugyldigt
            sangtekstTitel.textContent = "Sangtekst:";
            sangtekstVisning.textContent = "Vælg en sang fra listen ovenfor for at se teksten her.";
            // console.log("Songs: No song selected or invalid index.");
        } else {
            const selectedSong = allSongsData[selectedIndex];
            sangtekstTitel.textContent = `Sangtekst: ${selectedSong.title}`;
            sangtekstVisning.textContent = selectedSong.lyrics; // \n vil blive respekteret pga. white-space: pre-wrap;
            // console.log(`Songs: Displaying lyrics for "${selectedSong.title}"`);
        }
    }


    // === Tilknyt Event Listeners ===
    // Indlæs gemte lyttere for historie-sektionen
    loadAndDisplaySavedListeners();

    // Historie-generator knapper
    if (generateButton) { generateButton.addEventListener('click', handleGenerateClick); } else { console.error("Generate button (#generate-button) not found!"); }
    if (resetButton && storyShareButtonsContainer) { // Sikrer at reset knappen findes i containeren
        storyShareButtonsContainer.querySelector('#reset-button').addEventListener('click', () => handleResetClick(false));
    } else { console.error("Reset button (inside #story-share-buttons) not found!"); }

    if (autofillButton) { autofillButton.addEventListener('click', autofillFields); } else { console.error("Autofill button (#autofill-button) not found!"); }
    if (addListenerButton) { addListenerButton.addEventListener('click', addListenerGroup); } else { console.error("Add listener button (#add-listener-button) not found!"); }
    if (addKarakterButton) { addKarakterButton.addEventListener('click', addCharacterGroup); } else { console.error("Add character button (#add-karakter-button) not found!"); }
    if (readAloudButton) { readAloudButton.addEventListener('click', handleReadAloudClick); } else { console.info("Read Aloud button (#read-aloud-button) not found or user not authenticated."); }
    if (toggleFeedbackButton) { toggleFeedbackButton.addEventListener('click', toggleFeedbackEmbed); } else { console.error("Toggle feedback button (#toggle-feedback-button) not found!"); }
    if (generateImageButton) {
        generateImageButton.addEventListener('click', handleGenerateImageFromStoryClick); // Sørg for det er det korrekte nye funktionsnavn
    } else {
        console.warn("Knappen 'generate-image-button' blev ikke fundet for event listener.");
    }

    // Generiske "Tilføj felt" knapper for historie (sted, plot)
    document.querySelectorAll('.add-button[data-container]').forEach(button => {
        button.addEventListener('click', () => {
            const containerId = button.dataset.container;
            const placeholder = button.dataset.placeholder;
            const inputName = button.dataset.name;
            if(containerId && placeholder && inputName) {
                addInputField(containerId, placeholder, inputName);
            } else {
                // console.warn("Generic add button is missing data attributes:", button);
            }
        });
    });

    // === NYT: Event Listener og initialisering for Sangtekster ===
    if (sangDropdown) {
        sangDropdown.addEventListener('change', displaySelectedSong);
        loadSongs(); // Hent og populér sange ved sideindlæsning
    } else {
        console.error("Song dropdown (#sang-dropdown) not found. Song functionality will not be initialized.");
    }

    console.log("Script loaded and all initial event listeners attached.");

});
// Slut på DOMContentLoaded listener
