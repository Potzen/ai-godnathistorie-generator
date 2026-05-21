// Fil: static/hygge.js
// ES6 module for the /hygge page (Godnathistorier / Højtlæsning)
import { generateStoryApi, generateAudioApi, generateImageApi, generateQuizApi, saveHojtlasningStoryApi } from './modules/api_client.js';

document.addEventListener('DOMContentLoaded', () => {

// === Tooltip System ===
const tooltipElement = document.getElementById('info-tooltip');
const tooltipTextElement = document.getElementById('info-tooltip-text');
const tooltipCloseButton = document.getElementById('info-tooltip-close');
let currentVisibleTooltipIcon = null;
let clickOpensTooltip = false;

const tooltipTexts = {
    'pro-model-info': "'Standard'-modellen er hurtig. 'Pro'-modellen er giver højere kvalitet, mere kreativitet og bedre sammenhæng i historierne. Den er dog langsommere.",
    'interactive-info': "Når denne er slået til, vil AI'en forsøge at skrive historien med 1-2 indbyggede valgmuligheder for at engagere barnet. Funktionen virker bedst, når 'Lang' historielængde er valgt.",
    'bedtime-info': "Når denne er slået til, får AI'en en specifik instruktion om at gøre historien ekstra rolig, tryg og afdæmpet. Dette overtrumfer det generelle 'Stemning'-valg og er ideelt til at hjælpe et barn med at falde til ro ved sengetid."
};

function showTooltip(iconElement, text) {
    if (!tooltipElement || !tooltipTextElement) {
        return;
    }

    tooltipTextElement.textContent = text;

    tooltipElement.classList.remove('hidden');
    tooltipElement.style.display = 'block';
    tooltipElement.style.visibility = 'hidden';
    tooltipElement.style.position = 'absolute';
    tooltipElement.style.left = '-9999px';
    tooltipElement.style.top = '-9999px';

    const tooltipWidth = tooltipElement.offsetWidth;
    const tooltipHeight = tooltipElement.offsetHeight;

    const iconRect = iconElement.getBoundingClientRect();
    let top = iconRect.bottom + window.scrollY + 8;
    let left = iconRect.left + window.scrollX + (iconRect.width / 2) - (tooltipWidth / 2);

    if (left < 10) left = 10;
    if (left + tooltipWidth > window.innerWidth - 10) left = window.innerWidth - tooltipWidth - 10;
    if (top + tooltipHeight > window.innerHeight + window.scrollY - 10) top = iconRect.top + window.scrollY - tooltipHeight - 8;
    if (top < window.scrollY + 10) top = window.scrollY + 10;

    tooltipElement.style.top = `${top}px`;
    tooltipElement.style.left = `${left}px`;
    tooltipElement.style.visibility = 'visible';
    tooltipElement.classList.add('visible');

    currentVisibleTooltipIcon = iconElement;
}

function hideTooltip() {
    if (tooltipElement) {
        tooltipElement.classList.remove('visible');
        tooltipElement.classList.add('hidden');
        tooltipElement.style.visibility = '';
        tooltipElement.style.display = '';
        tooltipElement.style.left = '';
        tooltipElement.style.top = '';
        currentVisibleTooltipIcon = null;
    }
}

function initializeInfoIcons() {
    const infoIcons = document.querySelectorAll('.info-icon');

    if (!tooltipElement) {
        return;
    }

    infoIcons.forEach(icon => {
        icon.addEventListener('click', (event) => {
            event.stopPropagation();

            const tooltipId = icon.dataset.tooltipId;
            const textToShow = tooltipTexts[tooltipId];

            if (currentVisibleTooltipIcon === icon) {
                hideTooltip();
            } else if (textToShow) {
                showTooltip(icon, textToShow);
                clickOpensTooltip = true;
            } else {
                hideTooltip();
            }
        });
    });

    if (tooltipCloseButton) {
        tooltipCloseButton.addEventListener('click', (event) => {
            event.stopPropagation();
            hideTooltip();
        });
    }

    document.addEventListener('click', (event) => {
        if (clickOpensTooltip) {
            clickOpensTooltip = false;
            return;
        }

        if (tooltipElement && tooltipElement.classList.contains('visible')) {
            if (!tooltipElement.contains(event.target)) {
                hideTooltip();
            }
        }
    });
}
// === SLUT: Tooltip System ===

// === Google Analytics Event Tracking ===
function trackGAEvent(action, category, label, value) {
    const consentStatus = localStorage.getItem('cookieConsent');
    if (consentStatus === 'accepted' && typeof gtag === 'function') {
        gtag('event', action, {
            'event_category': category,
            'event_label': label,
            'value': value
        });
    }
}

// === Font Size Controls ===
const DEFAULT_FONT_SIZE_PX = 16;
const FONT_SIZE_STEP_PX = 1;
const MIN_FONT_SIZE_PX = 10;
const MAX_FONT_SIZE_PX = 30;

let currentStoryDisplayFontSize = DEFAULT_FONT_SIZE_PX;
const STORY_DISPLAY_FONT_KEY = 'storyDisplayFontSize';

function applyFontSize(element, sizeInPx) {
    if (element) {
        element.style.fontSize = `${sizeInPx}px`;
    }
}

function saveFontSizeToLocalStorage(storageKey, sizeInPx) {
    try {
        localStorage.setItem(storageKey, sizeInPx.toString());
    } catch (e) {
        console.error("Fejl ved lagring af skriftstørrelse til LocalStorage:", e);
    }
}

function loadFontSizesFromLocalStorage() {
    try {
        const storyDisplay = document.getElementById('story-display');
        const savedStoryDisplaySize = localStorage.getItem(STORY_DISPLAY_FONT_KEY);
        if (savedStoryDisplaySize) {
            const newSize = parseInt(savedStoryDisplaySize, 10);
            if (!isNaN(newSize) && newSize >= MIN_FONT_SIZE_PX && newSize <= MAX_FONT_SIZE_PX) {
                currentStoryDisplayFontSize = newSize;
            }
        }
        applyFontSize(storyDisplay, currentStoryDisplayFontSize);
    } catch (e) {
        console.error("Fejl ved indlæsning af skriftstørrelser fra LocalStorage:", e);
    }
}

function updateFontSize(targetElement, change, reset = false, elementType) {
    let currentSize;
    let storageKey;

    if (elementType === 'storyDisplay') {
        currentSize = currentStoryDisplayFontSize;
        storageKey = STORY_DISPLAY_FONT_KEY;
    } else {
        console.error("Ukendt element type i updateFontSize:", elementType);
        return;
    }

    let newSize;
    if (reset) {
        newSize = DEFAULT_FONT_SIZE_PX;
    } else {
        newSize = currentSize + change;
    }

    newSize = Math.max(MIN_FONT_SIZE_PX, Math.min(newSize, MAX_FONT_SIZE_PX));

    if (targetElement) {
        applyFontSize(targetElement, newSize);
        if (elementType === 'storyDisplay') {
            currentStoryDisplayFontSize = newSize;
        }
        saveFontSizeToLocalStorage(storageKey, newSize);
    }
}

// === Interactive Story Switch ===
function updateInteractiveStorySwitchAvailability() {
    const aiModelSwitch = document.getElementById('ai-model-switch');
    const interactiveStorySwitch = document.getElementById('interactive-story-switch');
    if (aiModelSwitch && interactiveStorySwitch) {
        if (aiModelSwitch.disabled) {
            interactiveStorySwitch.checked = false;
            interactiveStorySwitch.disabled = true;
            return;
        }

        if (aiModelSwitch.checked) {
            interactiveStorySwitch.disabled = false;
            interactiveStorySwitch.title = "Slå til for at få interaktive valg i historien.";
        } else {
            interactiveStorySwitch.disabled = true;
            interactiveStorySwitch.checked = false;
            interactiveStorySwitch.title = "Vælg 'Pro' under 'Pro AI-Model' for at aktivere interaktiv funktion.";
        }
    } else {
        if (!aiModelSwitch) console.warn("aiModelSwitch (Pro AI) blev ikke fundet. Interaktiv switch kan ikke styres korrekt.");
        if (!interactiveStorySwitch) console.warn("interactiveStorySwitch (Interaktiv Historie) blev ikke fundet.");
    }
}

// === Example Data for Autofill ===
const exampleListeners = [ { name: "Alma", age: "5" }, { name: "Oscar", age: "7" }, { name: "Sofus", age: "3"}, { name: "Mie", age: "6" }, { name: "Noah", age: "4" }, { name: "Freja", age: "8" }, { name: "Viggo", age: "5" } ];
const exampleCharacters = [ { description: "en drilsk nisse", name: "Pip" }, { description: "en meget søvnig bjørn", name: "" }, { description: "et flyvende tæppe", name: "" }, { description: "en robot der elsker kage", name: "Kaptajn Kiks" }, { description: "en fe der har mistet sin tryllestav", name: "Flora" } ];
const examplePlaces = [ "i en skov lavet af slik", "på en øde ø med talende papegøjer", "i et omvendt hus hvor alt er på loftet", "på månen hvor ostene gror", "dybt under jorden i en krystalgrotte" ];
const examplePlots = [ "skulle finde en forsvundet stjerne", "byggede en fantastisk maskine", "holdt en overraskelsesfest", "mødte et dyr de aldrig havde set før", "lærte at trylle med farver", "'at dele er en god ting'", "'man skal være modig'", "'ærlighed varer længst'" ];

function getRandomElement(arr) {
    if (!arr || arr.length === 0) { return null; }
    return arr[Math.floor(Math.random() * arr.length)];
}

// === Dynamic Input Fields ===
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
    const karakterContainer = document.getElementById('karakter-container');
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
    } else { console.error("Karakter container (#karakter-container) not found for adding new group."); }
}

