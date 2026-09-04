// Fil: static/stoette.js
// ES6 module for /stoette page (Narrativ Støtte)

import { generateNarrativeStoryApi, suggestCharacterTraitsApi, getGuidingQuestionsApi, analyzeStoryForLogbookApi, saveLogbookEntryApi, listContinuableStoriesApi, generateNarrativeStoryImageApi, generateProblemImageApi, listChildProfilesApi, saveChildProfileApi, deleteChildProfileApi } from './modules/api_client.js';

// Debug-logning er slaaet fra i produktion. Kaldene nedenfor dumpede hele
// dataobjekter - herunder den narrative analyse af barnet - til browserens
// konsol ved hver handling. Saet 'rmas_debug' i localStorage for at slaa dem
// til under udvikling:  localStorage.setItem('rmas_debug', '1')
const DEBUG = (() => {
    try { return localStorage.getItem('rmas_debug') === '1'; } catch { return false; }
})();
const debugLog = (...args) => { if (DEBUG) console.log(...args); };

document.addEventListener('DOMContentLoaded', () => {

    // === Module-level state ===
    let currentNarrativeData = null;
    let allProfilesData = [];

    // === Image element references ===
    const imageSection = document.getElementById('billede-til-historien-sektion');
    const storyImageContainer = document.getElementById('story-image-container');
    const storyImageLoader = document.getElementById('story-image-loader');
    const storyImageDisplay = document.getElementById('story-image-display');
    const storyImageError = document.getElementById('story-image-error');
    const problemImageContainer = document.getElementById('problem-image-container');
    const problemImageLoader = document.getElementById('problem-image-loader');
    const problemImageDisplay = document.getElementById('problem-image-display');
    const problemImageError = document.getElementById('problem-image-error');

    // === Tooltip system ===
    const tooltipElement = document.getElementById('info-tooltip');
    const tooltipTextElement = document.getElementById('info-tooltip-text');
    const tooltipCloseButton = document.getElementById('info-tooltip-close');
    let currentVisibleTooltipIcon = null;
    let clickOpensTooltip = false;

    const tooltipTexts = {
        'tooltip-narrative-focus': "Tip: Angiv her den centrale begivenhed, udfordring eller det fokus, historien skal omhandle. Det kan være en følelse (f.eks. generthed), en konkret situation (f.eks. 'svært ved at dele') eller en kommende begivenhed (f.eks. 'skolestart', 'en flytning'). En præcis beskrivelse hjælper AI'en med at skabe en målrettet historie.",
        'tooltip-narrative-goal': "Tip: Formulér her det ønskede mål med historien. Sigtepunktet kan være en positiv forandring, en ny forståelse eller en specifik indsigt, som historien skal understøtte hos barnet i relation til den centrale begivenhed/udfordring. Dette hjælper AI'en med at skabe et meningsfuldt og styrkende budskab i fortællingen.",
        'tooltip-child-strengths': "Tip: Beskriv dit barns positive egenskaber, eller hvad barnet holder af at gøre. Disse styrker kan flettes ind i historien som 'superkræfter', der hjælper hovedpersonen med at overvinde udfordringer. Dette kan bidrage til at styrke barnets selvværd og oplevelse af handlekraft."
    };

    function showTooltip(iconElement, text) {
        if (!tooltipElement || !tooltipTextElement) {
            console.error("FEJL: Tooltip HTML elementerne blev ikke fundet!");
            return;
        }
        debugLog("showTooltip FORSØGER for:", iconElement.dataset.tooltipId);

        tooltipTextElement.textContent = text;

        tooltipElement.classList.remove('hidden');
        tooltipElement.style.display = 'block';
        tooltipElement.style.visibility = 'hidden';
        tooltipElement.style.position = 'absolute';
        tooltipElement.style.left = '-9999px';
        tooltipElement.style.top = '-9999px';

        const tooltipWidth = tooltipElement.offsetWidth;
        const tooltipHeight = tooltipElement.offsetHeight;
        debugLog("Tooltip dimensioner målt: Bredde =", tooltipWidth, "Højde =", tooltipHeight);

        if (tooltipWidth === 0 && tooltipHeight === 0 && text.length > 0) {
            console.warn("ADVARSEL: Tooltip har stadig 0x0 dimensioner, selvom display='block' og visibility='hidden' blev sat. Tjek CSS for #info-tooltip for konflikter (f.eks. !important). Tekstlængde:", text.length);
        }

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

        debugLog("Tooltip SKULLE NU VÆRE SYNLIG OG POSITIONERET ved: top=", Math.round(top), "left=", Math.round(left));
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
            debugLog("Tooltip skjult.");
        }
    }

    function initializeInfoIcons() {
        const infoIcons = document.querySelectorAll('.info-icon');
        debugLog(`Fandt ${infoIcons.length} .info-icon elementer.`);

        if (!tooltipElement) {
            console.error("FEJL: Det primære tooltip-element (#info-tooltip) blev ikke fundet.");
            return;
        }

        infoIcons.forEach(icon => {
            icon.addEventListener('click', (event) => {
                event.stopPropagation();

                const tooltipId = icon.dataset.tooltipId;
                const textToShow = tooltipTexts[tooltipId];
                debugLog("Info-ikon klikket. ID:", tooltipId);

                if (currentVisibleTooltipIcon === icon) {
                    debugLog("Samme ikon klikket, skjuler aktiv tooltip.");
                    hideTooltip();
                } else if (textToShow) {
                    debugLog("Viser ny tooltip for:", tooltipId);
                    showTooltip(icon, textToShow);
                    clickOpensTooltip = true;
                } else {
                    console.warn(`Ingen hjælpetekst fundet for ID: ${tooltipId}`);
                    hideTooltip();
                }
            });
        });

        if (tooltipCloseButton) {
            tooltipCloseButton.addEventListener('click', (event) => {
                event.stopPropagation();
                debugLog("Tooltip luk-knap klikket.");
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
                    debugLog("Klik udenfor aktiv tooltip. Skjuler tooltip.");
                    hideTooltip();
                }
            }
        });

        if (infoIcons.length > 0) {
            debugLog("Info ikon event listeners initialiseret (version 3).");
        }
    }

    // === Google Analytics event tracking ===
    function trackGAEvent(action, category, label, value) {
        const consentStatus = localStorage.getItem('cookieConsent');
        if (consentStatus === 'accepted' && typeof gtag === 'function') {
            debugLog(`GA Event: Action='${action}', Category='${category}', Label='${label}'` + (value !== undefined ? `, Value=${value}` : ''));
            gtag('event', action, {
                'event_category': category,
                'event_label': label,
                'value': value
            });
        } else if (consentStatus !== 'accepted') {
            debugLog(`GA Event not sent (consent not accepted): Action='${action}', Category='${category}', Label='${label}'`);
        } else if (typeof gtag !== 'function') {
            console.warn(`GA Event not sent (gtag function not found): Action='${action}', Category='${category}', Label='${label}'`);
        }
    }

    // === Font size constants ===
    const DEFAULT_FONT_SIZE_PX = 19;
    const FONT_SIZE_STEP_PX = 2;
    const MIN_FONT_SIZE_PX = 14;
    const MAX_FONT_SIZE_PX = 34;
    const NARRATIVE_STORY_FONT_KEY = 'narrativeStoryFontSize';

    let currentNarrativeStoryFontSize = DEFAULT_FONT_SIZE_PX;

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

    function updateFontSize(targetElement, change, reset = false, elementType) {
        let currentSize;
        let storageKey;

        if (elementType === 'narrativeStory') {
            currentSize = currentNarrativeStoryFontSize;
            storageKey = NARRATIVE_STORY_FONT_KEY;
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
            if (elementType === 'narrativeStory') {
                currentNarrativeStoryFontSize = newSize;
            }
            saveFontSizeToLocalStorage(storageKey, newSize);
        }
    }

    // === Element references ===
    const narrativeGenerateStoryButton = document.getElementById('narrative-generate-story-button');
    const narrativeSuggestTraitsButton = document.getElementById('narrative-suggest-traits-button');
    const narrativeGenerateImagesButton = document.getElementById('narrative-generate-images-button');
    const narrativeFocusInput = document.getElementById('narrative-focus-input');
    const narrativeGoalInput = document.getElementById('narrative-goal-input');
    const narrativeChildNameInput = document.getElementById('narrative-child-name-1');
    const narrativeChildAgeInput = document.getElementById('narrative-child-age-1');
    const narrativeChildStrengthsSelect = document.getElementById('narrative-child-strengths-select');
    const narrativeChildStrengthsOther = document.getElementById('narrative-child-strengths-other');
    const narrativeChildValuesSelect = document.getElementById('narrative-child-values-select');
    const narrativeChildValuesOther = document.getElementById('narrative-child-values-other');
    const narrativeChildMotivationInput = document.getElementById('narrative-child-motivation');
    const narrativeChildReactionTextarea = document.getElementById('narrative-child-reaction');

    const narrativeProblemIdentityNameInput = document.getElementById('narrative-problem-identity-name');
    const narrativeProblemRoleFunctionInput = document.getElementById('narrative-problem-role-function');
    const narrativeProblemPurposeIntentionInput = document.getElementById('narrative-problem-purpose-intention');
    const narrativeProblemBehaviorActionInput = document.getElementById('narrative-problem-behavior-action');
    const narrativeProblemInfluenceInput = document.getElementById('narrative-problem-influence');

    const narrativeRelationsContainer = document.getElementById('narrative-relations-container');
    const narrativeMainCharactersContainer = document.getElementById('narrative-main-characters-container');
    const narrativePlacesContainer = document.getElementById('narrative-places-container');
    const narrativePlotContainer = document.getElementById('narrative-plot-container');
    const narrativeNegativePromptInput = document.getElementById('narrative-negative-prompt-input');
    const narrativeLengthSelect = document.getElementById('narrative-length-select');
    const narrativeMoodSelect = document.getElementById('narrative-mood-select');

    const narrativeLoadingIndicator = document.getElementById('narrative-loading-indicator');
    const narrativeErrorDisplay = document.getElementById('narrative-error-display');
    const narrativeGeneratedStorySection = document.getElementById('narrative-generated-story-section');
    const narrativeGeneratedTitle = document.getElementById('narrative-generated-title');
    const narrativeGeneratedStory = document.getElementById('narrative-generated-story');

    const narrativeDecreaseFontButton = document.getElementById('narrative-decrease-font-button');
    const narrativeIncreaseFontButton = document.getElementById('narrative-increase-font-button');
    const narrativeResetFontButton = document.getElementById('narrative-reset-font-button');
    const narrativeStoryEl = document.getElementById('narrative-generated-story');

    const continueStorySwitch = document.getElementById('continue-story-switch');
    const continuationOptions = document.getElementById('continuation-options');
    const parentStorySelect = document.getElementById('parent-story-select');
    const strategySelection = document.getElementById('continuation-strategy-selection');

    const logbookSection = document.getElementById('logbook-documentation-section');
    const logbookLoader = document.getElementById('logbook-analysis-loader');
    const logbookError = document.getElementById('logbook-analysis-error');
    const logbookForm = document.getElementById('logbook-entry-form');

    // === Dropdown toggles for narrative-info-dropdown ===
    document.querySelectorAll('.narrative-info-dropdown .dropdown-toggle').forEach(toggle => {
        toggle.addEventListener('click', () => {
            const content = toggle.nextElementSibling;
            if (content && content.classList.contains('dropdown-content')) {
                content.classList.toggle('hidden');
                toggle.classList.toggle('open');
            }
        });
    });

    // === Dynamic selects ("other..." functionality) ===
    const dynamicSelects = document.querySelectorAll('.dynamic-select');

    if (dynamicSelects.length > 0) {
        dynamicSelects.forEach(selectElement => {
            selectElement.addEventListener('change', function() {
                const otherInputId = this.dataset.otherInputId;
                const otherInputElement = document.getElementById(otherInputId);

                if (otherInputElement) {
                    if (this.value === 'other') {
                        otherInputElement.classList.remove('hidden');
                        otherInputElement.focus();
                        debugLog(`"Andet..." valgt for ${this.id}. Viser inputfelt: ${otherInputId}`);
                    } else {
                        otherInputElement.classList.add('hidden');
                        otherInputElement.value = '';
                        debugLog(`Anden option end "Andet..." valgt for ${this.id}. Skjuler inputfelt: ${otherInputId}`);
                    }
                } else {
                    console.error(`Could not find "other" input element with ID: ${otherInputId} for select: ${this.id}`);
                }
            });
        });
        debugLog("Dynamic select 'other...' functionality initialized.");
    } else {
        console.warn("No dynamic select elements found. 'Other...' functionality will not be available.");
    }

    // === Narrative relations dynamic input ===
    const narrativeAddRelationButton = document.getElementById('narrative-add-relation-button');
    let narrativeRelationCounter = 1;

    function createNarrativeRelationGroup() {
        narrativeRelationCounter++;
        const relationGroup = document.createElement('div');
        relationGroup.className = 'relation-group';

        const namePair = document.createElement('div');
        namePair.className = 'input-pair';
        const nameLabel = document.createElement('label');
        nameLabel.htmlFor = `narrative-relation-name-${narrativeRelationCounter}`;
        nameLabel.className = 'sr-only';
        nameLabel.textContent = 'Relations Navn';
        const nameInput = document.createElement('input');
        nameInput.type = 'text';
        nameInput.name = 'narrative_relation_name';
        nameInput.id = `narrative-relation-name-${narrativeRelationCounter}`;
        nameInput.placeholder = 'Navn (f.eks. Onkel Bo)';
        namePair.appendChild(nameLabel);
        namePair.appendChild(nameInput);

        const typePair = document.createElement('div');
        typePair.className = 'input-pair';
        const typeLabel = document.createElement('label');
        typeLabel.htmlFor = `narrative-relation-type-${narrativeRelationCounter}`;
        typeLabel.className = 'sr-only';
        typeLabel.textContent = 'Relationstype';
        const typeInput = document.createElement('input');
        typeInput.type = 'text';
        typeInput.name = 'narrative_relation_type';
        typeInput.id = `narrative-relation-type-${narrativeRelationCounter}`;
        typeInput.placeholder = 'Relation (f.eks. Nabo, Lærer)';
        typePair.appendChild(typeLabel);
        typePair.appendChild(typeInput);

        const removeButton = document.createElement('button');
        removeButton.type = 'button';
        removeButton.textContent = '-';
        removeButton.className = 'remove-button';
        removeButton.addEventListener('click', () => {
            relationGroup.remove();
        });

        relationGroup.appendChild(namePair);
        relationGroup.appendChild(typePair);
        relationGroup.appendChild(removeButton);

        return relationGroup;
    }

    if (narrativeAddRelationButton && narrativeRelationsContainer) {
        narrativeAddRelationButton.addEventListener('click', () => {
            const newGroup = createNarrativeRelationGroup();
            narrativeRelationsContainer.appendChild(newGroup);
            debugLog("New narrative relation group added.");
        });

        const initialNarrativeRelationRemoveButton = narrativeRelationsContainer.querySelector('.relation-group .initial-remove-button');
        if (initialNarrativeRelationRemoveButton) {
            initialNarrativeRelationRemoveButton.addEventListener('click', (e) => {
                const parentGroup = e.target.closest('.relation-group');
                if (parentGroup) {
                    parentGroup.querySelectorAll('input[type="text"]').forEach(input => input.value = '');
                    debugLog("Initial narrative relation group fields cleared.");
                }
            });
        }
        debugLog("Dynamic narrative relations functionality initialized.");
    } else {
        console.warn("Add narrative relation button or container not found. Dynamic relations will not work.");
    }

    // === Narrative main characters dynamic input ===
    const narrativeAddMainCharButton = document.getElementById('narrative-add-main-char-button');
    let narrativeMainCharCounter = 1;

    function createNarrativeMainCharacterGroup() {
        narrativeMainCharCounter++;
        const characterGroup = document.createElement('div');
        characterGroup.className = 'character-group';

        const descPair = document.createElement('div');
        descPair.className = 'input-pair';
        const descLabel = document.createElement('label');
        descLabel.htmlFor = `narrative-main-char-desc-${narrativeMainCharCounter}`;
        descLabel.className = 'sr-only';
        descLabel.textContent = 'Beskrivelse';
        const descInput = document.createElement('input');
        descInput.type = 'text';
        descInput.name = 'narrative_main_char_desc';
        descInput.id = `narrative-main-char-desc-${narrativeMainCharCounter}`;
        descInput.placeholder = 'Beskrivelse (f.eks. en finurlig robot)';
        descPair.appendChild(descLabel);
        descPair.appendChild(descInput);

        const namePair = document.createElement('div');
        namePair.className = 'input-pair';
        const nameLabel = document.createElement('label');
        nameLabel.htmlFor = `narrative-main-char-name-${narrativeMainCharCounter}`;
        nameLabel.className = 'sr-only';
        nameLabel.textContent = 'Navn';
        const nameInput = document.createElement('input');
        nameInput.type = 'text';
        nameInput.name = 'narrative_main_char_name';
        nameInput.id = `narrative-main-char-name-${narrativeMainCharCounter}`;
        nameInput.placeholder = 'Navn (valgfrit)';
        namePair.appendChild(nameLabel);
        namePair.appendChild(nameInput);

        const removeButton = document.createElement('button');
        removeButton.type = 'button';
        removeButton.textContent = '-';
        removeButton.className = 'remove-button';
        removeButton.addEventListener('click', () => {
            characterGroup.remove();
        });

        characterGroup.appendChild(descPair);
        characterGroup.appendChild(namePair);
        characterGroup.appendChild(removeButton);

        return characterGroup;
    }

    if (narrativeAddMainCharButton && narrativeMainCharactersContainer) {
        narrativeAddMainCharButton.addEventListener('click', () => {
            const newGroup = createNarrativeMainCharacterGroup();
            narrativeMainCharactersContainer.appendChild(newGroup);
            debugLog("New narrative main character group added.");
        });
    } else {
        console.warn("Add narrative main character button or container not found.");
    }

    // === Generic add buttons for places/plot ===
    const genericAddButtons = document.querySelectorAll('.generic-add-button');
    let genericInputCounter = {};

    if (genericAddButtons.length > 0) {
        genericAddButtons.forEach(button => {
            button.addEventListener('click', function() {
                const containerId = this.dataset.containerId;
                const inputName = this.dataset.inputName;
                const placeholder = this.dataset.inputPlaceholder;
                const idPrefix = this.dataset.inputIdPrefix;
                const container = document.getElementById(containerId);

                if (!container) {
                    console.error(`Generic add button: Container with ID '${containerId}' not found.`);
                    return;
                }

                if (genericInputCounter[idPrefix] === undefined) {
                    genericInputCounter[idPrefix] = 1;
                }
                genericInputCounter[idPrefix]++;

                const inputGroup = document.createElement('div');
                inputGroup.className = 'input-group';

                const label = document.createElement('label');
                label.htmlFor = `${idPrefix}-${genericInputCounter[idPrefix]}`;
                label.className = 'sr-only';
                label.textContent = placeholder;

                const newInput = document.createElement('input');
                newInput.type = 'text';
                newInput.name = inputName;
                newInput.id = `${idPrefix}-${genericInputCounter[idPrefix]}`;
                newInput.placeholder = placeholder;

                const removeButton = document.createElement('button');
                removeButton.type = 'button';
                removeButton.textContent = '-';
                removeButton.className = 'remove-button';
                removeButton.addEventListener('click', () => {
                    inputGroup.remove();
                });

                inputGroup.appendChild(label);
                inputGroup.appendChild(newInput);
                inputGroup.appendChild(removeButton);
                container.appendChild(inputGroup);
                debugLog(`Generic input added to ${containerId} with name ${inputName}`);
            });
        });
        debugLog("Generic add button functionality initialized.");
    } else {
        console.warn("No generic add buttons found.");
    }

    // === collectNarrativeData ===
    function collectNarrativeData() {
        const data = {};

        // 1. Centrale Narrative Input
        if (narrativeFocusInput) data.narrative_focus = narrativeFocusInput.value.trim();
        if (narrativeGoalInput) data.story_goal = narrativeGoalInput.value.trim();

        // 2. Information om Barnet
        if (narrativeChildNameInput) data.child_name = narrativeChildNameInput.value.trim();
        if (narrativeChildAgeInput) data.child_age = narrativeChildAgeInput.value.trim();

        // Barnets styrker (håndterer "Andet...")
        const strengths = [];
        if (narrativeChildStrengthsSelect) {
            const selectedValue = narrativeChildStrengthsSelect.value;
            if (selectedValue === 'other' && narrativeChildStrengthsOther?.value.trim()) {
                strengths.push(narrativeChildStrengthsOther.value.trim());
            } else if (selectedValue && selectedValue !== 'other') {
                strengths.push(selectedValue);
            }
        }
        data.child_strengths = strengths;

        // Barnets værdier (håndterer "Andet...")
        const values = [];
        if (narrativeChildValuesSelect) {
            const selectedValue = narrativeChildValuesSelect.value;
            if (selectedValue === 'other' && narrativeChildValuesOther?.value.trim()) {
                values.push(narrativeChildValuesOther.value.trim());
            } else if (selectedValue && selectedValue !== 'other') {
                values.push(selectedValue);
            }
        }
        data.child_values = values;

        if (narrativeChildMotivationInput) data.child_motivation = narrativeChildMotivationInput.value.trim();
        if (narrativeChildReactionTextarea) data.child_typical_reaction = narrativeChildReactionTextarea.value.trim();

        // 3. Problem-karakter (Brugerens eksternalisering)
        if (narrativeProblemIdentityNameInput) data.narrative_problem_identity_name = narrativeProblemIdentityNameInput.value.trim();
        if (narrativeProblemRoleFunctionInput) data.narrative_problem_role_function = narrativeProblemRoleFunctionInput.value.trim();
        if (narrativeProblemPurposeIntentionInput) data.narrative_problem_purpose_intention = narrativeProblemPurposeIntentionInput.value.trim();
        if (narrativeProblemBehaviorActionInput) data.narrative_problem_behavior_action = narrativeProblemBehaviorActionInput.value.trim();
        if (narrativeProblemInfluenceInput) data.narrative_problem_influence = narrativeProblemInfluenceInput.value.trim();

        // 4. Dynamiske lister (Relationer, Karakterer, Steder, Plot)
        // Vigtige Relationer
        data.important_relations = [];
        if (narrativeRelationsContainer) {
            narrativeRelationsContainer.querySelectorAll('.relation-group').forEach(group => {
                const nameInput = group.querySelector('input[name="narrative_relation_name"]');
                const typeInput = group.querySelector('input[name="narrative_relation_type"]');
                const name = nameInput ? nameInput.value.trim() : '';
                const type = typeInput ? typeInput.value.trim() : '';
                if (name || type) {
                    data.important_relations.push({ name: name, type: type });
                }
            });
        }

        // Hovedkarakterer
        data.main_characters = [];
        if (narrativeMainCharactersContainer) {
            narrativeMainCharactersContainer.querySelectorAll('.character-group').forEach(group => {
                const descInput = group.querySelector('input[name="narrative_main_char_desc"]');
                const nameInput = group.querySelector('input[name="narrative_main_char_name"]');
                const description = descInput ? descInput.value.trim() : '';
                const name = nameInput ? nameInput.value.trim() : '';
                if (description || name) {
                    data.main_characters.push({ description: description, name: name });
                }
            });
        }

        // Steder
        data.places = [];
        if (narrativePlacesContainer) {
            narrativePlacesContainer.querySelectorAll('.input-group input[name="narrative_place"]').forEach(input => {
                const value = input.value.trim();
                if (value) data.places.push(value);
            });
        }

        // Plot elementer
        data.plot_elements = [];
        if (narrativePlotContainer) {
            narrativePlotContainer.querySelectorAll('.input-group input[name="narrative_plot"]').forEach(input => {
                const value = input.value.trim();
                if (value) data.plot_elements.push(value);
            });
        }

        // 5. Generelle rammer
        if (narrativeNegativePromptInput) data.negative_prompt = narrativeNegativePromptInput.value.trim();
        if (narrativeLengthSelect) data.length = narrativeLengthSelect.value;
        if (narrativeMoodSelect) data.mood = narrativeMoodSelect.value;

        debugLog("Collected All Narrative Data:", data);
        return data;
    }

    // === populateNarrativeProfileSelector ===
    function populateNarrativeProfileSelector(profiles) {
        const selectorContainer = document.getElementById('narrative-profile-selector-container');
        const selector = document.getElementById('narrative-profile-select');
        if (!selector || !selectorContainer) return;

        selector.innerHTML = '<option value="">-- Vælg en gemt profil --</option>';
        if (profiles.length > 0) {
            profiles.forEach(profile => {
                const option = document.createElement('option');
                option.value = profile.id;
                option.textContent = profile.name;
                selector.appendChild(option);
            });
            selectorContainer.style.display = 'block';
        } else {
            selectorContainer.style.display = 'none';
        }
    }

    // === Narrative profile selector change handler ===
    const narrativeProfileSelector = document.getElementById('narrative-profile-select');
    if (narrativeProfileSelector) {
        narrativeProfileSelector.addEventListener('change', (event) => {
            const selectedProfileId = event.target.value;
            const selectedProfile = allProfilesData.find(p => p.id == selectedProfileId);

            const clearNarrativeForm = () => {
                document.getElementById('narrative-child-name-1').value = '';
                document.getElementById('narrative-child-age-1').value = '';

                const strengthsSelect = document.getElementById('narrative-child-strengths-select');
                strengthsSelect.value = '';
                const strengthsOther = document.getElementById('narrative-child-strengths-other');
                strengthsOther.value = '';
                strengthsOther.classList.add('hidden');

                const valuesSelect = document.getElementById('narrative-child-values-select');
                valuesSelect.value = '';
                const valuesOther = document.getElementById('narrative-child-values-other');
                valuesOther.value = '';
                valuesOther.classList.add('hidden');

                document.getElementById('narrative-child-motivation').value = '';
                document.getElementById('narrative-child-reaction').value = '';

                const relationsContainer = document.getElementById('narrative-relations-container');
                relationsContainer.innerHTML = `
                    <div class="relation-group">
                        <div class="input-pair">
                            <label for="narrative-relation-name-1" class="sr-only">Relations Navn</label>
                            <input type="text" name="narrative_relation_name" id="narrative-relation-name-1" placeholder="Navn (f.eks. Bedstemor Anna)">
                        </div>
                        <div class="input-pair">
                            <label for="narrative-relation-type-1" class="sr-only">Relationstype</label>
                            <input type="text" name="narrative_relation_type" id="narrative-relation-type-1" placeholder="Relation (f.eks. Bedste ven, Kæledyr)">
                        </div>
                        <button type="button" class="remove-button initial-remove-button" aria-hidden="true">-</button>
                    </div>`;
            };

            if (!selectedProfile) {
                clearNarrativeForm();
                return;
            }

            // Udfyld simple tekstfelter
            document.getElementById('narrative-child-name-1').value = selectedProfile.name || '';
            document.getElementById('narrative-child-age-1').value = selectedProfile.age || '';
            document.getElementById('narrative-child-motivation').value = (selectedProfile.motivations || []).join(', ');
            document.getElementById('narrative-child-reaction').value = (selectedProfile.reactions || []).join(', ');

            // Håndter dropdowns med "Andet..."-mulighed (Styrker og Værdier)
            const populateSelectWithOther = (selectId, otherId, values) => {
                const selectElement = document.getElementById(selectId);
                const otherElement = document.getElementById(otherId);
                const options = Array.from(selectElement.options).map(opt => opt.value);

                const valueToSet = values && values.length > 0 ? values[0] : '';

                if (valueToSet && options.includes(valueToSet)) {
                    selectElement.value = valueToSet;
                    otherElement.value = '';
                    otherElement.classList.add('hidden');
                } else if (valueToSet) {
                    selectElement.value = 'other';
                    otherElement.value = valueToSet;
                    otherElement.classList.remove('hidden');
                } else {
                    selectElement.value = '';
                    otherElement.value = '';
                    otherElement.classList.add('hidden');
                }
            };

            populateSelectWithOther('narrative-child-strengths-select', 'narrative-child-strengths-other', selectedProfile.strengths);
            populateSelectWithOther('narrative-child-values-select', 'narrative-child-values-other', selectedProfile.values);

            // Håndter den dynamiske liste af relationer
            const relationsContainer = document.getElementById('narrative-relations-container');
            relationsContainer.innerHTML = '';

            const relations = selectedProfile.relations && selectedProfile.relations.length > 0 ? selectedProfile.relations : [{ name: '', type: '' }];
            let relCounter = 0;
            relations.forEach(rel => {
                relCounter++;
                const newGroup = document.createElement('div');
                newGroup.className = 'relation-group';
                newGroup.innerHTML = `
                    <div class="input-pair">
                        <input type="text" name="narrative_relation_name" id="narrative-relation-name-${relCounter}" placeholder="Navn" value="${rel.name || ''}">
                    </div>
                    <div class="input-pair">
                        <input type="text" name="narrative_relation_type" id="narrative-relation-type-${relCounter}" placeholder="Relation" value="${rel.relation_type || ''}">
                    </div>
                    <button type="button" class="remove-button">-</button>`;

                newGroup.querySelector('.remove-button').addEventListener('click', () => newGroup.remove());
                relationsContainer.appendChild(newGroup);
            });
        });
    }

    // === Logbook documentation functions ===
    function resetLogbookSection() {
        if (logbookSection) logbookSection.classList.add('hidden');
        if (logbookLoader) logbookLoader.classList.add('hidden');
        if (logbookError) logbookError.classList.add('hidden');

        if (logbookForm) {
            logbookForm.classList.add('hidden');
            logbookForm.reset();

            logbookForm.querySelectorAll('.ai-suggested-input').forEach(el => {
                el.classList.remove('ai-suggested-input');
            });

            logbookForm.querySelectorAll('.progress-slider').forEach(sliderGroup => {
                const slider = sliderGroup.querySelector('input[type="range"]');
                const valueSpan = sliderGroup.querySelector('.range-value');
                if (slider && valueSpan) {
                    valueSpan.textContent = slider.value;
                }
            });

            const saveButton = document.getElementById('save-logbook-entry-button');
            if (saveButton) {
                saveButton.disabled = false;
                saveButton.classList.remove('disabled-button');
                saveButton.textContent = 'Gem Historien i Logbog';
                saveButton.style.backgroundColor = '';
            }
        }
    }

    function populateLogbookForm(storyId, data) {
        const storyIdField = document.getElementById('logbook-story-id');
        if (storyIdField) storyIdField.value = storyId;

        const fillField = (elementId, value) => {
            const element = document.getElementById(elementId);
            if (element && value) {
                element.value = Array.isArray(value) ? value.join(', ') : value;
                element.classList.add('ai-suggested-input');
                element.addEventListener('input', () => {
                    element.classList.remove('ai-suggested-input');
                }, { once: true });
            }
        };

        fillField('logbook-problem-name', data.problem_name);
        fillField('logbook-problem-category', data.problem_category);
        fillField('logbook-strength-type', data.strength_type);
        fillField('logbook-problem-influence', data.problem_influence);
        fillField('logbook-unique-outcome', data.unique_outcome);
        fillField('logbook-method-name', data.discovered_method_name);
        fillField('logbook-method-steps', data.discovered_method_steps);
        fillField('logbook-child-values', data.child_values);
        fillField('logbook-support-system', data.support_system);

        if (data.ai_summary) {
            fillField('logbook-ai-summary', data.ai_summary);
        }

        const originalStoryContainer = document.getElementById('logbook-original-story-container');
        const originalStoryTitleField = document.getElementById('logbook-original-story-title');

        if (originalStoryContainer && originalStoryTitleField && data.root_story_title) {
            originalStoryTitleField.value = data.root_story_title;
            originalStoryContainer.style.display = 'block';
        } else if (originalStoryContainer) {
            originalStoryContainer.style.display = 'none';
        }
    }

    // Progress slider event listeners
    document.querySelectorAll('.progress-slider input[type="range"]').forEach(slider => {
        const valueSpan = slider.nextElementSibling;
        if (valueSpan && valueSpan.classList.contains('range-value')) {
            valueSpan.textContent = slider.value;
            slider.addEventListener('input', () => {
                valueSpan.textContent = slider.value;
            });
        }
    });

    // Logbook form submit handler
    if (logbookForm) {
        logbookForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            const saveButton = document.getElementById('save-logbook-entry-button');
            const storyId = document.getElementById('logbook-story-id').value;

            if (!storyId) {
                alert("Fejl: Kunne ikke finde historiens ID. Kan ikke gemme.");
                return;
            }

            saveButton.disabled = true;
            saveButton.textContent = 'Gemmer...';

            const formData = new FormData(logbookForm);
            const dataToSave = Object.fromEntries(formData.entries());
            debugLog(`[DEBUG] Forsøger at gemme logbog for story_id: '${storyId}'. Fuld data:`, dataToSave);
            debugLog("Logbog: Sender data til server for at gemme:", dataToSave);

            try {
                const result = await saveLogbookEntryApi(storyId, dataToSave);
                debugLog("Server svar efter gem:", result);

                if (result.success) {
                    trackGAEvent('save_to_logbook', 'Narrativ Støtte', `Story ID: ${storyId}`, null);
                }

                saveButton.textContent = 'Gemt i Logbog!';
                saveButton.style.backgroundColor = '#28a745';
                saveButton.disabled = true;
                saveButton.classList.add('disabled-button');

            } catch (error) {
                console.error("Fejl ved gemning af logbogs-historie:", error);
                alert(`Der opstod en fejl: ${error.message}`);
                saveButton.disabled = false;
                saveButton.textContent = 'Gem Historie i Logbogen';
            }
        });
    }

    async function triggerLogbookAnalysis(storyId, storyContent, rootStoryTitle) {
        debugLog("Logbog: Starter analyse for story ID:", storyId);
        resetLogbookSection();

        if (!logbookSection || !logbookLoader || !logbookError || !logbookForm) {
            console.error("Logbog: Kritiske HTML-elementer til dokumentation mangler.");
            return;
        }

        logbookSection.classList.remove('hidden');
        logbookLoader.classList.remove('hidden');

        try {
            const analysisData = await analyzeStoryForLogbookApi(storyContent);
            debugLog("Logbog: Analyse modtaget fra API:", analysisData);

            if (analysisData.error) {
                throw new Error(analysisData.error);
            }

            if (rootStoryTitle) {
                analysisData.root_story_title = rootStoryTitle;
            }

            populateLogbookForm(storyId, analysisData);
            logbookLoader.classList.add('hidden');
            logbookForm.classList.remove('hidden');

        } catch (error) {
            console.error("Logbog: Fejl under analyse-workflow:", error);
            logbookLoader.classList.add('hidden');
            logbookError.textContent = `Fejl under analyse: ${error.message}`;
            logbookError.classList.remove('hidden');
        }
    }

    // === Reflection questions ===
    async function triggerAndDisplayReflectionQuestions(storyTitle, storyContent, narrativeBrief, originalInputs) {
        const reflectionSection = document.getElementById('narrative-reflection-section');
        const questionList = document.getElementById('narrative-reflection-questions-list');

        if (!reflectionSection || !questionList) {
            console.error("Elementer til refleksionsspørgsmål ikke fundet.");
            return;
        }

        questionList.innerHTML = '<li>Genererer spørgsmål...</li>';
        reflectionSection.classList.remove('hidden');

        try {
            const contextData = {
                final_story_title: storyTitle,
                final_story_content: storyContent,
                narrative_brief: narrativeBrief,
                original_user_inputs: originalInputs
            };

            const result = await getGuidingQuestionsApi(contextData);

            if (result.reflection_questions && result.reflection_questions.length > 0) {
                questionList.innerHTML = result.reflection_questions.map(q => `<li>${q}</li>`).join('');
            } else {
                questionList.innerHTML = '<li>Kunne ikke generere specifikke spørgsmål til denne historie.</li>';
            }

        } catch (error) {
            console.error("Fejl under hentning af refleksionsspørgsmål:", error);
            questionList.innerHTML = `<li>Fejl: Kunne ikke hente spørgsmål.</li>`;
        }
    }

    // === populateCharacterTraitFields ===
    function populateCharacterTraitFields(suggestions) {
        debugLog("populateCharacterTraitFields kaldt med forslag:", suggestions);
        const aiSuggestionClass = 'ai-suggested-input';
        let attemptedToFillProblemCharacter = false;

        function setSimpleInput(element, value) {
            if (element && value && element.value.trim() === '') {
                element.value = value;
                element.classList.add(aiSuggestionClass);
                element.addEventListener('input', () => element.classList.remove(aiSuggestionClass), { once: true });
                return true;
            } else if (element && value && element.value.trim() !== '') {
                debugLog(`Skipped pre-filling ${element.id || 'element'} because it already has user input: "${element.value.trim()}"`);
            }
            return false;
        }

        if (suggestions && suggestions.problem_character_suggestions) {
            const ps = suggestions.problem_character_suggestions;
            debugLog("Forsøger at anvende forslag til Problem-Karakter:", ps);
            if (Object.keys(ps).length > 0) {
                attemptedToFillProblemCharacter = true;
                setSimpleInput(narrativeProblemIdentityNameInput, ps.identity_name ? ps.identity_name[0] : null);
                setSimpleInput(narrativeProblemRoleFunctionInput, ps.role_function ? ps.role_function[0] : null);
                setSimpleInput(narrativeProblemPurposeIntentionInput, ps.purpose_intention ? ps.purpose_intention[0] : null);
                setSimpleInput(narrativeProblemBehaviorActionInput, ps.behavior_action ? ps.behavior_action[0] : null);
                setSimpleInput(narrativeProblemInfluenceInput, ps.influence_on_protagonist ? ps.influence_on_protagonist[0] : null);
            }
        } else {
            debugLog("Ingen forslag til Problem-Karakter modtaget i suggestions objektet.");
        }

        if (suggestions && suggestions.protagonist_character_suggestions) {
            debugLog("Forslag til Protagonist-Karakter modtaget, men vil IKKE blive anvendt.");
        }

        debugLog("populateCharacterTraitFields udført. Forsøgte at udfylde problem-karakter:", attemptedToFillProblemCharacter);
        return attemptedToFillProblemCharacter;
    }

    // === Narrative suggest traits button ===
    if (narrativeSuggestTraitsButton) {
        narrativeSuggestTraitsButton.addEventListener('click', async () => {
            debugLog("Narrative 'Suggest Traits' button clicked.");
            const focusText = narrativeFocusInput ? narrativeFocusInput.value.trim() : "";

            if (!focusText) {
                alert("Udfyld venligst 'Tema, Udfordring eller Fokus for Historien' først.");
                if (narrativeFocusInput) narrativeFocusInput.focus();
                return;
            }

            const originalButtonText = narrativeSuggestTraitsButton.textContent;
            narrativeSuggestTraitsButton.disabled = true;
            narrativeSuggestTraitsButton.textContent = "Foreslår træk...";

            try {
                const suggestions = await suggestCharacterTraitsApi(focusText);
                debugLog("Forslag til karaktertræk modtaget fra API:", suggestions);

                if (suggestions && !suggestions.error) {
                    const attemptedProblemFill = populateCharacterTraitFields(suggestions);

                    if (attemptedProblemFill) {
                        let actuallyFilledSomething = false;
                        if (suggestions.problem_character_suggestions) {
                            const ps = suggestions.problem_character_suggestions;
                            if ((ps.identity_name && ps.identity_name[0] && narrativeProblemIdentityNameInput.value === ps.identity_name[0]) ||
                                (ps.role_function && ps.role_function[0] && narrativeProblemRoleFunctionInput.value === ps.role_function[0]) ||
                                (ps.purpose_intention && ps.purpose_intention[0] && narrativeProblemPurposeIntentionInput.value === ps.purpose_intention[0]) ||
                                (ps.behavior_action && ps.behavior_action[0] && narrativeProblemBehaviorActionInput.value === ps.behavior_action[0]) ||
                                (ps.influence_on_protagonist && ps.influence_on_protagonist[0] && narrativeProblemInfluenceInput.value === ps.influence_on_protagonist[0])
                            ) {
                                actuallyFilledSomething = true;
                            }
                        }

                        if (actuallyFilledSomething) {
                            debugLog("AI har foreslået karaktertræk for Problem-Karakteren, og felter er opdateret.");
                        } else if (attemptedProblemFill && !actuallyFilledSomething) {
                            debugLog("AI havde forslag til Problem-Karakteren, men alle relevante felter var allerede udfyldt eller matchede forslaget.");
                        } else {
                            debugLog("Ingen forslag til Problem-Karakteren blev anvendt (muligvis ingen forslag fra AI).");
                        }
                    } else {
                        debugLog("AI returnerede ingen forslag til Problem-Karakteren (attemptedProblemFill var false).");
                    }

                } else if (suggestions && suggestions.error) {
                    alert(`Fejl under forslag til karaktertræk: ${suggestions.error}`);
                    console.error("Fejl fra suggestCharacterTraitsApi:", suggestions.error);
                } else {
                    alert("AI kunne ikke generere forslag (uventet svar fra server). Tjek konsollen.");
                    console.warn("Uventet eller tomt svar (uden fejl) fra suggestCharacterTraitsApi:", suggestions);
                }

            } catch (error) {
                console.error("Fejl ved API kald til suggestCharacterTraitsApi:", error);
                alert(`Der opstod en fejl under hentning af karaktertræk-forslag: ${error.message}`);
            } finally {
                narrativeSuggestTraitsButton.disabled = false;
                narrativeSuggestTraitsButton.textContent = originalButtonText;
            }
        });
    } else {
        console.warn("Knappen '#narrative-suggest-traits-button' blev ikke fundet.");
    }

    // === Narrative image generation ===
    async function handleGenerateNarrativeImagesClick() {
        if (!currentNarrativeData || !currentNarrativeData.storyContent) {
            alert("Fejl: Der er ingen genereret narrativ historie at skabe billeder fra.");
            return;
        }

        narrativeGenerateImagesButton.disabled = true;
        narrativeGenerateImagesButton.textContent = "Genererer billeder...";

        imageSection.classList.remove('hidden');
        storyImageContainer.classList.remove('hidden');
        problemImageContainer.classList.remove('hidden');
        storyImageLoader.classList.remove('hidden');
        problemImageLoader.classList.remove('hidden');
        [storyImageDisplay, problemImageDisplay, storyImageError, problemImageError].forEach(el => el.classList.add('hidden'));
        storyImageError.textContent = '';
        problemImageError.textContent = '';

        const storyImagePromise = generateNarrativeStoryImageApi(currentNarrativeData);
        const problemImagePromise = generateProblemImageApi(currentNarrativeData);

        storyImagePromise
            .then(result => {
                if (result.image_url) {
                    storyImageDisplay.src = result.image_url;
                    storyImageDisplay.classList.remove('hidden');
                } else {
                    throw new Error(result.error || "Ukendt fejl fra serveren.");
                }
            })
            .catch(error => {
                storyImageError.textContent = `Fejl (Historie): ${error.message}`;
                storyImageError.classList.remove('hidden');
            })
            .finally(() => {
                storyImageLoader.classList.add('hidden');
            });

        problemImagePromise
            .then(result => {
                if (result.image_url) {
                    problemImageDisplay.src = result.image_url;
                    problemImageDisplay.classList.remove('hidden');
                } else {
                    throw new Error(result.error || "Ukendt fejl fra serveren.");
                }
            })
            .catch(error => {
                problemImageError.textContent = `Fejl (Problem): ${error.message}`;
                problemImageError.classList.remove('hidden');
            })
            .finally(() => {
                problemImageLoader.classList.add('hidden');
            });

        await Promise.allSettled([storyImagePromise, problemImagePromise]);

        narrativeGenerateImagesButton.disabled = false;
        narrativeGenerateImagesButton.textContent = "Skab Billeder til Fortællingen";
    }

    // === Continuation story flow ===
    const strategyButtons = document.querySelectorAll('[name="continuation_strategy"]');

    if (continueStorySwitch) {
        continueStorySwitch.addEventListener('change', async () => {
            if (continueStorySwitch.checked) {
                continuationOptions.classList.remove('hidden');
                parentStorySelect.innerHTML = '<option value="">Henter historier...</option>';
                parentStorySelect.disabled = true;
                strategySelection.classList.add('hidden');

                try {
                    const stories = await listContinuableStoriesApi();
                    parentStorySelect.innerHTML = '<option value="">-- Vælg historie at bygge videre på --</option>';

                    if (stories.length > 0) {
                        stories.forEach(story => {
                            const option = document.createElement('option');
                            option.value = story.id;
                            option.textContent = story.title;
                            parentStorySelect.appendChild(option);
                        });
                        parentStorySelect.disabled = false;
                    } else {
                        parentStorySelect.innerHTML = '<option value="">Ingen historier fundet i logbogen</option>';
                    }
                } catch (error) {
                    console.error("Fejl ved hentning af historieliste:", error);
                    parentStorySelect.innerHTML = `<option value="">Fejl: ${error.message}</option>`;
                }
            } else {
                continuationOptions.classList.add('hidden');
                strategySelection.classList.add('hidden');
                parentStorySelect.innerHTML = '<option value="">-- Henter Historier... --</option>';
            }
        });
    }

    if (parentStorySelect) {
        parentStorySelect.addEventListener('change', () => {
            if (parentStorySelect.value) {
                strategySelection.classList.remove('hidden');
            } else {
                strategySelection.classList.add('hidden');
            }
        });
    }

    const handleStrategyClick = (event) => {
        const strategy = event.target.value;
        const parentStoryId = parentStorySelect.value;

        if (!parentStoryId) {
            alert("Vælg venligst en historie fra listen først.");
            return;
        }

        debugLog(`Strategi valgt: ${strategy}, Forælder ID: ${parentStoryId}`);

        if (narrativeGenerateStoryButton) narrativeGenerateStoryButton.disabled = true;
        strategyButtons.forEach(btn => btn.disabled = true);

        const narrativeData = collectNarrativeData();

        narrativeData.parent_story_id = parentStoryId;
        narrativeData.continuation_strategy = strategy;

        executeNarrativeGeneration(narrativeData);
    };

    strategyButtons.forEach(button => {
        button.addEventListener('click', handleStrategyClick);
    });

    // === executeNarrativeGeneration ===
    async function executeNarrativeGeneration(dataToSend) {
        debugLog("executeNarrativeGeneration: Starter med data:", dataToSend);
        resetLogbookSection();

        const originalButtonText = narrativeGenerateStoryButton.textContent;
        narrativeGenerateStoryButton.disabled = true;
        strategyButtons.forEach(btn => btn.disabled = true);
        narrativeGenerateStoryButton.textContent = "Genererer...";

        narrativeErrorDisplay.classList.add('hidden');
        narrativeGeneratedStorySection.classList.add('hidden');
        narrativeLoadingIndicator.classList.remove('hidden');

        try {
            const result = await generateNarrativeStoryApi(dataToSend);
            debugLog("Svar modtaget fra server:", result);
            if (result.error) throw new Error(result.error);

            const eventLabel = dataToSend.continuation_strategy ? `Continuation: ${dataToSend.continuation_strategy}` : 'New Story';
            trackGAEvent('generate_narrative_story', 'Narrativ Støtte', eventLabel, null);

            if (narrativeGeneratedTitle) narrativeGeneratedTitle.textContent = result.title;
            if (narrativeGeneratedStory) narrativeGeneratedStory.innerHTML = result.story.replace(/\n/g, '<br>');
            if (narrativeGeneratedStorySection) narrativeGeneratedStorySection.classList.remove('hidden');

            currentNarrativeData = dataToSend;
            currentNarrativeData.storyContent = result.story;
            if (narrativeGenerateImagesButton) {
                narrativeGenerateImagesButton.disabled = false;
                narrativeGenerateImagesButton.removeAttribute('title');
            }

            if (result.story_id && result.story) {
                triggerLogbookAnalysis(result.story_id, result.story, result.root_story_title);
                triggerAndDisplayReflectionQuestions(result.title, result.story, dataToSend, dataToSend);
            } else {
                throw new Error("Modtog ikke et validt story_id fra backend.");
            }
        } catch (error) {
            console.error('Fejl under historiegenerering:', error);
            if (narrativeErrorDisplay) narrativeErrorDisplay.textContent = `Ups! Noget gik galt: ${error.message}`;
            narrativeErrorDisplay.classList.remove('hidden');
        } finally {
            if (narrativeLoadingIndicator) narrativeLoadingIndicator.classList.add('hidden');
            narrativeGenerateStoryButton.disabled = false;
            strategyButtons.forEach(btn => btn.disabled = false);
            narrativeGenerateStoryButton.textContent = originalButtonText;
        }
    }

    // === startNarrativeGeneration ===
    function startNarrativeGeneration(strategy = null) {
        const narrativeData = collectNarrativeData();

        if (strategy) {
            const parentStoryId = parentStorySelect.value;
            if (!parentStoryId) {
                alert("Vælg venligst en historie fra listen først.");
                return;
            }
            narrativeData.parent_story_id = parentStoryId;
            narrativeData.continuation_strategy = strategy;
        }

        executeNarrativeGeneration(narrativeData);
    }

    // === Wire up narrative generate button ===
    if (narrativeGenerateStoryButton) {
        narrativeGenerateStoryButton.addEventListener('click', () => startNarrativeGeneration(null));
    }

    // === Wire up narrative image button ===
    if (narrativeGenerateImagesButton) {
        narrativeGenerateImagesButton.addEventListener('click', handleGenerateNarrativeImagesClick);
    }

    // === Font size buttons for narrative ===
    if (narrativeDecreaseFontButton && narrativeStoryEl) {
        narrativeDecreaseFontButton.addEventListener('click', () => updateFontSize(narrativeStoryEl, -1, false, 'narrativeStory'));
    }
    if (narrativeIncreaseFontButton && narrativeStoryEl) {
        narrativeIncreaseFontButton.addEventListener('click', () => updateFontSize(narrativeStoryEl, 1, false, 'narrativeStory'));
    }
    if (narrativeResetFontButton && narrativeStoryEl) {
        narrativeResetFontButton.addEventListener('click', () => updateFontSize(narrativeStoryEl, 0, true, 'narrativeStory'));
    }

    // === Style guidance dropdowns ===
    document.querySelectorAll('.dropdown-toggle').forEach(button => {
        if (['Vejledning', 'Hvad er'].some(kw => button.textContent.includes(kw))) {
            button.style.color = '#bbbe70';
        }
    });

    // === Profile feature: load profiles on page load ===
    listChildProfilesApi().then(profiles => {
        allProfilesData = profiles;
        populateNarrativeProfileSelector(profiles);
    }).catch(err => console.warn('Kunne ikke hente profiler:', err));

    // === Initialize ===
    initializeInfoIcons();

    // Load saved font size from localStorage
    const savedNarrSize = localStorage.getItem('narrativeStoryFontSize');
    if (savedNarrSize && narrativeStoryEl) {
        const sz = parseInt(savedNarrSize, 10);
        if (!isNaN(sz)) narrativeStoryEl.style.fontSize = sz + 'px';
    }

    debugLog("stoette.js: DOMContentLoaded initialization complete.");
});
