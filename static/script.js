// Kør først koden, når hele HTML dokumentet er færdigindlæst og klar
document.addEventListener('DOMContentLoaded', () => {
    console.log("DOMContentLoaded event fired.");

    // === Hent referencer til HTML elementer ===
    const generateButton = document.getElementById('generate-button');
    const resetButton = document.getElementById('reset-button');
    const storyDisplay = document.getElementById('story-display');
    const generatorSection = document.getElementById('generator');
    const laengdeSelect = document.getElementById('laengde-select');
    const moodSelect = document.getElementById('mood-select');

    // Input field containers/specific inputs
    const listenerContainer = document.getElementById('listener-container');
    const addListenerButton = document.getElementById('add-listener-button');
    const karakterContainer = document.getElementById('karakter-container');
    const addKarakterButton = document.getElementById('add-karakter-button');
    // IDs for nemmere adgang til de første inputfelter for deling:
    const førsteKarakterDescInput = document.getElementById('karakter-desc-1');
    const førsteKarakterNavnInput = document.getElementById('karakter-navn-1');
    const førsteStedInput = document.getElementById('sted-input-1');
    const førstePlotInput = document.getElementById('plot-input-1');

    const stedContainer = document.getElementById('sted-container');
    const plotContainer = document.getElementById('plot-container');

    const interactiveCheckbox = document.getElementById('interactive-checkbox');
    const autofillButton = document.getElementById('autofill-button');
    const toggleFeedbackButton = document.getElementById('toggle-feedback-button');
    const feedbackEmbedContainer = document.getElementById('feedback-embed-container');
    const negativePromptInput = document.getElementById('negative-prompt-input');

    // Lyd-elementer
    const readAloudButton = document.getElementById('read-aloud-button');
    const audioLoadingDiv = document.getElementById('audio-loading');
    const audioErrorDiv = document.getElementById('audio-error');
    const audioPlayer = document.getElementById('audio-player');

    // Billed-elementer (hvis de bruges)
    const imageControlsDiv = document.getElementById('image-controls');
    const generateImageButton = document.getElementById('generate-image-button'); // Selvom ikke fuldt implementeret, behold reference
    const storyImageTag = document.getElementById('story-image');
    const imageErrorDiv = document.getElementById('image-error');


    // Cookie Consent Banner elementer
    const cookieConsentBanner = document.getElementById('cookie-consent-banner');
    const acceptCookiesButton = document.getElementById('accept-cookies-button');

    // Historie-dele knapper
    const storyShareButtonsContainer = document.getElementById('story-share-buttons');
    const shareStoryFacebookButton = document.getElementById('share-story-facebook-button');
    const copyStoryButton = document.getElementById('copy-story-button');

    console.log("DOM references obtained.");

    // === Eksempeldata til Autoudfyld ===
    const exampleListeners = [ { name: "Alma", age: "5" }, { name: "Oscar", age: "7" }, { name: "Sofus", age: "3"}, { name: "Luna", age: "6" }, { name: "Noah", age: "4" }, { name: "Freja", age: "8" }, { name: "Viggo", age: "5" } ];
    const exampleCharacters = [ { description: "en drilsk nisse", name: "Pip" }, { description: "en meget søvnig bjørn", name: "" }, { description: "et flyvende tæppe", name: "" }, { description: "en robot der elsker kage", name: "Kaptajn Kiks" }, { description: "en fe der har mistet sin tryllestav", name: "Flora" } ];
    const examplePlaces = [ "i en skov lavet af slik", "på en øde ø med talende papegøjer", "i et omvendt hus hvor alt er på loftet", "på månen hvor ostene gror", "dybt under jorden i en krystalgrotte" ];
    const examplePlots = [ "skulle finde en forsvundet stjerne", "byggede en fantastisk maskine", "holdt en overraskelsesfest", "mødte et dyr de aldrig havde set før", "lærte at trylle med farver", "'at dele er en god ting'", "'man skal være modig'", "'ærlighed varer længst'" ];
    console.log("Example data defined.");


    // === Logik for Cookie Consent Banner ===
    function triggerAnalyticsPageView() {
        if (typeof gtag === 'function') {
            console.log('Triggering Google Analytics page_view event for path:', window.location.pathname);
            gtag('event', 'page_view', {
                page_path: window.location.pathname,
                page_location: window.location.href,
                page_title: document.title
            });
        } else {
            console.warn('gtag function not found. Analytics page_view not sent.');
        }
    }

    if (cookieConsentBanner && acceptCookiesButton) {
        const consentStatus = localStorage.getItem('cookieConsent');
        console.log('Cookie consent status from localStorage:', consentStatus);
        if (consentStatus === 'accepted') {
            triggerAnalyticsPageView();
        } else if (consentStatus !== 'rejected') {
            cookieConsentBanner.classList.remove('hidden');
        }
        acceptCookiesButton.addEventListener('click', () => {
            localStorage.setItem('cookieConsent', 'accepted');
            cookieConsentBanner.classList.add('hidden');
            triggerAnalyticsPageView();
        });
    } else {
        console.warn('Cookie consent banner or accept button not found in the DOM.');
    }

    // === Hjælpefunktioner ===
    function getRandomElement(arr) {
        if (!arr || arr.length === 0) { console.warn("getRandomElement called with empty or null array"); return null; }
        return arr[Math.floor(Math.random() * arr.length)];
     }

    function addInputField(containerId, placeholder, inputName) {
        const container = document.getElementById(containerId);
        if (!container) { console.error(`Container med ID '${containerId}' blev ikke fundet.`); return; }
        const inputGroup = document.createElement('div'); inputGroup.className = 'input-group';
        const newInput = document.createElement('input'); newInput.type = 'text'; newInput.name = inputName; newInput.placeholder = placeholder;
        const removeButton = document.createElement('button'); removeButton.type = 'button'; removeButton.textContent = '-'; removeButton.className = 'remove-button';
        removeButton.addEventListener('click', () => { inputGroup.remove(); });
        inputGroup.appendChild(newInput); inputGroup.appendChild(removeButton); container.appendChild(inputGroup);
    }

    let karakterCounter = 1;
    function addCharacterGroup() {
        karakterCounter++;
        const characterGroup = document.createElement('div'); characterGroup.className = 'character-group';
        const descPair = document.createElement('div'); descPair.className = 'input-pair';
        const descLabel = document.createElement('label'); descLabel.htmlFor = `karakter-desc-${karakterCounter}`; descLabel.className = 'sr-only'; descLabel.textContent = 'Beskrivelse';
        const descInput = document.createElement('input'); descInput.type = 'text'; descInput.name = 'karakter_desc'; descInput.id = `karakter-desc-${karakterCounter}`; descInput.placeholder = 'Beskrivelse (f.eks. en klog ugle)';
        descPair.appendChild(descLabel); descPair.appendChild(descInput);
        const namePair = document.createElement('div'); namePair.className = 'input-pair';
        const nameLabel = document.createElement('label'); nameLabel.htmlFor = `karakter-navn-${karakterCounter}`; nameLabel.className = 'sr-only'; nameLabel.textContent = 'Navn';
        const nameInput = document.createElement('input'); nameInput.type = 'text'; nameInput.name = 'karakter_navn'; nameInput.id = `karakter-navn-${karakterCounter}`; nameInput.placeholder = 'Navn (valgfrit)';
        namePair.appendChild(nameLabel); namePair.appendChild(nameInput);
        const removeButton = document.createElement('button'); removeButton.type = 'button'; removeButton.textContent = '-'; removeButton.className = 'remove-button';
        removeButton.addEventListener('click', () => { characterGroup.remove(); });
        characterGroup.appendChild(descPair); characterGroup.appendChild(namePair); characterGroup.appendChild(removeButton);
        if (karakterContainer) {
             karakterContainer.appendChild(characterGroup);
        } else { console.error("Karakter container not found!");}
    }

    let listenerCounter = 1;
    function addListenerGroup() {
        listenerCounter++;
        const listenerGroup = document.createElement('div'); listenerGroup.className = 'listener-group';
        const namePair = document.createElement('div'); namePair.className = 'input-pair';
        const nameLabel = document.createElement('label'); nameLabel.htmlFor = `listener-name-${listenerCounter}`; nameLabel.className = 'sr-only'; nameLabel.textContent = 'Navn';
        const nameInput = document.createElement('input'); nameInput.type = 'text'; nameInput.name = 'listener_name_single'; nameInput.id = `listener-name-${listenerCounter}`; nameInput.placeholder = 'Barnets Navn';
        namePair.appendChild(nameLabel); namePair.appendChild(nameInput);
        const agePair = document.createElement('div'); agePair.className = 'input-pair';
        const ageLabel = document.createElement('label'); ageLabel.htmlFor = `listener-age-${listenerCounter}`; ageLabel.className = 'sr-only'; ageLabel.textContent = 'Alder';
        const ageInput = document.createElement('input'); ageInput.type = 'text'; ageInput.name = 'listener_age_single'; ageInput.id = `listener-age-${listenerCounter}`; ageInput.placeholder = 'Alder (f.eks. 5)';
        agePair.appendChild(ageLabel); agePair.appendChild(ageInput);
        const removeButton = document.createElement('button'); removeButton.type = 'button'; removeButton.textContent = '-'; removeButton.className = 'remove-button';
        removeButton.addEventListener('click', () => {
            listenerGroup.remove();
            saveCurrentListeners();
        });
        listenerGroup.appendChild(namePair); listenerGroup.appendChild(agePair); listenerGroup.appendChild(removeButton);
        if (listenerContainer) {
             listenerContainer.appendChild(listenerGroup);
        } else { console.error("Listener container not found!");}
        return listenerGroup;
    }

    function saveCurrentListeners() {
        console.log("Attempting to save listeners...");
        const currentListeners = [];
        if (!listenerContainer) { console.error("Cannot save listeners: Container not found."); return; }
        listenerContainer.querySelectorAll('.listener-group').forEach(group => {
            const nameInput = group.querySelector('input[name="listener_name_single"]');
            const ageInput = group.querySelector('input[name="listener_age_single"]');
            const name = nameInput ? nameInput.value.trim() : '';
            const age = ageInput ? ageInput.value.trim() : '';
            if (name || age) { currentListeners.push({ name: name, age: age }); }
        });
        try {
            if (currentListeners.length > 0) {
                localStorage.setItem('savedListeners', JSON.stringify(currentListeners));
                console.log("Listeners saved to LocalStorage:", JSON.stringify(currentListeners));
            } else {
                localStorage.removeItem('savedListeners');
                console.log("No listener data to save; removed saved listeners from LocalStorage.");
            }
        } catch (e) { console.error("Error saving listeners to LocalStorage:", e); }
    }

    function loadAndDisplaySavedListeners() {
        console.log("Attempting to load listeners from LocalStorage...");
        const savedListenersJSON = localStorage.getItem('savedListeners');
        if (savedListenersJSON) {
            console.log("Found saved listeners:", savedListenersJSON);
            try {
                const savedListeners = JSON.parse(savedListenersJSON);
                if (Array.isArray(savedListeners) && savedListeners.length > 0) {
                    if (!listenerContainer) { console.error("Cannot display listeners: Container not found."); return false; }
                    const existingGroups = listenerContainer.querySelectorAll('.listener-group');
                    // Fjern alle undtagen den første gruppe
                    for (let i = existingGroups.length - 1; i > 0; i--) { existingGroups[i].remove(); }

                    const firstGroup = listenerContainer.querySelector('.listener-group');
                    if (!firstGroup) { // Hvis selv den første gruppe mangler (skulle ikke ske)
                        console.error("Initial listener group not found for loading!");
                        // Opret en første gruppe hvis den mangler helt (defensiv kodning)
                        // addListenerGroup(); // Dette vil skabe en ny, tom gruppe.
                        // firstGroup = listenerContainer.querySelector('.listener-group');
                        // if (!firstGroup) return false; // Giv op hvis det stadig fejler
                        return false;
                    }

                    const firstListenerNameInput = firstGroup.querySelector('input[name="listener_name_single"]');
                    const firstListenerAgeInput = firstGroup.querySelector('input[name="listener_age_single"]');

                    if(firstListenerNameInput) firstListenerNameInput.value = savedListeners[0].name || '';
                    if(firstListenerAgeInput) firstListenerAgeInput.value = savedListeners[0].age || '';
                    console.log("Populated first listener group with:", savedListeners[0]);

                    if (savedListeners.length > 1) {
                        for (let i = 1; i < savedListeners.length; i++) {
                            const listenerData = savedListeners[i];
                            const newGroup = addListenerGroup(); // addListenerGroup håndterer selv at tilføje til DOM
                            if (newGroup) {
                                const newNameInput = newGroup.querySelector('input[name="listener_name_single"]');
                                const newAgeInput = newGroup.querySelector('input[name="listener_age_single"]');
                                if(newNameInput) newNameInput.value = listenerData.name || '';
                                if(newAgeInput) newAgeInput.value = listenerData.age || '';
                                console.log(`Added and populated listener group ${i+1} with:`, listenerData);
                            }
                        }
                    }
                    console.log("Finished loading and displaying listeners.");
                    return true;
                }
            } catch (e) {
                console.error("Error parsing saved listeners from LocalStorage:", e);
                localStorage.removeItem('savedListeners'); // Ryd ugyldige data
            }
        } else {
            console.log("No saved listeners found in LocalStorage.");
        }
        return false;
    }

     function autofillFields() {
        console.log("--> autofillFields started");
        // Nulstil først alle felter (inkl. fjernelse af ekstra grupper og lyttere)
        try {
             handleResetClick(); // Sørg for at dette også rydder gemte lyttere
             console.log("handleResetClick completed for autofill.");
        } catch(e) {
            console.error("Error during handleResetClick from autofill:", e);
            // Fortsæt evt. selvom reset fejler, men det kan give underlig opførsel
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
        const firstStedInputElem = document.querySelector('#sted-container input[name="sted"]'); // Brug querySelector for det første match
        if (randomPlace && firstStedInputElem) {
            firstStedInputElem.value = randomPlace;
        }

        // Udfyld plot (det første input)
        const randomPlot = getRandomElement(examplePlots);
        const firstPlotInputElem = document.querySelector('#plot-container input[name="plot"]'); // Brug querySelector for det første match
        if (randomPlot && firstPlotInputElem) {
            firstPlotInputElem.value = randomPlot;
        }

        if(negativePromptInput) negativePromptInput.value = ''; // Sørg for at negativ prompt er ryddet
        console.log("--> autofillFields finished");
    }

    function toggleFeedbackEmbed() {
        if (feedbackEmbedContainer) {
            feedbackEmbedContainer.classList.toggle('hidden');
            console.log("Feedback embed toggled.");
        } else {
            console.error("Feedback embed container not found!");
        }
    }

    // Hjælpefunktion til at samle historie-input til deling
    function getStoryInputsForSharing() {
        const inputs = {
            karakterBeskrivelse: '',
            karakterNavn: '',
            sted: '',
            plot: '',
            stemning: ''
        };
        if (førsteKarakterDescInput) {
            inputs.karakterBeskrivelse = førsteKarakterDescInput.value.trim();
        }
        if (førsteKarakterNavnInput && førsteKarakterNavnInput.value.trim()) {
            inputs.karakterNavn = førsteKarakterNavnInput.value.trim();
        }
        if (førsteStedInput) {
            inputs.sted = førsteStedInput.value.trim();
        }
        if (førstePlotInput) {
            inputs.plot = førstePlotInput.value.trim();
        }
        if (moodSelect && moodSelect.selectedIndex >= 0) { // Tjek at et valg er truffet
            inputs.stemning = moodSelect.options[moodSelect.selectedIndex].text;
        }
        return inputs;
    }


    async function handleGenerateClick(event) {
        event.preventDefault();
        console.log("--> handleGenerateClick started");

        const karakterer = [];
        if(karakterContainer) { karakterContainer.querySelectorAll('.character-group').forEach(group => { const descInput = group.querySelector('input[name="karakter_desc"]'); const nameInput = group.querySelector('input[name="karakter_navn"]'); const description = descInput ? descInput.value.trim() : ''; const name = nameInput ? nameInput.value.trim() : ''; if (description) { karakterer.push({ description: description, name: name }); } }); }
        const steder = []; document.querySelectorAll('#sted-container .input-group input[name="sted"]').forEach(input => { const v = input.value.trim(); if(v) steder.push(v); });
        const plots = []; document.querySelectorAll('#plot-container .input-group input[name="plot"]').forEach(input => { const v = input.value.trim(); if(v) plots.push(v); });
        const listeners = [];
        if(listenerContainer) { listenerContainer.querySelectorAll('.listener-group').forEach(group => { const nameInput = group.querySelector('input[name="listener_name_single"]'); const ageInput = group.querySelector('input[name="listener_age_single"]'); const name = nameInput ? nameInput.value.trim() : ''; const age = ageInput ? ageInput.value.trim() : ''; if (name || age) { listeners.push({ name: name, age: age }); } }); }

        const selectedLaengde = laengdeSelect ? laengdeSelect.value : 'kort';
        const selectedMoodValue = moodSelect ? moodSelect.value : 'neutral';
        const isInteractive = false; // Som aftalt, altid falsk
        const negativePromptText = negativePromptInput ? negativePromptInput.value.trim() : '';

        console.log("--- Data Indsamlet for Generering ---");
        // ... (andre console.log her hvis ønsket) ...

        saveCurrentListeners(); // Gem lytter-data før API kald
        const dataToSend = { karakterer, steder, plots, laengde: selectedLaengde, mood: selectedMoodValue, listeners, interactive: isInteractive, negative_prompt: negativePromptText };
        console.log("Data prepared for sending to /generate:", dataToSend);

        // Vis Loading State
        if(generateButton) { generateButton.disabled = true; generateButton.textContent = 'Laver historie...'; }
        if(storyDisplay) storyDisplay.textContent = 'Historien genereres... Vent venligst.';
        if(resetButton) resetButton.style.display = 'none';
        if (storyShareButtonsContainer) storyShareButtonsContainer.classList.add('hidden'); // Skjul dele-knapper

        // Skjul lyd/billede elementer
        if(audioPlayer) { audioPlayer.pause(); audioPlayer.src = ''; audioPlayer.classList.add('hidden'); }
        if(audioLoadingDiv) audioLoadingDiv.classList.add('hidden');
        if(audioErrorDiv) audioErrorDiv.textContent = '';
        if(imageControlsDiv) imageControlsDiv.classList.add('hidden'); // Hvis relevant
        if(storyImageTag) { storyImageTag.classList.add('hidden'); storyImageTag.src = ""; } // Hvis relevant
        if(imageErrorDiv) imageErrorDiv.textContent = ''; // Hvis relevant

        try {
            console.log("Initiating fetch call to /generate...");
            const response = await fetch('/generate', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(dataToSend) });
            console.log("Fetch response received. Status:", response.status);
            if (!response.ok) {
                 let errorMsg = `Serverfejl: ${response.status} ${response.statusText}`;
                 try { const errorData = await response.json(); errorMsg += ` - ${errorData.error || JSON.stringify(errorData)}`; } catch (e) { errorMsg += ` - ${await response.text().catch(() => 'Could not read response text')}`; }
                 throw new Error(errorMsg);
            }
            const result = await response.json();
            console.log("JSON parsed successfully:", result);

            if(storyDisplay) storyDisplay.textContent = result.story || "Modtog en tom historie fra serveren.";
            if(resetButton) resetButton.style.display = 'inline-block';

            if (storyShareButtonsContainer && result.story && result.story.trim() !== "") { // Vis kun hvis der faktisk er en historie
                storyShareButtonsContainer.classList.remove('hidden');
            }

        } catch (error) {
             console.error('Fejl under generering (catch block):', error);
             if(storyDisplay) storyDisplay.textContent = `Ups! Noget gik galt under historiegenerering: ${error.message}. Prøv igen eller tjek konsollen for detaljer.`;
             if(resetButton) resetButton.style.display = 'inline-block'; // Vis reset knap ved fejl
        } finally {
             console.log("Executing finally block for story generation...");
             if(generateButton) { generateButton.disabled = false; generateButton.textContent = 'Skab Historie'; }
             console.log("Loading state removed.");
        }
        console.log("--> handleGenerateClick finished");
    }

    async function handleReadAloudClick() {
        console.log("--> handleReadAloudClick started");
        if (!storyDisplay || !storyDisplay.textContent || storyDisplay.textContent.trim() === '' || storyDisplay.textContent.includes('Historien genereres...')) {
            console.error("No valid story text found to read aloud.");
            if(audioErrorDiv) audioErrorDiv.textContent = "Fejl: Kunne ikke finde gyldig historietekst at læse højt.";
            return;
        }

        if (!readAloudButton || !audioLoadingDiv || !audioErrorDiv || !audioPlayer) {
             console.error("Audio elements check failed.");
             if(audioErrorDiv) {
                audioErrorDiv.textContent = "Fejl: Kunne ikke initialisere lyd-elementer (kontakt support hvis problemet fortsætter).";
                audioErrorDiv.classList.remove('hidden');
             }
             if(audioLoadingDiv) audioLoadingDiv.classList.add('hidden');
             if(audioPlayer) audioPlayer.classList.add('hidden');
             return;
        }
        console.log("Audio element check passed.");

        const storyText = storyDisplay.textContent;

        if(audioLoadingDiv) audioLoadingDiv.classList.remove('hidden');
        if(audioErrorDiv) { audioErrorDiv.textContent = ''; audioErrorDiv.classList.add('hidden');}
        if(audioPlayer) { audioPlayer.pause(); audioPlayer.src = ''; audioPlayer.classList.add('hidden');}
        if(readAloudButton) { readAloudButton.disabled = true; readAloudButton.textContent = 'Genererer Lyd...'; }

        try {
            console.log("Initiating fetch call to /generate_audio...");
            const response = await fetch('/generate_audio', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text: storyText }) });
            console.log("Fetch response received for audio. Status:", response.status);
            if (!response.ok) {
                let errorMsg = `Serverfejl (${response.status})`;
                try { const errorData = await response.json(); errorMsg = errorData.error || `${errorMsg} ${response.statusText}`; } catch (e) { errorMsg += ` ${response.statusText}`; console.warn("Could not parse error response as JSON."); }
                 throw new Error(errorMsg);
            }
            const contentType = response.headers.get("content-type");
            if (!contentType || !contentType.includes("audio/mpeg")) {
                 throw new Error(`Modtog ikke gyldig lydfil fra serveren (type: ${contentType}).`);
            }
            console.log("Audio data received. Creating Blob URL...");
            const audioBlob = await response.blob();
            const audioUrl = URL.createObjectURL(audioBlob);
            if(audioPlayer) {
                audioPlayer.src = audioUrl;
                audioPlayer.classList.remove('hidden');
                console.log("Audio player ready.");
            } else {
                 console.error("Audio player element not found when trying to set source!");
                 throw new Error("Intern fejl: Kunne ikke finde lyd-afspiller element.");
            }
        } catch (error) {
            console.error("Fejl under lydgenerering:", error);
            if(audioErrorDiv) {
                audioErrorDiv.textContent = `Fejl: ${error.message}`;
                audioErrorDiv.classList.remove('hidden');
            }
            if(audioPlayer) audioPlayer.classList.add('hidden');
        } finally {
            if(audioLoadingDiv) audioLoadingDiv.classList.add('hidden');
            if(readAloudButton) {
                readAloudButton.disabled = false;
                readAloudButton.textContent = 'Læs Historien Højt';
            }
            console.log("--> handleReadAloudClick finished");
        }
    }

    async function handleGenerateImageClick() {
         console.warn("Billedgenerering er ikke implementeret endnu.");
         if(imageErrorDiv) { imageErrorDiv.textContent = "Billedgenerering er ikke tilgængelig endnu."; imageErrorDiv.classList.remove('hidden'); }
    }

    function handleResetClick() {
        console.log("--> handleResetClick started");
        if(generatorSection) {
            generatorSection.querySelectorAll('input[type="text"], textarea').forEach(input => {
                input.value = '';
            });
        }
        if(interactiveCheckbox) interactiveCheckbox.checked = false;
        console.log("Cleared text inputs and textarea.");

        const removeExtraGroups = (containerId, groupSelector) => {
            const container = document.getElementById(containerId);
            if (container) {
                const groups = container.querySelectorAll(groupSelector);
                if (groups.length > 1) {
                    for (let i = groups.length - 1; i > 0; i--) {
                        groups[i].remove();
                    }
                } else {
                    console.log(`Only one group found for ${groupSelector} in ${containerId}, not removing.`);
                }
            } else {
                console.warn(`Reset: Container ${containerId} not found`);
            }
        };
        removeExtraGroups('listener-container', '.listener-group');
        removeExtraGroups('karakter-container', '.character-group');
        removeExtraGroups('sted-container', '.input-group');
        removeExtraGroups('plot-container', '.input-group');
        console.log("Removed extra groups.");

        if(storyDisplay) storyDisplay.textContent = '';
        if(resetButton) resetButton.style.display = 'none';

        if (storyShareButtonsContainer) storyShareButtonsContainer.classList.add('hidden'); // Skjul dele-knapper

        // Skjul lyd/billede elementer
        if(audioPlayer) { audioPlayer.pause(); audioPlayer.src = ''; audioPlayer.classList.add('hidden'); }
        if(audioLoadingDiv) audioLoadingDiv.classList.add('hidden');
        if(audioErrorDiv) { audioErrorDiv.textContent = ''; audioErrorDiv.classList.add('hidden'); }
        if(imageControlsDiv) imageControlsDiv.classList.add('hidden');
        if(storyImageTag) { storyImageTag.classList.add('hidden'); storyImageTag.src = ""; }
        if(imageErrorDiv) { imageErrorDiv.textContent = ''; imageErrorDiv.classList.add('hidden'); }

        console.log("Cleared story display and hid controls (reset, individual audio/image elements, share buttons).");

        if(laengdeSelect) laengdeSelect.value = 'kort';
        if(moodSelect) moodSelect.value = 'neutral';
        console.log("Reset dropdowns.");

        try {
            localStorage.removeItem('savedListeners');
            console.log("Removed saved listeners from LocalStorage due to reset.");
        } catch (e) {
            console.error("Error removing listeners from LocalStorage:", e);
        }
        console.log("--> handleResetClick finished");
    }


 // === Event Listeners for historie-dele knapper ===
    if (shareStoryFacebookButton) {
        shareStoryFacebookButton.addEventListener('click', () => { // <--- MANGLENDE EVENT LISTENER TILFØJET HER
            const inputs = getStoryInputsForSharing();
            const storyText = storyDisplay.textContent || "";
            const appURL = window.location.origin;

            let quoteTextParts = [`Jeg har skabt en historie med Read Me A Story! (${appURL})`];
            let storyDetails = [];
            if (inputs.karakterBeskrivelse) {
                let karakter = inputs.karakterBeskrivelse;
                if (inputs.karakterNavn) karakter += ` ved navn ${inputs.karakterNavn}`;
                storyDetails.push(`Hovedperson: ${karakter}.`);
            }
            if (inputs.sted) storyDetails.push(`Sted: ${inputs.sted}.`);
            if (inputs.plot) storyDetails.push(`Plot: ${inputs.plot}.`);
            if (inputs.stemning) storyDetails.push(`Stemning: ${inputs.stemning}.`);

            quoteTextParts.push(storyDetails.join(' '));

            if (storyText) {
                const snippet = storyText.substring(0, 150) + (storyText.length > 150 ? "..." : "");
                quoteTextParts.push(`Uddrag: "${snippet}"`);
            }
            // quoteTextParts.push(`Prøv selv på ${appURL}`); // appURL er allerede i startteksten

            const quote = encodeURIComponent(quoteTextParts.join(' '));
            const encodedAppURL = encodeURIComponent(appURL); // Selvom origin typisk er ren, for en sikkerheds skyld.
            const facebookShareURL = `https://www.facebook.com/sharer/sharer.php?u=${encodedAppURL}&quote=${quote}`;

            console.log("Forsøger at dele på Facebook med quote:", decodeURIComponent(quote));
            console.log("Facebook Share URL:", facebookShareURL);

            window.open(facebookShareURL, '_blank', 'width=600,height=400,noopener,noreferrer');
        });
    } else {
        console.warn("Facebook share button (#share-story-facebook-button) not found.");
    }

    if (copyStoryButton) {
        copyStoryButton.addEventListener('click', async () => { // <--- MANGLENDE EVENT LISTENER TILFØJET HER
            const inputs = getStoryInputsForSharing();
            const storyText = storyDisplay.textContent || "";
            const appURL = window.location.origin;

            let textToCopyParts = ["Min Godnathistorie fra Read Me A Story:", "---"];
            if (inputs.karakterBeskrivelse) {
                let karakter = inputs.karakterBeskrivelse;
                if (inputs.karakterNavn) karakter += ` ved navn ${inputs.karakterNavn}`;
                textToCopyParts.push(`Hovedperson: ${karakter}`);
            }
            if (inputs.sted) textToCopyParts.push(`Sted: ${inputs.sted}`);
            if (inputs.plot) textToCopyParts.push(`Plot/Morale: ${inputs.plot}`);
            if (inputs.stemning) textToCopyParts.push(`Stemning: ${inputs.stemning}`);
            textToCopyParts.push("---");

            if (storyText) {
                textToCopyParts.push("Historie:");
                textToCopyParts.push(storyText);
            }
            textToCopyParts.push("---");
            textToCopyParts.push(`Skabt med Read Me A Story: ${appURL}`);

            const textToCopy = textToCopyParts.join('\n\n');

            try {
                await navigator.clipboard.writeText(textToCopy);
                const originalText = copyStoryButton.textContent;
                copyStoryButton.textContent = 'Kopieret!';
                copyStoryButton.disabled = true;
                setTimeout(() => {
                    copyStoryButton.textContent = originalText;
                    copyStoryButton.disabled = false;
                }, 2000);
                console.log('Historie kopieret til udklipsholder');
            } catch (err) {
                console.error('Fejl ved kopiering til udklipsholder: ', err);
                alert('Kunne ikke kopiere historien automatisk. Du kan prøve at markere og kopiere teksten manuelt.');
            }
        });
    } else {
        console.warn("Copy story button (#copy-story-button) not found.");
    }
    // === SLUT: Event Listeners for historie-dele knapper ===

    // === Tilknyt øvrige Event Listeners ===
    // Indlæs gemte lyttere først
    loadAndDisplaySavedListeners();

    if (generateButton) { generateButton.addEventListener('click', handleGenerateClick); } else { console.error("Generate button not found!"); }
    if (resetButton) { resetButton.addEventListener('click', handleResetClick); } else { console.error("Reset button not found!"); }
    if (autofillButton) { autofillButton.addEventListener('click', autofillFields); } else { console.error("Autofill button not found!"); }
    if (addListenerButton) { addListenerButton.addEventListener('click', addListenerGroup); } else { console.error("Add listener button not found!"); }
    if (addKarakterButton) { addKarakterButton.addEventListener('click', addCharacterGroup); } else { console.error("Add character button not found!"); }
    if (readAloudButton) { readAloudButton.addEventListener('click', handleReadAloudClick); } else { console.info("Read Aloud button not found."); } // Kan være deaktiveret for ikke-loggede ind
    if (toggleFeedbackButton) { toggleFeedbackButton.addEventListener('click', toggleFeedbackEmbed); } else { console.error("Toggle feedback button not found!"); }
    if (generateImageButton) { generateImageButton.addEventListener('click', handleGenerateImageClick); } else { console.info("Generate Image button (image feature) not found or not active."); }

    document.querySelectorAll('.add-button[data-container]').forEach(button => {
        button.addEventListener('click', () => {
            const containerId = button.dataset.container;
            const placeholder = button.dataset.placeholder;
            const inputName = button.dataset.name;
            if(containerId && placeholder && inputName) {
                addInputField(containerId, placeholder, inputName);
            } else {
                console.warn("Generic add button is missing data attributes:", button);
            }
        });
        // console.log(`Listener attached for generic add button targeting ${button.dataset.container}`); // Kan være meget støjende
    });

    console.log("Script loaded and all initial event listeners attached.");

}); // Slut på DOMContentLoaded listener