let listenerCounter = 1;
function addListenerGroup() {
    listenerCounter++;
    const listenerContainer = document.getElementById('listener-container');
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
    } else { console.error("Listener container (#listener-container) not found for adding new group."); }
    return listenerGroup;
}

// === LocalStorage for Listeners ===
function saveCurrentListeners() {
    const listenerContainer = document.getElementById('listener-container');
    const currentListeners = [];
    if (!listenerContainer) { console.error("Cannot save listeners: Listener container not found."); return; }
    listenerContainer.querySelectorAll('.listener-group').forEach(group => {
        const nameInput = group.querySelector('input[name="listener_name_single"]');
        const ageInput = group.querySelector('input[name="listener_age_single"]');
        const name = nameInput ? nameInput.value.trim() : '';
        const age = ageInput ? ageInput.value.trim() : '';
        if (name || age) {
            currentListeners.push({ name: name, age: age });
        }
    });
    try {
        if (currentListeners.length > 0) {
            localStorage.setItem('savedListeners', JSON.stringify(currentListeners));
        } else {
            localStorage.removeItem('savedListeners');
        }
    } catch (e) { console.error("Error saving listeners to LocalStorage:", e); }
}

function loadAndDisplaySavedListeners() {
    const listenerContainer = document.getElementById('listener-container');
    const savedListenersJSON = localStorage.getItem('savedListeners');
    if (savedListenersJSON) {
        try {
            const savedListeners = JSON.parse(savedListenersJSON);
            if (Array.isArray(savedListeners) && savedListeners.length > 0) {
                if (!listenerContainer) { console.error("Cannot display listeners: Listener container not found."); return false; }

                const existingGroups = listenerContainer.querySelectorAll('.listener-group');
                for (let i = existingGroups.length - 1; i > 0; i--) {
                    existingGroups[i].remove();
                }

                const firstGroup = listenerContainer.querySelector('.listener-group');
                if (!firstGroup) {
                    console.error("Initial listener group not found for loading!");
                    return false;
                }
                const firstListenerNameInput = firstGroup.querySelector('input[name="listener_name_single"]');
                const firstListenerAgeInput = firstGroup.querySelector('input[name="listener_age_single"]');

                if (firstListenerNameInput) firstListenerNameInput.value = savedListeners[0].name || '';
                if (firstListenerAgeInput) firstListenerAgeInput.value = savedListeners[0].age || '';

                if (savedListeners.length > 1) {
                    for (let i = 1; i < savedListeners.length; i++) {
                        const listenerData = savedListeners[i];
                        const newGroup = addListenerGroup();
                        if (newGroup) {
                            const newNameInput = newGroup.querySelector('input[name="listener_name_single"]');
                            const newAgeInput = newGroup.querySelector('input[name="listener_age_single"]');
                            if (newNameInput) newNameInput.value = listenerData.name || '';
                            if (newAgeInput) newAgeInput.value = listenerData.age || '';
                        }
                    }
                }
                return true;
            }
        } catch (e) {
            console.error("Error parsing saved listeners from LocalStorage:", e);
            localStorage.removeItem('savedListeners');
        }
    }
    return false;
}

