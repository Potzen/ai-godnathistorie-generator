// Kør først koden, når hele HTML dokumentet er færdigindlæst og klar
document.addEventListener('DOMContentLoaded', () => {
    console.log("DOMContentLoaded event fired."); // Start log

    // === Hent referencer til HTML elementer ===
    // Henter alle nødvendige elementer fra HTML-siden via deres ID
    const generateButton = document.getElementById('generate-button');
    const resetButton = document.getElementById('reset-button');
    const storyDisplay = document.getElementById('story-display');
    const generatorSection = document.getElementById('generator');
    const laengdeSelect = document.getElementById('laengde-select'); // Vigtig for reset
    const moodSelect = document.getElementById('mood-select'); // Vigtig for reset
    const listenerContainer = document.getElementById('listener-container');
    const addListenerButton = document.getElementById('add-listener-button');
    const karakterContainer = document.getElementById('karakter-container');
    const addKarakterButton = document.getElementById('add-karakter-button');
    const interactiveCheckbox = document.getElementById('interactive-checkbox');
    const autofillButton = document.getElementById('autofill-button');
    const toggleFeedbackButton = document.getElementById('toggle-feedback-button');
    const feedbackEmbedContainer = document.getElementById('feedback-embed-container');
    // Referencer til billede elementer (hvis de er implementeret, ellers er de uskadelige)
    const imageControlsDiv = document.getElementById('image-controls');
    const generateImageButton = document.getElementById('generate-image-button');
    const imageLoadingDiv = document.getElementById('image-loading');
    const storyImageTag = document.getElementById('story-image');
    const imageErrorDiv = document.getElementById('image-error');
    console.log("DOM references obtained.");

    // === Eksempeldata til Autoudfyld ===
    // Lister med forslag til hurtig udfyldning
    const exampleListeners = [
        { name: "Alma", age: "5" }, { name: "Oscar", age: "7" },
        { name: "Sofus", age: "3"}, { name: "Luna", age: "6" },
        { name: "Noah", age: "4" }, { name: "Freja", age: "8" },
        { name: "Viggo", age: "5" } // Kun eksempler med ét barn
    ];
     const exampleCharacters = [
        { description: "en drilsk nisse", name: "Pip" }, { description: "en meget søvnig bjørn", name: "" },
        { description: "et flyvende tæppe", name: "" }, { description: "en robot der elsker kage", name: "Kaptajn Kiks" },
        { description: "en fe der har mistet sin tryllestav", name: "Flora" }
     ];
     const examplePlaces = [
        "i en skov lavet af slik", "på en øde ø med talende papegøjer", "i et omvendt hus hvor alt er på loftet",
        "på månen hvor ostene gror", "dybt under jorden i en krystalgrotte"
     ];
     const examplePlots = [
        "skulle finde en forsvundet stjerne", "byggede en fantastisk maskine", "holdt en overraskelsesfest",
        "mødte et dyr de aldrig havde set før", "lærte at trylle med farver", "'at dele er en god ting'",
        "'man skal være modig'", "'ærlighed varer længst'"
     ];
    console.log("Example data defined.");

    // === Hjælpefunktioner ===
    // Funktion til at vælge et tilfældigt element fra en liste
    function getRandomElement(arr) {
        if (!arr || arr.length === 0) { console.warn("getRandomElement called with empty or null array"); return null; };
        const index = Math.floor(Math.random() * arr.length);
        return arr[index];
     }

    // Funktion til at tilføje Sted/Plot felter
    function addInputField(containerId, placeholder, inputName) {
        const container = document.getElementById(containerId);
        if (!container) { console.error(`Container med ID '${containerId}' blev ikke fundet.`); return; }
        const inputGroup = document.createElement('div'); inputGroup.className = 'input-group';
        const newInput = document.createElement('input'); newInput.type = 'text'; newInput.name = inputName; newInput.placeholder = placeholder;
        const removeButton = document.createElement('button'); removeButton.type = 'button'; removeButton.textContent = '-'; removeButton.className = 'remove-button';
        removeButton.addEventListener('click', () => { inputGroup.remove(); });
        inputGroup.appendChild(newInput); inputGroup.appendChild(removeButton); container.appendChild(inputGroup);
    }

    // Funktion til at tilføje Karakter par (Beskrivelse + Navn)
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

    // Funktion til at tilføje Lytter par (Navn + Alder) - OPDATERET til at returnere gruppen og gemme ved fjernelse
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
        // Tilføj event listener til den nye fjern-knap
        removeButton.addEventListener('click', () => {
            listenerGroup.remove();
            // VIGTIGT: Gem den nye (reducerede) liste, når en lytter fjernes manuelt
            saveCurrentListeners();
        });
        listenerGroup.appendChild(namePair); listenerGroup.appendChild(agePair); listenerGroup.appendChild(removeButton);
        if (listenerContainer) {
             listenerContainer.appendChild(listenerGroup);
        } else { console.error("Listener container not found!");}
        return listenerGroup; // *** Returner det nye element ***
    }

    // === Funktion til at gemme aktuelle lyttere i LocalStorage ===
    function saveCurrentListeners() {
        console.log("Attempting to save listeners...");
        const currentListeners = [];
        if (!listenerContainer) { console.error("Cannot save listeners: Container not found."); return; }

        listenerContainer.querySelectorAll('.listener-group').forEach(group => {
            const nameInput = group.querySelector('input[name="listener_name_single"]');
            const ageInput = group.querySelector('input[name="listener_age_single"]');
            const name = nameInput ? nameInput.value.trim() : '';
            const age = ageInput ? ageInput.value.trim() : '';
            // Gem kun rækker hvor der er indtastet noget (enten navn eller alder)
            if (name || age) {
                currentListeners.push({ name: name, age: age });
            }
        });

        try {
            if (currentListeners.length > 0) {
                // Konverter listen af objekter til en JSON-streng
                const listenersJSON = JSON.stringify(currentListeners);
                // Gem strengen i localStorage under nøglen 'savedListeners'
                localStorage.setItem('savedListeners', listenersJSON);
                console.log("Listeners saved to LocalStorage:", listenersJSON);
            } else {
                // Hvis ingen lyttere er indtastet, fjern evt. gamle gemte data
                localStorage.removeItem('savedListeners');
                console.log("No listener data to save; removed saved listeners from LocalStorage.");
            }
        } catch (e) {
            // Håndter evt. fejl (f.eks. hvis localStorage er fuld eller deaktiveret)
            console.error("Error saving listeners to LocalStorage:", e);
        }
    }

    // === Funktion til at indlæse og vise gemte lyttere ===
    function loadAndDisplaySavedListeners() {
        console.log("Attempting to load listeners from LocalStorage...");
        // Hent den gemte JSON-streng fra localStorage
        const savedListenersJSON = localStorage.getItem('savedListeners');
        if (savedListenersJSON) {
            console.log("Found saved listeners:", savedListenersJSON);
            try {
                // Konverter JSON-strengen tilbage til en liste af objekter
                const savedListeners = JSON.parse(savedListenersJSON);
                // Tjek om det er en gyldig liste med mindst ét element
                if (Array.isArray(savedListeners) && savedListeners.length > 0) {
                    if (!listenerContainer) { console.error("Cannot display listeners: Container not found."); return false; }

                    // Ryd eventuelle eksisterende rækker (udover den første)
                    const existingGroups = listenerContainer.querySelectorAll('.listener-group');
                    for (let i = existingGroups.length - 1; i > 0; i--) {
                        existingGroups[i].remove();
                    }

                    // Udfyld den første (altid eksisterende) lytter-række
                    const firstGroup = listenerContainer.querySelector('.listener-group');
                     if (!firstGroup) { console.error("Initial listener group not found!"); return false; }
                    const firstListenerNameInput = firstGroup.querySelector('input[name="listener_name_single"]');
                    const firstListenerAgeInput = firstGroup.querySelector('input[name="listener_age_single"]');
                    if(firstListenerNameInput) firstListenerNameInput.value = savedListeners[0].name || '';
                    if(firstListenerAgeInput) firstListenerAgeInput.value = savedListeners[0].age || '';
                    console.log("Populated first listener group with:", savedListeners[0]);

                    // Hvis der var gemt flere lyttere, tilføj nye rækker og udfyld dem
                    if (savedListeners.length > 1) {
                        for (let i = 1; i < savedListeners.length; i++) {
                            const listenerData = savedListeners[i];
                            // Kald addListenerGroup for at oprette en ny række (den returnerer den nye gruppe)
                            const newGroup = addListenerGroup();
                            if (newGroup) {
                                // Find inputfelterne i den *nye* gruppe og sæt værdierne
                                const newNameInput = newGroup.querySelector('input[name="listener_name_single"]');
                                const newAgeInput = newGroup.querySelector('input[name="listener_age_single"]');
                                if(newNameInput) newNameInput.value = listenerData.name || '';
                                if(newAgeInput) newAgeInput.value = listenerData.age || '';
                                console.log(`Added and populated listener group ${i+1} with:`, listenerData);
                            }
                        }
                    }
                    console.log("Finished loading and displaying listeners.");
                    return true; // Indikerer succes
                }
            } catch (e) {
                // Håndter fejl hvis gemte data er korrupte
                console.error("Error parsing saved listeners from LocalStorage:", e);
                localStorage.removeItem('savedListeners'); // Fjern de ugyldige data
            }
        } else {
            console.log("No saved listeners found in LocalStorage.");
        }
        return false; // Indikerer at intet blev indlæst
    }

    // === Funktion til Autoudfyld ===
     function autofillFields() {
        console.log("--> autofillFields started");
        handleResetClick(); // Ryd op først (Bemærk: handleResetClick rydder også localStorage nu)
        console.log("handleResetClick completed for autofill.");

        // Udfyld Lytter (kun den første række)
        const randomListener = getRandomElement(exampleListeners);
        if (randomListener && listenerContainer) { const firstListenerNameInput = listenerContainer.querySelector('input[name="listener_name_single"]'); const firstListenerAgeInput = listenerContainer.querySelector('input[name="listener_age_single"]'); if (firstListenerNameInput) firstListenerNameInput.value = randomListener.name; if (firstListenerAgeInput) firstListenerAgeInput.value = randomListener.age; }
        // Udfyld Karakter (kun den første række)
        const randomCharacter = getRandomElement(exampleCharacters);
        if (randomCharacter && karakterContainer) { const firstCharDescInput = karakterContainer.querySelector('input[name="karakter_desc"]'); const firstCharNameInput = karakterContainer.querySelector('input[name="karakter_navn"]'); if (firstCharDescInput) firstCharDescInput.value = randomCharacter.description; if (firstCharNameInput) firstCharNameInput.value = randomCharacter.name; }
        // Udfyld Sted
        const randomPlace = getRandomElement(examplePlaces); const firstStedInput = document.querySelector('#sted-container input[name="sted"]'); if (randomPlace && firstStedInput) { firstStedInput.value = randomPlace; }
        // Udfyld Plot
        const randomPlot = getRandomElement(examplePlots); const firstPlotInput = document.querySelector('#plot-container input[name="plot"]'); if (randomPlot && firstPlotInput) { firstPlotInput.value = randomPlot; }

        console.log("--> autofillFields finished");
    }

    // === Feedback Toggle Funktion ===
    function toggleFeedbackEmbed() {
        if (feedbackEmbedContainer) { feedbackEmbedContainer.classList.toggle('hidden'); console.log("Feedback embed toggled."); }
        else { console.error("Feedback embed container not found!"); }
    }

    // === Funktion: Klik på "Skab Godnathistorie" ===
    async function handleGenerateClick(event) {
        event.preventDefault();
        console.log("--> handleGenerateClick started");

        // Indsamling af data
        const karakterer = [];
        if(karakterContainer) {
            karakterContainer.querySelectorAll('.character-group').forEach(group => {
                const descInput = group.querySelector('input[name="karakter_desc"]'); const nameInput = group.querySelector('input[name="karakter_navn"]');
                const description = descInput ? descInput.value.trim() : ''; const name = nameInput ? nameInput.value.trim() : '';
                if (description) { karakterer.push({ description: description, name: name }); }
             });
        }
        const steder = []; document.querySelectorAll('#sted-container .input-group input[name="sted"]').forEach(input => { const v = input.value.trim(); if(v) steder.push(v); });
        const plots = []; document.querySelectorAll('#plot-container .input-group input[name="plot"]').forEach(input => { const v = input.value.trim(); if(v) plots.push(v); });
        const listeners = [];
        if(listenerContainer) {
            listenerContainer.querySelectorAll('.listener-group').forEach(group => {
                 const nameInput = group.querySelector('input[name="listener_name_single"]'); const ageInput = group.querySelector('input[name="listener_age_single"]');
                 const name = nameInput ? nameInput.value.trim() : ''; const age = ageInput ? ageInput.value.trim() : '';
                 if (name || age) { listeners.push({ name: name, age: age }); }
            });
        }
        const selectedLaengde = laengdeSelect ? laengdeSelect.value : 'kort'; // Default til 'kort'
        const selectedMood = moodSelect ? moodSelect.value : 'neutral';
        const isInteractive = interactiveCheckbox ? interactiveCheckbox.checked : false;

        console.log("--- Data Indsamlet ---");
        console.log("Listeners:", listeners);
        // ... andre logs ...

        // *** GEM AKTUELLE LYTTERE ***
        saveCurrentListeners();

        console.log("Validation skipped.");
        const dataToSend = { karakterer, steder, plots, laengde: selectedLaengde, mood: selectedMood, listeners, interactive: isInteractive };
        console.log("Data prepared for sending:", dataToSend);

        // Vis Loading State...
        console.log("Setting loading state...");
        if(generateButton) { generateButton.disabled = true; generateButton.textContent = 'Laver historie...'; }
        if(storyDisplay) storyDisplay.textContent = 'Historien genereres...';
        if(resetButton) resetButton.style.display = 'none';
        // Skjul evt. gammelt billede/fejl/knap ...
        if(imageControlsDiv) imageControlsDiv.classList.add('hidden');
        if(storyImageTag) { storyImageTag.classList.add('hidden'); storyImageTag.src = ""; }
        if(imageErrorDiv) imageErrorDiv.textContent = '';
        console.log("Loading state set.");

        // Fetch API Kald ...
        try {
            console.log("Initiating fetch call to /generate...");
            const response = await fetch('/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(dataToSend)
             });
            console.log("Fetch response received. Status:", response.status);
            if (!response.ok) {
                 let errorMsg = `Serverfejl: ${response.status} ${response.statusText}`;
                 try { const errorData = await response.json(); errorMsg += ` - ${errorData.error || JSON.stringify(errorData)}`; } catch (e) { /* Ignorer */ }
                 throw new Error(errorMsg);
            }
            const result = await response.json();
            console.log("JSON parsed successfully.");

            // Vis resultat
            if(storyDisplay) storyDisplay.textContent = result.story || "Modtog en tom historie.";
            if(resetButton) resetButton.style.display = 'inline-block';
            // Vis billede-knap hvis den findes og er implementeret
            if (imageControlsDiv && generateImageButton) imageControlsDiv.classList.remove('hidden');
            console.log("Story displayed, reset and maybe image buttons shown.");
        } catch (error) {
             console.error('Fejl under generering (catch block):', error);
             if(storyDisplay) storyDisplay.textContent = `Ups! Noget gik galt: ${error.message}. Tjek konsollen for detaljer.`;
        } finally {
             console.log("Executing finally block...");
             if(generateButton) { generateButton.disabled = false; generateButton.textContent = 'Skab Godnathistorie'; }
             console.log("Loading state removed.");
        }
        console.log("--> handleGenerateClick finished");
    }

    // === Funktion: Klik på "Generer Billede" ===
    // Tom funktion, da den ikke er implementeret endnu
    async function handleGenerateImageClick() {
         console.warn("Billedgenerering er ikke implementeret endnu.");
         // Her ville fetch kald til /generate_image osv. komme
    }

    // === Funktion: Klik på "Prøv Igen" (OPDATERET RESET AF DROPDOWN) ===
    function handleResetClick() {
        console.log("--> handleResetClick started");
        // Ryd inputs, checkbox, fjern ekstra grupper...
        if(generatorSection) {
            generatorSection.querySelectorAll('input[type="text"]').forEach(input => { input.value = ''; });
        }
         if(interactiveCheckbox) interactiveCheckbox.checked = false;
        console.log("Cleared inputs and checkbox.");

        const removeExtraGroups = (containerId, groupSelector) => {
            const container = document.getElementById(containerId);
            if (container) {
                const groups = container.querySelectorAll(groupSelector);
                // Tjek om der er mere end én gruppe før vi fjerner
                if (groups.length > 1) {
                    for (let i = groups.length - 1; i > 0; i--) {
                        console.log(`Removing extra group at index ${i}:`, groups[i]);
                        groups[i].remove();
                    }
                } else {
                    console.log(`Only one group found for ${groupSelector} in ${containerId}, not removing.`);
                }
            } else { console.warn(`Reset: Container ${containerId} not found`); }
        };
        removeExtraGroups('listener-container', '.listener-group');
        removeExtraGroups('karakter-container', '.character-group');
        removeExtraGroups('sted-container', '.input-group');
        removeExtraGroups('plot-container', '.input-group');
        console.log("Removed extra groups.");

        // Ryd historie og skjul knapper/billede...
        if(storyDisplay) storyDisplay.textContent = '';
        if(resetButton) resetButton.style.display = 'none';
        if(imageControlsDiv) imageControlsDiv.classList.add('hidden');
        if(storyImageTag) { storyImageTag.classList.add('hidden'); storyImageTag.src = ""; }
        if(imageErrorDiv) imageErrorDiv.textContent = '';
        console.log("Cleared story display and hid controls.");

        // Nulstil dropdowns...
        // *** OPDATERET: Nulstil længde til 'kort' ***
        if(laengdeSelect) laengdeSelect.value = 'kort';
        if(moodSelect) moodSelect.value = 'neutral';
        console.log("Reset dropdowns.");

        // *** Ryd gemte lyttere fra LocalStorage ***
        try {
            localStorage.removeItem('savedListeners');
            console.log("Removed saved listeners from LocalStorage due to reset.");
        } catch (e) {
             console.error("Error removing listeners from LocalStorage:", e);
        }
        console.log("--> handleResetClick finished");
    }


    // === Tilknyt Event Listeners ===
    // Tilføjer tjek for om elementet findes før tilknytning
    if (generateButton) { generateButton.addEventListener('click', handleGenerateClick); console.log("Generate listener attached."); } else { console.error("Generate button not found!"); }
    if (resetButton) { resetButton.addEventListener('click', handleResetClick); console.log("Reset listener attached."); } else { console.error("Reset button not found!"); }
    if (autofillButton) { autofillButton.addEventListener('click', autofillFields); console.log("Autofill listener attached."); } else { console.error("Autofill button not found!"); }
    if (addListenerButton) { addListenerButton.addEventListener('click', addListenerGroup); console.log("Add listener button listener attached."); } else { console.error("Add listener button not found!"); }
    if (addKarakterButton) { addKarakterButton.addEventListener('click', addCharacterGroup); console.log("Add character button listener attached."); } else { console.error("Add character button not found!"); }
    if (toggleFeedbackButton) { toggleFeedbackButton.addEventListener('click', toggleFeedbackEmbed); console.log("Feedback toggle listener attached."); } else { console.error("Toggle feedback button not found!"); }
    // Tilføj listener for billede knap hvis den findes
    if (generateImageButton) { generateImageButton.addEventListener('click', handleGenerateImageClick); console.log("Generate Image listener attached."); } else { console.info("Generate Image button not found (feature might be inactive)."); }

     // Tilføj listeners til generiske Tilføj-knapper (Sted/Plot)
     document.querySelectorAll('.add-button[data-container]').forEach(button => {
         button.addEventListener('click', () => {
            const containerId = button.dataset.container;
            const placeholder = button.dataset.placeholder;
            const inputName = button.dataset.name;
            addInputField(containerId, placeholder, inputName);
        });
        console.log(`Listener attached for generic add button targeting ${button.dataset.container}`);
     });


    // === Initialiser siden ved at indlæse gemte lyttere ===
    loadAndDisplaySavedListeners();


    console.log("Script loaded and initial listeners attached check complete.");

}); // Slut på DOMContentLoaded listener - SØRG FOR DENNE ER MED!
