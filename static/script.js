// Kør først koden, når hele HTML dokumentet er færdigindlæst og klar
document.addEventListener('DOMContentLoaded', () => {
    console.log("DOMContentLoaded event fired."); // Start log

    // === Hent referencer til HTML elementer ===
    const generateButton = document.getElementById('generate-button');
    const resetButton = document.getElementById('reset-button');
    const storyDisplay = document.getElementById('story-display');
    const generatorSection = document.getElementById('generator');
    const laengdeSelect = document.getElementById('laengde-select');
    const moodSelect = document.getElementById('mood-select');
    const listenerContainer = document.getElementById('listener-container');
    const addListenerButton = document.getElementById('add-listener-button');
    const karakterContainer = document.getElementById('karakter-container');
    const addKarakterButton = document.getElementById('add-karakter-button');
    const interactiveCheckbox = document.getElementById('interactive-checkbox');
    const autofillButton = document.getElementById('autofill-button');
    // *** Referencer til Feedback Toggle ***
    const toggleFeedbackButton = document.getElementById('toggle-feedback-button');
    const feedbackEmbedContainer = document.getElementById('feedback-embed-container');
    console.log("DOM references obtained.");

    // === Eksempeldata til Autoudfyld (Rettet Listener data) ===
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
        "mødte et dyr de aldrig havde set før", "lærte at trylle med farver"
     ];
    console.log("Example data defined.");

    // Hjælpefunktion til at få et tilfældigt element fra en liste
    function getRandomElement(arr) {
        if (!arr || arr.length === 0) { console.warn("getRandomElement called with empty or null array"); return null; };
        const index = Math.floor(Math.random() * arr.length);
        return arr[index];
     }

    // === Funktion til dynamisk at tilføje Sted/Plot felter ===
    function addInputField(containerId, placeholder, inputName) {
        const container = document.getElementById(containerId);
        if (!container) { console.error(`Container med ID '${containerId}' blev ikke fundet.`); return; }
        const inputGroup = document.createElement('div'); inputGroup.className = 'input-group';
        const newInput = document.createElement('input'); newInput.type = 'text'; newInput.name = inputName; newInput.placeholder = placeholder;
        const removeButton = document.createElement('button'); removeButton.type = 'button'; removeButton.textContent = '-'; removeButton.className = 'remove-button';
        removeButton.addEventListener('click', () => { inputGroup.remove(); });
        inputGroup.appendChild(newInput); inputGroup.appendChild(removeButton); container.appendChild(inputGroup);
    }

    // === Tilføj Event Listeners til "Tilføj Sted/Plot" knapperne ===
    document.querySelectorAll('.add-button[data-container]').forEach(button => {
         button.addEventListener('click', () => {
            const containerId = button.dataset.container;
            const placeholder = button.dataset.placeholder;
            const inputName = button.dataset.name;
            addInputField(containerId, placeholder, inputName);
        });
     });

    // === Funktion til at tilføje et Karakter (Beskrivelse + Navn) par ===
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
        karakterContainer.appendChild(characterGroup);
    }
    // Event Listener for "Tilføj karakter" knappen
    addKarakterButton.addEventListener('click', addCharacterGroup);

    // === Funktion til at tilføje et Navn/Alder par (Lytter) ===
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
         removeButton.addEventListener('click', () => { listenerGroup.remove(); });
         listenerGroup.appendChild(namePair); listenerGroup.appendChild(agePair); listenerGroup.appendChild(removeButton);
         listenerContainer.appendChild(listenerGroup);
     }
     // Event Listener for "Tilføj barn" knappen
    addListenerButton.addEventListener('click', addListenerGroup);

     // === Funktion der udfylder felterne med eksempler ===
     function autofillFields() {
         console.log("--> autofillFields started");
         handleResetClick(); // Ryd op først
         console.log("handleResetClick completed for autofill.");

         // Udfyld Lytter
         console.log("Attempting to fill listener info...");
         const randomListener = getRandomElement(exampleListeners);
         console.log("Random listener data:", randomListener);
         if (randomListener) {
             const firstListenerNameInput = listenerContainer.querySelector('input[name="listener_name_single"]');
             const firstListenerAgeInput = listenerContainer.querySelector('input[name="listener_age_single"]');
             console.log("Found listener name input:", firstListenerNameInput);
             console.log("Found listener age input:", firstListenerAgeInput);
             if (firstListenerNameInput) { firstListenerNameInput.value = randomListener.name; console.log(`Set listener name to: ${randomListener.name}`); }
             else { console.warn("Could not find first listener name input."); }
             if (firstListenerAgeInput) { firstListenerAgeInput.value = randomListener.age; console.log(`Set listener age to: ${randomListener.age}`); }
             else { console.warn("Could not find first listener age input."); }
         } else { console.warn("No random listener data selected."); }

         // Udfyld Karakter
         console.log("Attempting to fill character info...");
         const randomCharacter = getRandomElement(exampleCharacters);
         console.log("Random character data:", randomCharacter);
         if (randomCharacter) {
             const firstCharDescInput = karakterContainer.querySelector('input[name="karakter_desc"]');
             const firstCharNameInput = karakterContainer.querySelector('input[name="karakter_navn"]');
             console.log("Found character desc input:", firstCharDescInput);
             console.log("Found character name input:", firstCharNameInput);
             if (firstCharDescInput) { firstCharDescInput.value = randomCharacter.description; console.log(`Set character desc to: ${randomCharacter.description}`); }
             else { console.warn("Could not find first character desc input."); }
             if (firstCharNameInput) { firstCharNameInput.value = randomCharacter.name; console.log(`Set character name to: ${randomCharacter.name}`); }
              else { console.warn("Could not find first character name input."); }
         } else { console.warn("No random character data selected."); }

         // Udfyld Sted
         console.log("Attempting to fill place info...");
         const randomPlace = getRandomElement(examplePlaces);
         console.log("Random place data:", randomPlace);
         const firstStedInput = document.querySelector('#sted-container input[name="sted"]');
         console.log("Found place input:", firstStedInput);
         if (randomPlace && firstStedInput) { firstStedInput.value = randomPlace; console.log(`Set place to: ${randomPlace}`); }
         else { console.warn("Could not find first place input or no random place."); }

         // Udfyld Plot
         console.log("Attempting to fill plot info...");
         const randomPlot = getRandomElement(examplePlots);
         console.log("Random plot data:", randomPlot);
         const firstPlotInput = document.querySelector('#plot-container input[name="plot"]');
         console.log("Found plot input:", firstPlotInput);
         if (randomPlot && firstPlotInput) { firstPlotInput.value = randomPlot; console.log(`Set plot to: ${randomPlot}`); }
         else { console.warn("Could not find first plot input or no random plot."); }

         console.log("--> autofillFields finished");
     }
     // Event Listener for Autoudfyld knappen
     autofillButton.addEventListener('click', autofillFields);
     console.log("Autofill listener attached.");


     // === Funktion til at vise/skjule feedback iframe ===
     function toggleFeedbackEmbed() {
         // Tjek om container elementet blev fundet korrekt ved start
         if (feedbackEmbedContainer) {
             // Brug classList.toggle til at tilføje/fjerne 'hidden' klassen
             feedbackEmbedContainer.classList.toggle('hidden');
             console.log("Feedback embed toggled. Hidden state:", feedbackEmbedContainer.classList.contains('hidden'));
         } else {
             // Dette bør ikke ske hvis HTML ID er korrekt
             console.error("FEJL: Feedback embed container (#feedback-embed-container) blev ikke fundet!");
         }
     }
     // Event Listener for Feedback Toggle Knap
     // Vi tjekker om knappen findes, før vi tilføjer listener
     if (toggleFeedbackButton) {
         toggleFeedbackButton.addEventListener('click', toggleFeedbackEmbed);
         console.log("Feedback toggle listener attached.");
     } else {
         console.error("FEJL: Knappen #toggle-feedback-button blev ikke fundet!");
     }


    // === Funktion der håndterer klik på "Skab Godnathistorie" knappen ===
    async function handleGenerateClick(event) {
         event.preventDefault();
         console.log("--> handleGenerateClick started");
         // --- Indsamling af data ---
         const karakterer = [];
         document.querySelectorAll('#karakter-container .character-group').forEach(group => {
            const descInput = group.querySelector('input[name="karakter_desc"]'); const nameInput = group.querySelector('input[name="karakter_navn"]');
            const description = descInput ? descInput.value.trim() : ''; const name = nameInput ? nameInput.value.trim() : '';
            if (description) { karakterer.push({ description: description, name: name }); }
         });
         const steder = [];
         document.querySelectorAll('#sted-container .input-group input[name="sted"]').forEach(input => { const value = input.value.trim(); if (value) steder.push(value); });
         const plots = [];
         document.querySelectorAll('#plot-container .input-group input[name="plot"]').forEach(input => { const value = input.value.trim(); if (value) plots.push(value); });
         const listeners = [];
         document.querySelectorAll('#listener-container .listener-group').forEach(group => {
             const nameInput = group.querySelector('input[name="listener_name_single"]'); const ageInput = group.querySelector('input[name="listener_age_single"]');
             const name = nameInput ? nameInput.value.trim() : ''; const age = ageInput ? ageInput.value.trim() : '';
             if (name || age) { listeners.push({ name: name, age: age }); }
         });
         const selectedLaengde = laengdeSelect.value;
         const selectedMood = moodSelect.value;
         const isInteractive = interactiveCheckbox.checked;

         console.log("--- Data Indsamlet (før validering) ---");
         // ... logs for data ...
         console.log("--- Tjekker Validering ---");
         console.log("Validation skipped."); // Validering er fjernet

         // --- Forbered Data til Afsendelse ---
         const dataToSend = {
             karakterer: karakterer, steder: steder, plots: plots,
             laengde: selectedLaengde, mood: selectedMood, listeners: listeners,
             interactive: isInteractive
         };
         console.log("Data prepared for sending:", dataToSend);

         // --- Vis Loading State ---
         console.log("Setting loading state...");
         generateButton.disabled = true;
         console.log("--- LOG: Before setting textContent to 'Laver historie...'");
         generateButton.textContent = 'Laver historie...';
         console.log("--- LOG: After setting textContent to 'Laver historie...'");
         storyDisplay.textContent = '';
         resetButton.style.display = 'none';
         console.log("Loading state set.");

         // --- Asynkront Kald til Backend med Fetch API ---
         try {
             console.log("Initiating fetch call to /generate...");
             const response = await fetch('/generate', {
                 method: 'POST', // *** VIGTIGT: Denne skal være her ***
                 headers: { 'Content-Type': 'application/json' },
                 body: JSON.stringify(dataToSend),
             });
             console.log("Fetch response received. Status:", response.status);

             if (!response.ok) {
                  console.error("Server response not OK:", response.status, response.statusText);
                  let errorMsg = `Serverfejl: ${response.status} ${response.statusText}`;
                  try { const errorData = await response.json(); errorMsg += ` - ${errorData.error || JSON.stringify(errorData)}`; } catch (e) { /* Ignorer */ }
                  throw new Error(errorMsg);
             }
             console.log("Parsing JSON response...");
             const result = await response.json();
             console.log("JSON parsed successfully.");
             console.log("Displaying story...");
             storyDisplay.textContent = result.story;
             resetButton.style.display = 'inline-block';
             console.log("Story displayed, reset button shown.");
         } catch (error) {
             console.error('Fejl under generering (catch block):', error);
              storyDisplay.textContent = `Ups! Noget gik galt: ${error.message}. Tjek konsollen for detaljer.`;
         } finally {
             console.log("Executing finally block...");
             generateButton.disabled = false;
              console.log("--- LOG: Before setting textContent back to 'Skab Godnathistorie'");
              generateButton.textContent = 'Skab Godnathistorie';
              console.log("--- LOG: After setting textContent back to 'Skab Godnathistorie'");
              console.log("Loading state removed.");
         }
         console.log("--> handleGenerateClick finished");
    }

    // === Funktion der håndterer klik på "Prøv Igen" knappen ===
    function handleResetClick() {
         console.log("--> handleResetClick started");
         // Ryd alle tekst-inputfelter
         generatorSection.querySelectorAll('input[type="text"]').forEach(input => { input.value = ''; });
         console.log("Cleared text inputs.");
         // Nulstil interaktiv tjekboks
         interactiveCheckbox.checked = false;
         console.log("Reset checkbox.");
         // Funktion til at fjerne alle undtagen den første gruppe i en container
         const removeExtraGroups = (containerId, groupSelector) => {
             const container = document.getElementById(containerId);
             if (container) {
                 const groups = container.querySelectorAll(groupSelector);
                 console.log(`Found ${groups.length} groups with selector '${groupSelector}' in container '${containerId}'`);
                 for (let i = groups.length - 1; i > 0; i--) {
                     console.log(`Removing extra group at index ${i}:`, groups[i]);
                     groups[i].remove();
                 }
             } else { console.warn(`Reset: Container ${containerId} not found for selector ${groupSelector}`); }
         };
         // Fjern ekstra grupper for hver type
         removeExtraGroups('listener-container', '.listener-group');
         removeExtraGroups('karakter-container', '.character-group');
         removeExtraGroups('sted-container', '.input-group');
         removeExtraGroups('plot-container', '.input-group');
         console.log("Removed extra groups.");
         // Ryd historie-visningsområdet og skjul knap
         storyDisplay.textContent = '';
         resetButton.style.display = 'none';
         console.log("Cleared story display and hid reset button.");
         // Nulstil dropdowns
         laengdeSelect.value = 'mellem';
         moodSelect.value = 'neutral';
         console.log("Reset dropdowns.");
         console.log("--> handleResetClick finished");
    }


    // === Tilknyt funktionerne til knapperne ===
    // Vi tjekker om knapperne findes før vi tilknytter listeners for en sikkerheds skyld
    if (generateButton) {
        generateButton.addEventListener('click', handleGenerateClick);
        console.log("Generate listener attached.");
    } else { console.error("Generate button not found!"); }

    if (resetButton) {
        resetButton.addEventListener('click', handleResetClick);
        console.log("Reset listener attached.");
    } else { console.error("Reset button not found!"); }

    if (autofillButton) {
         autofillButton.addEventListener('click', autofillFields);
         console.log("Autofill listener attached.");
    } else { console.error("Autofill button not found!"); }


    console.log("Script loaded and initial listeners attached check complete.");

}); // Slut på DOMContentLoaded listener