// === Autofill ===
function autofillFields() {
    try {
        handleResetClick(false);
    } catch(e) {
        console.error("Autofill: Error during handleResetClick:", e);
    }

    const listenerContainer = document.getElementById('listener-container');
    const randomListener = getRandomElement(exampleListeners);
    if (randomListener && listenerContainer) {
        const firstListenerNameInput = listenerContainer.querySelector('#listener-name-1');
        const firstListenerAgeInput = listenerContainer.querySelector('#listener-age-1');
        if (firstListenerNameInput) firstListenerNameInput.value = randomListener.name;
        if (firstListenerAgeInput) firstListenerAgeInput.value = randomListener.age;
    }

    const karakterContainer = document.getElementById('karakter-container');
    const randomCharacter = getRandomElement(exampleCharacters);
    if (randomCharacter && karakterContainer) {
        const firstCharDescInput = karakterContainer.querySelector('#karakter-desc-1');
        const firstCharNameInput = karakterContainer.querySelector('#karakter-navn-1');
        if (firstCharDescInput) firstCharDescInput.value = randomCharacter.description;
        if (firstCharNameInput) firstCharNameInput.value = randomCharacter.name;
    }

    const randomPlace = getRandomElement(examplePlaces);
    const firstStedInputElem = document.querySelector('#sted-container input[name="sted"]');
    if (randomPlace && firstStedInputElem) {
        firstStedInputElem.value = randomPlace;
    }

    const randomPlot = getRandomElement(examplePlots);
    const firstPlotInputElem = document.querySelector('#plot-container input[name="plot"]');
    if (randomPlot && firstPlotInputElem) {
        firstPlotInputElem.value = randomPlot;
    }

    const negativePromptInput = document.getElementById('negative-prompt-input');
    if (negativePromptInput) negativePromptInput.value = '';
}

// === Reset Function ===
function handleResetClick(clearLocalStorageForListeners = true) {
    const generatorSection = document.getElementById('generator');
    const storyDisplay = document.getElementById('story-display');
    const storySectionHeading = document.getElementById('story-section-heading');
    const storyShareButtonsContainer = document.getElementById('story-share-buttons');
    const audioPlayer = document.getElementById('audio-player');
    const audioLoadingDiv = document.getElementById('audio-loading');
    const audioErrorDiv = document.getElementById('audio-error');
    const loginPromptAudio = document.getElementById('login-prompt-audio');
    const laengdeSelect = document.getElementById('laengde-select');
    const moodSelect = document.getElementById('mood-select');
    const resetButton = document.getElementById('reset-button');

    if (generatorSection) {
        generatorSection.querySelectorAll('input[type="text"], textarea').forEach(input => {
            if (!input.closest('#listener-container')) {
                input.value = '';
            }
        });
    }

    const removeExtraGroups = (containerId, groupSelector) => {
        const container = document.getElementById(containerId);
        if (container) {
            const groups = container.querySelectorAll(groupSelector);
            for (let i = groups.length - 1; i > 0; i--) { groups[i].remove(); }
        }
    };
    if (clearLocalStorageForListeners) {
        removeExtraGroups('listener-container', '.listener-group');
    }
    removeExtraGroups('karakter-container', '.character-group');
    removeExtraGroups('sted-container', '.input-group');
    removeExtraGroups('plot-container', '.input-group');

    if (storyDisplay) storyDisplay.textContent = '';
    if (storySectionHeading) storySectionHeading.textContent = 'Jeres historie';
    if (resetButton && storyShareButtonsContainer) {
        const innerReset = storyShareButtonsContainer.querySelector('#reset-button');
        if (innerReset) innerReset.style.display = 'none';
    }
    if (storyShareButtonsContainer) storyShareButtonsContainer.classList.add('hidden');

    if (audioPlayer) { audioPlayer.pause(); audioPlayer.src = ''; audioPlayer.classList.add('hidden'); }
    if (audioLoadingDiv) audioLoadingDiv.classList.add('hidden');
    if (audioErrorDiv) { audioErrorDiv.textContent = ''; audioErrorDiv.classList.add('hidden'); }
    if (loginPromptAudio) loginPromptAudio.classList.add('hidden');

    if (laengdeSelect) laengdeSelect.value = 'kort';
    if (moodSelect) moodSelect.value = 'neutral';

    if (clearLocalStorageForListeners) {
        try {
            localStorage.removeItem('savedListeners');
        } catch (e) {
            console.error("Reset: Error removing listeners from LocalStorage:", e);
        }
    }
}

// === Story Sharing Input Helper ===
function getStoryInputsForSharing() {
    const storySectionHeading = document.getElementById('story-section-heading');
    const moodSelect = document.getElementById('mood-select');
    const førsteKarakterDescInput = document.getElementById('karakter-desc-1');
    const førsteKarakterNavnInput = document.getElementById('karakter-navn-1');
    const førsteStedInput = document.getElementById('sted-input-1');
    const førstePlotInput = document.getElementById('plot-input-1');

    const inputs = {
        titel: "Jeres historie",
        karakterBeskrivelse: '',
        karakterNavn: '',
        sted: '',
        plot: '',
        stemning: ''
    };

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

// === Generate Story ===
async function handleGenerateClick(event) {
    event.preventDefault();

    const generateButton = document.getElementById('generate-button');
    const aiModelSwitch = document.getElementById('ai-model-switch');

    const karakterer = Array.from(document.getElementById('karakter-container').querySelectorAll('.character-group')).map(g => ({ description: g.querySelector('input[name="karakter_desc"]').value.trim(), name: g.querySelector('input[name="karakter_navn"]').value.trim() })).filter(k => k.description);
    const steder = Array.from(document.querySelectorAll('#sted-container input[name="sted"]')).map(i => i.value.trim()).filter(Boolean);
    const plots = Array.from(document.querySelectorAll('#plot-container input[name="plot"]')).map(i => i.value.trim()).filter(Boolean);
    const listeners = Array.from(document.getElementById('listener-container').querySelectorAll('.listener-group')).map(g => ({ name: g.querySelector('input[name="listener_name_single"]').value.trim(), age: g.querySelector('input[name="listener_age_single"]').value.trim() })).filter(l => l.name || l.age);
    const dataToSend = {
        karakterer, steder, plots, listeners,
        laengde: document.getElementById('laengde-select').value,
        mood: document.getElementById('mood-select').value,
        interactive: document.getElementById('interactive-story-switch').checked,
        is_bedtime_story: document.getElementById('bedtime-story-switch').checked,
        negative_prompt: document.getElementById('negative-prompt-input').value.trim(),
        selected_model: (aiModelSwitch && !aiModelSwitch.disabled && aiModelSwitch.checked) ? 'gemini-2.5-pro-preview-06-05' : 'gemini-1.5-flash-latest'
    };
    saveCurrentListeners();

    if (generateButton) { generateButton.disabled = true; generateButton.textContent = 'Laver historie...'; }

    const storyDisplay = document.getElementById('story-display');
    const storySectionHeading = document.getElementById('story-section-heading');
    const storyShareButtonsContainer = document.getElementById('story-share-buttons');
    const audioPlayer = document.getElementById('audio-player');

    if (storyDisplay) {
        storyDisplay.innerHTML = `
            <div id="story-loading-indicator">
                <p>Historien genereres... Vent venligst.</p>
                <span class="spinner"></span>
            </div>
        `;
    }
    if (storySectionHeading) storySectionHeading.textContent = 'Jeres historie';
    if (storyShareButtonsContainer) storyShareButtonsContainer.classList.add('hidden');
    if (audioPlayer) { audioPlayer.classList.add('hidden'); audioPlayer.src = ''; }
    document.querySelectorAll('.js-generate-image').forEach(button => button.disabled = true);

    try {
        const result = await generateStoryApi(dataToSend);
        if (result.error) throw new Error(result.error);

        trackGAEvent('generate_story', 'Højtlæsning', `Mood: ${dataToSend.mood} - Length: ${dataToSend.laengde}`, null);

        const cleanTitle = (result.title || "Jeres historie").trim();
        const cleanStory = (result.story || "Modtog en tom historie.").replace(/^\s+/, '');

        if (storyDisplay) {
            storyDisplay.innerHTML = '';
            const newStoryContentDiv = document.createElement('div');
            newStoryContentDiv.id = 'story-text-content';
            newStoryContentDiv.textContent = cleanStory;
            storyDisplay.appendChild(newStoryContentDiv);
        }

        if (storySectionHeading) storySectionHeading.textContent = cleanTitle;
        if (storyShareButtonsContainer && cleanStory) storyShareButtonsContainer.classList.remove('hidden');

        const userRole = document.getElementById('current-user-role-data')?.dataset.role || 'guest';
        document.querySelectorAll('.js-generate-image').forEach(button => {
            if (userRole !== 'guest' && cleanStory) {
                button.disabled = false;
                button.removeAttribute('title');
            }
        });

    } catch (error) {
        if (storyDisplay) storyDisplay.innerHTML = `<p style="color: red; text-align: center;">Ups! Noget gik galt: ${error.message}.</p>`;
        if (storySectionHeading) storySectionHeading.textContent = "Fejl ved generering";
    } finally {
        if (generateButton) { generateButton.disabled = false; generateButton.textContent = 'Skab Historie'; }
    }
}

// === Quiz ===
function renderQuiz(quizData) {
    if (!quizSektion || !quizContainer) return;
    currentQuizData = quizData;
    correctAnswersCount = 0;
    quizContainer.innerHTML = '';
    quizFeedback.classList.add('hidden');

    quizData.forEach((q, index) => {
        const questionEl = document.createElement('div');
        questionEl.className = 'quiz-question-block';
        questionEl.style.marginBottom = '25px';

        const questionText = document.createElement('p');
        questionText.style.fontWeight = 'bold';
        questionText.textContent = `${index + 1}. ${q.question}`;

        const optionsEl = document.createElement('div');
        optionsEl.className = 'quiz-options';
        optionsEl.style.display = 'flex';
        optionsEl.style.flexDirection = 'column';
        optionsEl.style.gap = '10px';

        q.options.forEach((option, optionIndex) => {
            const optionBtn = document.createElement('button');
            optionBtn.className = 'utility-button';
            optionBtn.textContent = option;
            optionBtn.dataset.qIndex = index;
            optionBtn.dataset.oIndex = optionIndex;
            optionBtn.onclick = checkAnswer;
            optionsEl.appendChild(optionBtn);
        });

        questionEl.append(questionText, optionsEl);
        quizContainer.appendChild(questionEl);
    });
    quizSektion.classList.remove('hidden');
}

function checkAnswer(event) {
    const btn = event.target;
    const qIndex = parseInt(btn.dataset.qIndex, 10);
    const oIndex = parseInt(btn.dataset.oIndex, 10);

    const questionData = currentQuizData[qIndex];
    const parentOptions = btn.parentElement;

    parentOptions.querySelectorAll('button').forEach(button => button.disabled = true);

    if (oIndex === questionData.correct_answer_index) {
        btn.style.backgroundColor = 'var(--color-success-bg)';
        btn.style.borderColor = 'var(--color-success-border)';
        btn.style.color = 'var(--color-success-text)';
        correctAnswersCount++;
    } else {
        btn.style.backgroundColor = 'var(--color-error-bg)';
        btn.style.borderColor = 'var(--color-error-border)';
        btn.style.color = 'var(--color-error-text)';
        parentOptions.children[questionData.correct_answer_index].style.backgroundColor = 'var(--color-success-bg)';
    }

    if (correctAnswersCount === currentQuizData.length) {
        quizFeedback.textContent = "Fantastisk! Du har svaret rigtigt på alt. Du kan nu generere et billede til historien.";
        quizFeedback.className = 'flash-message flash-success';
        quizFeedback.classList.remove('hidden');

        document.getElementById('dynamic-quiz-reward-button')?.remove();

        const rewardButton = document.createElement('button');
        rewardButton.id = 'dynamic-quiz-reward-button';
        rewardButton.type = 'button';
        rewardButton.textContent = 'Generer Billede';
        rewardButton.className = 'utility-button quiz-success-button';

        rewardButton.addEventListener('click', handleGenerateImageFromStoryClick);

        quizFeedback.insertAdjacentElement('afterend', rewardButton);
    }
}

async function fetchAndDisplayQuiz(storyContent, lixScore) {
    if (!quizSektion || !quizContainer) return;
    quizSektion.classList.remove('hidden');
    quizContainer.innerHTML = '<p>Genererer quiz, vent venligst...</p>';

    try {
        const data = await generateQuizApi(storyContent, lixScore);
        if (data.questions && data.questions.length > 0) {
            renderQuiz(data.questions);
        } else {
            throw new Error("Modtog en tom quiz fra serveren.");
        }
    } catch (error) {
        console.error("Fejl under hentning af quiz:", error);
        quizContainer.innerHTML = `<p style="color:red;">Kunne ikke oprette en quiz til denne historie.</p>`;
    }
}

// === Read Aloud (TTS) ===
async function handleReadAloudClick() {
    const readAloudButton = document.getElementById('read-aloud-button');
    const audioLoadingDiv = document.getElementById('audio-loading');
    const audioErrorDiv = document.getElementById('audio-error');
    const audioPlayer = document.getElementById('audio-player');
    const loginPromptAudio = document.getElementById('login-prompt-audio');
    const ttsVoiceSelect = document.getElementById('tts-voice-select');

    if (readAloudButton.classList.contains('disabled-button')) {
        if (loginPromptAudio) {
            loginPromptAudio.classList.remove('hidden');
            setTimeout(() => loginPromptAudio.classList.add('hidden'), 5000);
        }
        return;
    }

    const storyTextContent = document.getElementById('story-text-content');
    const storyText = storyTextContent ? storyTextContent.textContent.trim() : "";

    if (!storyText || storyText === '' || storyText.includes('Historien genereres...')) {
        if (audioErrorDiv) {
            audioErrorDiv.textContent = "Ingen historie at læse højt.";
            audioErrorDiv.classList.remove('hidden');
            setTimeout(() => audioErrorDiv.classList.add('hidden'), 3000);
        }
        return;
    }

    if (!audioLoadingDiv || !audioErrorDiv || !audioPlayer || !ttsVoiceSelect) {
        console.error("Read Aloud: Critical audio or voice selection elements missing from DOM.");
        if (audioErrorDiv) {
            audioErrorDiv.textContent = "Fejl: Nødvendige elementer mangler (kontakt support).";
            audioErrorDiv.classList.remove('hidden');
        }
        return;
    }

    const selectedVoice = ttsVoiceSelect.value;

    trackGAEvent('play_audio', 'Højtlæsning', `Voice: ${selectedVoice}`, null);

    if (audioLoadingDiv) audioLoadingDiv.classList.remove('hidden');
    if (audioErrorDiv) { audioErrorDiv.textContent = ''; audioErrorDiv.classList.add('hidden'); }
    if (audioPlayer) { audioPlayer.pause(); audioPlayer.src = ''; audioPlayer.classList.add('hidden'); }
    if (readAloudButton) { readAloudButton.disabled = true; readAloudButton.textContent = 'Genererer Lyd...'; }

    try {
        const response = await generateAudioApi(storyText, selectedVoice);
        const mediaSource = new MediaSource();
        audioPlayer.src = URL.createObjectURL(mediaSource);
        audioPlayer.classList.remove('hidden');

        mediaSource.addEventListener('sourceopen', async () => {
            const sourceBuffer = mediaSource.addSourceBuffer('audio/mpeg');
            const reader = response.body.getReader();

            const appendBuffer = async (buffer) => {
                return new Promise((resolve, reject) => {
                    sourceBuffer.addEventListener('updateend', () => resolve(), { once: true });
                    sourceBuffer.addEventListener('error', (e) => reject(e), { once: true });
                    sourceBuffer.appendBuffer(buffer);
                });
            };

            while (true) {
                const { done, value } = await reader.read();
                if (done) {
                    const waitForUpdateEnd = () => {
                        return new Promise(resolve => {
                            if (!sourceBuffer.updating) {
                                resolve();
                            } else {
                                sourceBuffer.addEventListener('updateend', () => resolve(), { once: true });
                            }
                        });
                    };

                    await waitForUpdateEnd();

                    if (mediaSource.readyState === 'open') {
                        mediaSource.endOfStream();
                    }
                    break;
                }
                if (value) {
                    await appendBuffer(value);
                }
            }
        });

        mediaSource.addEventListener('sourceended', () => {});
        mediaSource.addEventListener('error', (event) => {
            console.error('MediaSource error:', event);
            if (audioErrorDiv) {
                audioErrorDiv.textContent = 'Fejl under afspilning af lydstream.';
                audioErrorDiv.classList.remove('hidden');
            }
            if (audioPlayer) audioPlayer.classList.add('hidden');
        });

    } catch (error) {
        console.error("Read Aloud: Error during audio generation or streaming:", error);
        if (audioErrorDiv) {
            audioErrorDiv.textContent = `Lydfejl: ${error.message}`;
            audioErrorDiv.classList.remove('hidden');
        }
        if (audioPlayer) audioPlayer.classList.add('hidden');
    } finally {
        if (audioLoadingDiv) audioLoadingDiv.classList.add('hidden');
        if (readAloudButton) {
            readAloudButton.disabled = false;
            readAloudButton.textContent = 'Læs Historien Højt';
        }
    }
}

// === Generate Image from Story ===
async function handleGenerateImageFromStoryClick() {
    const imageSection = document.getElementById('billede-til-historien-sektion');
    const storyImageContainer = document.getElementById('story-image-container');
    const storyImageLoader = document.getElementById('story-image-loader');
    const storyImageDisplay = document.getElementById('story-image-display');
    const storyImageError = document.getElementById('story-image-error');
    const generateImageButtons = document.querySelectorAll('.js-generate-image');

    const storyContentElement = document.getElementById('story-text-content');

    const currentStoryText = storyContentElement ? storyContentElement.textContent.trim() : "";
    if (!currentStoryText) {
        alert("Generer venligst en historie først.");
        return;
    }

    const karakterer = [];
    document.querySelectorAll('#karakter-container .character-group').forEach(group => {
        const descInput = group.querySelector('input[name="karakter_desc"]');
        const nameInput = group.querySelector('input[name="karakter_navn"]');
        if (descInput && descInput.value.trim()) {
            karakterer.push({
                description: descInput.value.trim(),
                name: nameInput ? nameInput.value.trim() : ''
            });
        }
    });

    const steder = [];
    document.querySelectorAll('#sted-container .input-group input[name="sted"]').forEach(input => {
        const v = input.value.trim();
        if (v) steder.push(v);
    });

    if (imageSection) imageSection.classList.remove('hidden');
    if (storyImageContainer) storyImageContainer.classList.remove('hidden');
    if (storyImageLoader) storyImageLoader.classList.remove('hidden');
    if (storyImageDisplay) storyImageDisplay.classList.add('hidden');
    if (storyImageError) storyImageError.classList.add('hidden');
    generateImageButtons.forEach(button => button.disabled = true);

    try {
        const dataToSend = {
            story_text: currentStoryText,
            karakterer: karakterer,
            steder: steder
        };

        trackGAEvent('generate_image', 'Højtlæsning', 'Success', null);

        const result = await generateImageApi(dataToSend);

        if (result.image_url) {
            if (storyImageDisplay) {
                storyImageDisplay.src = result.image_url;
                storyImageDisplay.classList.remove('hidden');
            }
        } else {
            throw new Error(result.error || "Uventet svar fra serveren.");
        }
    } catch (error) {
        if (storyImageError) {
            storyImageError.textContent = `Fejl: ${error.message}`;
            storyImageError.classList.remove('hidden');
        }
    } finally {
        if (storyImageLoader) storyImageLoader.classList.add('hidden');
        generateImageButtons.forEach(button => button.disabled = false);
    }
}

// === Quiz & Image state variables (module-scope inside DOMContentLoaded) ===
const quizSektion = document.getElementById('quiz-sektion');
const quizContainer = document.getElementById('quiz-container');
const quizFeedback = document.getElementById('quiz-feedback');
let currentQuizData = [];
let correctAnswersCount = 0;

// === Font sizes ===
loadFontSizesFromLocalStorage();

// === Failure info dropdown ===
const failureInfoDropdownToggle = document.getElementById('failure-info-dropdown-toggle');
const failureInfoDropdownContent = document.getElementById('failure-info-dropdown-content');
if (failureInfoDropdownToggle && failureInfoDropdownContent) {
    failureInfoDropdownToggle.addEventListener('click', () => {
        failureInfoDropdownContent.classList.toggle('hidden');
        failureInfoDropdownToggle.classList.toggle('open');
    });
}

// === Interactive switch availability ===
updateInteractiveStorySwitchAvailability();
const aiModelSwitch = document.getElementById('ai-model-switch');
if (aiModelSwitch) aiModelSwitch.addEventListener('change', updateInteractiveStorySwitchAvailability);

// === Bedtime story switch: show/hide song section ===
const bedtimeStorySwitch = document.getElementById('bedtime-story-switch');
const sangteksterSektion = document.getElementById('sangtekster-sektion');
if (bedtimeStorySwitch && sangteksterSektion) {
    const updateSongVisibility = () => sangteksterSektion.classList.toggle('hidden', !bedtimeStorySwitch.checked);
    bedtimeStorySwitch.addEventListener('change', updateSongVisibility);
    updateSongVisibility();
}

// === Load saved listeners ===
loadAndDisplaySavedListeners();

// === Generate button ===
const generateButton = document.getElementById('generate-button');
if (generateButton) generateButton.addEventListener('click', handleGenerateClick);

// === Reset button ===
const storyShareButtonsContainer = document.getElementById('story-share-buttons');
if (storyShareButtonsContainer) {
    const innerReset = storyShareButtonsContainer.querySelector('#reset-button');
    if (innerReset) innerReset.addEventListener('click', () => handleResetClick(false));
}

// === Autofill button ===
const autofillButton = document.getElementById('autofill-button');
if (autofillButton) autofillButton.addEventListener('click', autofillFields);

// === Add listener button ===
const addListenerButton = document.getElementById('add-listener-button');
if (addListenerButton) addListenerButton.addEventListener('click', addListenerGroup);

// === Add character button ===
const addKarakterButton = document.getElementById('add-karakter-button');
if (addKarakterButton) addKarakterButton.addEventListener('click', addCharacterGroup);

// === Generic add buttons for sted/plot ===
document.querySelectorAll('#generator .add-button[data-container]').forEach(button => {
    button.addEventListener('click', () => {
        const containerId = button.dataset.container;
        const placeholder = button.dataset.placeholder;
        const inputName = button.dataset.name;
        if (containerId && placeholder && inputName) addInputField(containerId, placeholder, inputName);
    });
});

// === Read aloud button ===
const readAloudButton = document.getElementById('read-aloud-button');
if (readAloudButton) readAloudButton.addEventListener('click', handleReadAloudClick);

// === Image buttons ===
const hojtlaesningImageButton = document.getElementById('generate-image-from-output-button');
if (hojtlaesningImageButton) hojtlaesningImageButton.addEventListener('click', handleGenerateImageFromStoryClick);
document.querySelectorAll('.js-generate-image:not(#generate-image-from-output-button)').forEach(btn => {
    if (!btn.disabled) btn.addEventListener('click', handleGenerateImageFromStoryClick);
});

// === Feedback toggle ===
const toggleFeedbackButton = document.getElementById('toggle-feedback-button');
const feedbackEmbedContainer = document.getElementById('feedback-embed-container');
if (toggleFeedbackButton && feedbackEmbedContainer) {
    toggleFeedbackButton.addEventListener('click', () => feedbackEmbedContainer.classList.toggle('hidden'));
}

// === Save to Logbook button ===
const saveToLogbookButton = document.getElementById('save-to-logbook-button');
if (saveToLogbookButton) {
    saveToLogbookButton.addEventListener('click', async () => {
        const titleElement = document.getElementById('story-section-heading');
        const contentElement = document.getElementById('story-text-content');
        const title = titleElement ? titleElement.textContent.replace(/LIX: \d+/, '').trim() : "Uden Titel";
        const content = contentElement ? contentElement.textContent.trim() : "";
        if (!content) { alert("Der er ingen historie at gemme."); return; }
        saveToLogbookButton.disabled = true;
        saveToLogbookButton.textContent = 'Gemmer...';
        try {
            const result = await saveHojtlasningStoryApi({ title, content });
            if (result.success) trackGAEvent('save_to_logbook', 'Højtlæsning', `Story ID: ${result.story_id}`, null);
            saveToLogbookButton.textContent = 'Gemt!';
            saveToLogbookButton.style.backgroundColor = '#28a745';
        } catch (error) {
            console.error("Fejl ved gemning til logbog:", error);
            alert(`Kunne ikke gemme historien: ${error.message}`);
            saveToLogbookButton.disabled = false;
            saveToLogbookButton.textContent = 'Gem i Logbog';
        }
    });
}

// === Share to Facebook ===
const shareStoryFacebookButton = document.getElementById('share-story-facebook-button');
if (shareStoryFacebookButton) {
    shareStoryFacebookButton.addEventListener('click', () => {
        const storyData = getStoryInputsForSharing();
        const storyDisplay = document.getElementById('story-display');
        const storyText = storyDisplay ? storyDisplay.textContent : "";
        const appURL = window.location.origin;

        let quoteParts = [];
        quoteParts.push(`Jeg har lige lavet en historie: "${storyData.titel}"`);
        if (storyData.karakterBeskrivelse) {
            let karakter = storyData.karakterBeskrivelse;
            if (storyData.karakterNavn) karakter += ` ved navn ${storyData.karakterNavn}`;
            quoteParts.push(`Hovedperson: ${karakter}.`);
        }
        if (storyData.sted) quoteParts.push(`Sted: ${storyData.sted}.`);
        const snippet = storyText.substring(0, 120) + (storyText.length > 120 ? "..." : "");
        if (snippet) quoteParts.push(`Uddrag: "${snippet}"`);
        quoteParts.push(`Prøv selv på Read Me A Story!`);

        const quote = encodeURIComponent(quoteParts.join(' '));
        const encodedAppURL = encodeURIComponent(appURL);
        const facebookShareURL = `https://www.facebook.com/sharer/sharer.php?u=${encodedAppURL}&quote=${quote}&hashtag=%23ReadMeAStory`;

        window.open(facebookShareURL, '_blank', 'width=600,height=400,noopener,noreferrer');
    });
}

// === Copy Story button ===
const copyStoryButton = document.getElementById('copy-story-button');
if (copyStoryButton) {
    copyStoryButton.addEventListener('click', async () => {
        const storyData = getStoryInputsForSharing();
        const storyDisplay = document.getElementById('story-display');
        const storyText = storyDisplay ? storyDisplay.textContent : "";
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
        } catch (err) {
            console.error('Failed to copy story to clipboard: ', err);
            alert('Kunne ikke kopiere automatisk. Prøv evt. at markere og kopiere teksten manuelt.');
        }
    });
}

// === Font size buttons ===
const storyDisplay = document.getElementById('story-display');
const decreaseFontButton = document.getElementById('decrease-font-button');
const increaseFontButton = document.getElementById('increase-font-button');
const resetFontButton = document.getElementById('reset-font-button');
if (decreaseFontButton && storyDisplay) decreaseFontButton.addEventListener('click', () => updateFontSize(storyDisplay, -FONT_SIZE_STEP_PX, false, 'storyDisplay'));
if (increaseFontButton && storyDisplay) increaseFontButton.addEventListener('click', () => updateFontSize(storyDisplay, FONT_SIZE_STEP_PX, false, 'storyDisplay'));
if (resetFontButton && storyDisplay) resetFontButton.addEventListener('click', () => updateFontSize(storyDisplay, 0, true, 'storyDisplay'));

// === Info icons (tooltips) ===
initializeInfoIcons();

// === GA page view (cookie consent handled by base.html) ===
const consentStatus = localStorage.getItem('cookieConsent');
if (consentStatus === 'accepted') {
    if (typeof gtag === 'function') gtag('event', 'page_view', { page_path: window.location.pathname });
}

}); // end DOMContentLoaded
