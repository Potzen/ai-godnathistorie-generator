// Fil: static/script.js
import { initializeLogbook } from './logbook.js';
import { saveHojtlasningStoryApi, generateStoryApi, generateImageApi, suggestCharacterTraitsApi, generateNarrativeStoryApi, getGuidingQuestionsApi, generateAudioApi, generateLixStoryApi, analyzeStoryForLogbookApi, saveLogbookEntryApi, listContinuableStoriesApi, generateProblemImageApi, saveChildProfileApi, listChildProfilesApi, deleteChildProfileApi, generateNarrativeStoryImageApi, generateQuizApi } from './modules/api_client.js';

// Kør først koden, når hele HTML dokumentet er færdigindlæst og klar
document.addEventListener('DOMContentLoaded', () => {

const quizSektion = document.getElementById('quiz-sektion');
const quizContainer = document.getElementById('quiz-container');
const quizFeedback = document.getElementById('quiz-feedback');
let currentQuizData = [];
let correctAnswersCount = 0;
console.log("DOMContentLoaded event fired. Initializing Read Me A Story script.");
const imageSection = document.getElementById('billede-til-historien-sektion');
const storyImageContainer = document.getElementById('story-image-container');
const storyImageLoader = document.getElementById('story-image-loader');
const storyImageDisplay = document.getElementById('story-image-display');
const storyImageError = document.getElementById('story-image-error');
const problemImageContainer = document.getElementById('problem-image-container');
const problemImageLoader = document.getElementById('problem-image-loader');
const problemImageDisplay = document.getElementById('problem-image-display');
const problemImageError = document.getElementById('problem-image-error');
const narrativeGenerateImagesButton = document.getElementById('narrative-generate-images-button');
let currentNarrativeData = null; // Global variabel


// === START: Tekster og Logik for Informationsikoner (Tooltips) ===
const tooltipElement = document.getElementById('info-tooltip');
const tooltipTextElement = document.getElementById('info-tooltip-text');
const tooltipCloseButton = document.getElementById('info-tooltip-close');
let currentVisibleTooltipIcon = null;
let clickOpensTooltip = false; // Nyt flag for at håndtere den første klik-interaktion
const storyTextContent = document.getElementById('story-text-content');

const tooltipTexts = {
    'tooltip-narrative-focus': "Tip: Angiv her den centrale begivenhed, udfordring eller det fokus, historien skal omhandle. Det kan være en følelse (f.eks. generthed), en konkret situation (f.eks. 'svært ved at dele') eller en kommende begivenhed (f.eks. 'skolestart', 'en flytning'). En præcis beskrivelse hjælper AI'en med at skabe en målrettet historie.",
    'tooltip-narrative-goal': "Tip: Formulér her det ønskede mål med historien. Sigtepunktet kan være en positiv forandring, en ny forståelse eller en specifik indsigt, som historien skal understøtte hos barnet i relation til den centrale begivenhed/udfordring. Dette hjælper AI'en med at skabe et meningsfuldt og styrkende budskab i fortællingen.",
    'tooltip-child-strengths': "Tip: Beskriv dit barns positive egenskaber, eller hvad barnet holder af at gøre. Disse styrker kan flettes ind i historien som 'superkræfter', der hjælper hovedpersonen med at overvinde udfordringer. Dette kan bidrage til at styrke barnets selvværd og oplevelse af handlekraft.", // <-- KOMMA TILFØJET HER
    'pro-model-info': "'Standard'-modellen er hurtig. 'Pro'-modellen er giver højere kvalitet, mere kreativitet og bedre sammenhæng i historierne. Den er dog langsommere.",
    'interactive-info': "Når denne er slået til, vil AI'en forsøge at skrive historien med 1-2 indbyggede valgmuligheder for at engagere barnet. Funktionen virker bedst, når 'Lang' historielængde er valgt.",
    'bedtime-info': "Når denne er slået til, får AI'en en specifik instruktion om at gøre historien ekstra rolig, tryg og afdæmpet. Dette overtrumfer det generelle 'Stemning'-valg og er ideelt til at hjælpe et barn med at falde til ro ved sengetid."
};


function showTooltip(iconElement, text) {
    if (!tooltipElement || !tooltipTextElement) {
        console.error("FEJL: Tooltip HTML elementerne blev ikke fundet!");
        return;
    }
    console.log("showTooltip FORSØGER for:", iconElement.dataset.tooltipId);

    tooltipTextElement.textContent = text;

    // Forcer synlighed for måling (men hold den usynlig for brugeren og ude af flow)
    tooltipElement.classList.remove('hidden'); // Fjern .hidden hvis den styrer display:none
    tooltipElement.style.display = 'block';    // Sæt display: block direkte
    tooltipElement.style.visibility = 'hidden';// Gør den usynlig, men dimensionerbar
    tooltipElement.style.position = 'absolute';// Sørg for den er ude af normalt flow
    tooltipElement.style.left = '-9999px';     // Flyt langt væk
    tooltipElement.style.top = '-9999px';

    // Mål dimensioner
    const tooltipWidth = tooltipElement.offsetWidth;
    const tooltipHeight = tooltipElement.offsetHeight;
    console.log("Tooltip dimensioner målt: Bredde =", tooltipWidth, "Højde =", tooltipHeight);

    if (tooltipWidth === 0 && tooltipHeight === 0 && text.length > 0) {
        console.warn("ADVARSEL: Tooltip har stadig 0x0 dimensioner, selvom display='block' og visibility='hidden' blev sat. Tjek CSS for #info-tooltip for konflikter (f.eks. !important). Tekstlængde:", text.length);
        // Vi fortsætter med positionering, men den vil være forkert hvis dimensionerne er 0.
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
    tooltipElement.style.visibility = 'visible'; // Gør den synlig på den korrekte position
    tooltipElement.classList.add('visible');     // Sørg for .visible klassen er der for CSS styling

    console.log("Tooltip SKULLE NU VÆRE SYNLIG OG POSITIONERET ved: top=", Math.round(top), "left=", Math.round(left));
    currentVisibleTooltipIcon = iconElement;
}

function hideTooltip() {
    if (tooltipElement) {
        tooltipElement.classList.remove('visible');
        tooltipElement.classList.add('hidden');
        // Nulstil inline styles der blev brugt til måling/visning
        tooltipElement.style.visibility = '';
        tooltipElement.style.display = ''; // Lader CSS klasserne styre display
        tooltipElement.style.left = '';
        tooltipElement.style.top = '';
        currentVisibleTooltipIcon = null;
        console.log("Tooltip skjult.");
    }
}

function initializeInfoIcons() {
    const infoIcons = document.querySelectorAll('.info-icon');
    console.log(`Fandt ${infoIcons.length} .info-icon elementer.`);

    if (!tooltipElement) {
        console.error("FEJL: Det primære tooltip-element (#info-tooltip) blev ikke fundet.");
        return;
    }

    infoIcons.forEach(icon => {
        icon.addEventListener('click', (event) => {
            event.stopPropagation(); // Meget vigtig!

            const tooltipId = icon.dataset.tooltipId;
            const textToShow = tooltipTexts[tooltipId];
            console.log("Info-ikon klikket. ID:", tooltipId);

            if (currentVisibleTooltipIcon === icon) {
                console.log("Samme ikon klikket, skjuler aktiv tooltip.");
                hideTooltip();
            } else if (textToShow) {
                console.log("Viser ny tooltip for:", tooltipId);
                showTooltip(icon, textToShow);
                clickOpensTooltip = true; // Sæt flag NÅR vi aktivt viser en ny tooltip
            } else {
                console.warn(`Ingen hjælpetekst fundet for ID: ${tooltipId}`);
                hideTooltip();
            }
        });
    });

    if (tooltipCloseButton) {
        tooltipCloseButton.addEventListener('click', (event) => {
            event.stopPropagation();
            console.log("Tooltip luk-knap klikket.");
            hideTooltip();
        });
    }

    document.addEventListener('click', (event) => {
        // Hvis et klik lige har åbnet tooltip'en, ignorer dette document click event
        if (clickOpensTooltip) {
            clickOpensTooltip = false; // Nulstil flaget for næste klik
            return;
        }

        if (tooltipElement && tooltipElement.classList.contains('visible')) {
            // Tjek om klikket var på selve tooltip-boksen eller et info-ikon
            // (klik på info-ikon håndteres allerede af dens egen listener pga. stopPropagation ovenfor)
            if (!tooltipElement.contains(event.target)) {
                console.log("Klik udenfor aktiv tooltip. Skjuler tooltip.");
                hideTooltip();
            }
        }
    });

    if (infoIcons.length > 0) {
        console.log("Info ikon event listeners initialiseret (version 3).");
    }
}
// === SLUT: Tekster og Logik for Informationsikoner (Tooltips) ===

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
    const generateButton = document.getElementById('generate-button');
    const resetButton = document.getElementById('reset-button'); // Bemærk: Denne er nu inde i story-share-buttons

    const generateImageButtons = document.querySelectorAll('.js-generate-image');
    const imageLoadingIndicator = document.getElementById('image-loading-indicator');
    const imageGenerationError = document.getElementById('image-generation-error');
    const storyDisplay = document.getElementById('story-display');
    const storySectionHeading = document.getElementById('story-section-heading'); // Til opdatering af historietitel
    const storyLoadingIndicator = document.getElementById('story-loading-indicator');
    const generatorSection = document.getElementById('generator');
    const laengdeSelect = document.getElementById('laengde-select');
    const moodSelect = document.getElementById('mood-select');
    const aiModelSwitch = document.getElementById('ai-model-switch'); // Reference til den nye switch
    const interactiveStorySwitch = document.getElementById('interactive-story-switch');
    const bedtimeStorySwitch = document.getElementById('bedtime-story-switch');

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
    const ttsVoiceSelect = document.getElementById('tts-voice-select'); // Reference til stemmevalgsdropdown
    const ttsVoiceSelectionDiv = document.getElementById('tts-voice-selection'); // Reference til containeren for stemmevalg

    // Billed-elementer (hvis de bruges - pt. ikke aktivt)

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

    // === Referencer for Narrativ Støtte Modul ===
    const narrativeGenerateStoryButton = document.getElementById('narrative-generate-story-button');
    const narrativeSuggestTraitsButton = document.getElementById('narrative-suggest-traits-button');
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
    const narrativeReflectionSection = document.getElementById('narrative-reflection-section');
    const narrativeReflectionQuestionsList = document.getElementById('narrative-reflection-questions-list');
    const narrativeDebugSection = document.getElementById('narrative-debug-section');
    const narrativeDebugStatus = document.getElementById('narrative-debug-status');
    const narrativeDebugBrief = document.getElementById('narrative-debug-brief');
    const narrativeDebugDraftTitle = document.getElementById('narrative-debug-draft-title');
    const narrativeDebugDraftContent = document.getElementById('narrative-debug-draft-content');


    // --- NYT: Sangtekst Sektion Elementer ---
    const sangDropdown = document.getElementById('sang-dropdown');
    const sangtekstTitel = document.getElementById('sangtekst-titel'); // Overskriften for sangteksten
    const sangtekstVisning = document.getElementById('sangtekst-visning'); // Hvor selve teksten vises
    let allSongsData = []; // Global variabel til at gemme sangdata


    // === Referencer for Skriftstørrelseskontrol (Standard Historier) ===
    const decreaseFontButton = document.getElementById('decrease-font-button');
    const increaseFontButton = document.getElementById('increase-font-button');
    const resetFontButton = document.getElementById('reset-font-button');
    // storyDisplay er allerede defineret tidligere i dit script for standardhistorier

    // === Referencer for Skriftstørrelseskontrol (Narrative Historier) ===
    const narrativeDecreaseFontButton = document.getElementById('narrative-decrease-font-button');
    const narrativeIncreaseFontButton = document.getElementById('narrative-increase-font-button');
    const narrativeResetFontButton = document.getElementById('narrative-reset-font-button');
    // narrativeGeneratedStory er allerede defineret tidligere i dit script for narrative historier
    // (Den hedder 'narrativeGeneratedStory' i din nuværende JS, svarer til #narrative-generated-story i HTML)

    // === Variabler for Skriftstørrelseskontrol ===
    const DEFAULT_FONT_SIZE_PX = 16; // Standard skriftstørrelse i pixels
    const FONT_SIZE_STEP_PX = 1;   // Hvor meget skriftstørrelsen ændres pr. klik
    const MIN_FONT_SIZE_PX = 10;   // Minimum tilladt skriftstørrelse
    const MAX_FONT_SIZE_PX = 30;   // Maksimum tilladt skriftstørrelse

    let currentStoryDisplayFontSize = DEFAULT_FONT_SIZE_PX;
    let currentNarrativeStoryFontSize = DEFAULT_FONT_SIZE_PX;
    const STORY_DISPLAY_FONT_KEY = 'storyDisplayFontSize';
    const NARRATIVE_STORY_FONT_KEY = 'narrativeStoryFontSize';
    const failureInfoDropdownToggle = document.getElementById('failure-info-dropdown-toggle');
    const failureInfoDropdownContent = document.getElementById('failure-info-dropdown-content');
    console.log("DOM references obtained for all sections.");

    // --- START: Logik for Interaktiv Historie Switch afhængighed af Pro AI-Model Switch ---
    function updateInteractiveStorySwitchAvailability() {
        console.log("--- updateInteractiveStorySwitchAvailability KØRER ---"); // DEBUG
        if (aiModelSwitch && interactiveStorySwitch) {
            console.log(`aiModelSwitch.disabled: ${aiModelSwitch.disabled}, aiModelSwitch.checked: ${aiModelSwitch.checked}`); // DEBUG

            if (aiModelSwitch.disabled) {
                console.log("aiModelSwitch er disabled. Sætter interaktiv til disabled og unchecked."); // DEBUG
                interactiveStorySwitch.checked = false;
                interactiveStorySwitch.disabled = true;
                return;
            }

            if (aiModelSwitch.checked) { // Pro AI-Model er TIL
                console.log("aiModelSwitch er TIL. Aktiverer interaktiv switch."); // DEBUG
                interactiveStorySwitch.disabled = false;
                interactiveStorySwitch.title = "Slå til for at få interaktive valg i historien.";
            } else { // Pro AI-Model er FRA
                console.log("aiModelSwitch er FRA. Deaktiverer interaktiv switch."); // DEBUG
                interactiveStorySwitch.disabled = true;
                interactiveStorySwitch.checked = false; // Slå den interaktive fra
                interactiveStorySwitch.title = "Vælg 'Pro' under 'Pro AI-Model' for at aktivere interaktiv funktion.";
            }
            console.log(`EFTER opdatering: interactiveStorySwitch.disabled: ${interactiveStorySwitch.disabled}, interactiveStorySwitch.checked: ${interactiveStorySwitch.checked}`); // DEBUG
        } else {
            if (!aiModelSwitch) console.warn("aiModelSwitch (Pro AI) blev ikke fundet. Interaktiv switch kan ikke styres korrekt.");
            if (!interactiveStorySwitch) console.warn("interactiveStorySwitch (Interaktiv Historie) blev ikke fundet.");
        }
        console.log("--- updateInteractiveStorySwitchAvailability FÆRDIG ---"); // DEBUG
    }

    // Tilføj event listener til Pro AI-Model switchen
if (aiModelSwitch) {
        aiModelSwitch.addEventListener('change', function() { // Gør det til en anonym funktion for at logge først
            console.log("Pro AI-Model (aiModelSwitch) 'change' event registreret."); // DEBUG
            updateInteractiveStorySwitchAvailability();
        });
    }

    // Kald funktionen én gang ved sideindlæsning for at sætte den korrekte initiale tilstand
    // for interactiveStorySwitch baseret på aiModelSwitch's starttilstand.
    updateInteractiveStorySwitchAvailability();
    // --- SLUT: Logik for Interaktiv Historie Switch ---

    // === Funktioner for Skriftstørrelseskontrol ===

    /**
     * Anvender en given skriftstørrelse på et HTML-element.
     * @param {HTMLElement} element - HTML-elementet, hvis skriftstørrelse skal ændres.
     * @param {number} sizeInPx - Den ønskede skriftstørrelse i pixels.
     */
    function applyFontSize(element, sizeInPx) {
        if (element) {
            element.style.fontSize = `${sizeInPx}px`;
            // console.log(`Applied font size ${sizeInPx}px to element:`, element.id || element.tagName);
        } else {
            // console.warn("Forsøgte at anvende skriftstørrelse på et ikke-eksisterende element.");
        }
    }

    /**
     * Gemmer en skriftstørrelsespræference i LocalStorage.
     * @param {string} storageKey - Nøglen der skal bruges i LocalStorage.
     * @param {number} sizeInPx - Skriftstørrelsen der skal gemmes.
     */
    function saveFontSizeToLocalStorage(storageKey, sizeInPx) {
        try {
            localStorage.setItem(storageKey, sizeInPx.toString());
            // console.log(`Saved font size ${sizeInPx}px to LocalStorage with key: ${storageKey}`);
        } catch (e) {
            console.error("Fejl ved lagring af skriftstørrelse til LocalStorage:", e);
        }
    }

    /**
     * Indlæser skriftstørrelsespræferencer fra LocalStorage og anvender dem.
     * Kaldes ved sideindlæsning.
     */
    function loadFontSizesFromLocalStorage() {
        // console.log("Forsøger at indlæse skriftstørrelser fra LocalStorage...");
        try {
            const savedStoryDisplaySize = localStorage.getItem(STORY_DISPLAY_FONT_KEY);
            if (savedStoryDisplaySize) {
                const newSize = parseInt(savedStoryDisplaySize, 10);
                if (!isNaN(newSize) && newSize >= MIN_FONT_SIZE_PX && newSize <= MAX_FONT_SIZE_PX) {
                    currentStoryDisplayFontSize = newSize;
                    // console.log(`Indlæst gemt skriftstørrelse for storyDisplay: ${newSize}px`);
                }
            }
            applyFontSize(storyDisplay, currentStoryDisplayFontSize);

            const savedNarrativeStorySize = localStorage.getItem(NARRATIVE_STORY_FONT_KEY);
            if (savedNarrativeStorySize) {
                const newSize = parseInt(savedNarrativeStorySize, 10);
                if (!isNaN(newSize) && newSize >= MIN_FONT_SIZE_PX && newSize <= MAX_FONT_SIZE_PX) {
                    currentNarrativeStoryFontSize = newSize;
                    // console.log(`Indlæst gemt skriftstørrelse for narrativeGeneratedStory: ${newSize}px`);
                }
            }
            // 'narrativeGeneratedStory' er ID'et fra din HTML for den narrative historie-div
            // Sørg for, at 'narrativeGeneratedStory' er korrekt defineret globalt eller hentet her
            if (document.getElementById('narrative-generated-story')) { // Tjek om elementet findes
                 applyFontSize(document.getElementById('narrative-generated-story'), currentNarrativeStoryFontSize);
            }


        } catch (e) {
            console.error("Fejl ved indlæsning af skriftstørrelser fra LocalStorage:", e);
        }
    }

    /**
     * Opdaterer skriftstørrelsen for et givet element og gemmer præferencen.
     * @param {HTMLElement} targetElement - Elementet der skal opdateres.
     * @param {number} change - Ændringen i pixels (+FONT_SIZE_STEP_PX eller -FONT_SIZE_STEP_PX).
     * @param {boolean} reset - Sæt til true for at nulstille til DEFAULT_FONT_SIZE_PX.
     * @param {'storyDisplay' | 'narrativeStory'}elementType - Type af element for korrekt variabel og storage key.
     */
    function updateFontSize(targetElement, change, reset = false, elementType) {
        let currentSize;
        let storageKey;

        if (elementType === 'storyDisplay') {
            currentSize = currentStoryDisplayFontSize;
            storageKey = STORY_DISPLAY_FONT_KEY;
        } else if (elementType === 'narrativeStory') {
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

        // Begræns størrelsen indenfor MIN og MAX
        newSize = Math.max(MIN_FONT_SIZE_PX, Math.min(newSize, MAX_FONT_SIZE_PX));

        if (targetElement) {
            applyFontSize(targetElement, newSize);
            if (elementType === 'storyDisplay') {
                currentStoryDisplayFontSize = newSize;
            } else {
                currentNarrativeStoryFontSize = newSize;
            }
            saveFontSizeToLocalStorage(storageKey, newSize);
            // console.log(`Font size for ${elementType} (ID: ${targetElement.id}) updated to: ${newSize}px`);
        } else {
            // console.warn(`Target element for font size update (type: ${elementType}) er ikke fundet i DOM.`);
        }
    }

    // === Event Listeners for Skriftstørrelseskontrol ===

    // For Standard Historier (#story-display)
    if (decreaseFontButton && storyDisplay) {
        decreaseFontButton.addEventListener('click', () => {
            updateFontSize(storyDisplay, -FONT_SIZE_STEP_PX, false, 'storyDisplay');
        });
    }
    if (increaseFontButton && storyDisplay) {
        increaseFontButton.addEventListener('click', () => {
            updateFontSize(storyDisplay, FONT_SIZE_STEP_PX, false, 'storyDisplay');
        });
    }
    if (resetFontButton && storyDisplay) {
        resetFontButton.addEventListener('click', () => {
            updateFontSize(storyDisplay, 0, true, 'storyDisplay');
        });
    }

    // For Narrative Historier (#narrative-generated-story)
    // Sørg for, at 'narrativeGeneratedStory' er en gyldig reference til det korrekte HTML element
    // Vi bruger document.getElementById her for at sikre, vi har det nyeste reference, hvis DOM ændrer sig.
    const narrativeStoryElement = document.getElementById('narrative-generated-story');

    if (narrativeDecreaseFontButton && narrativeStoryElement) {
        narrativeDecreaseFontButton.addEventListener('click', () => {
            updateFontSize(narrativeStoryElement, -FONT_SIZE_STEP_PX, false, 'narrativeStory');
        });
    } else if (narrativeDecreaseFontButton && !narrativeStoryElement) {
        // console.warn("narrativeDecreaseFontButton findes, men #narrative-generated-story ikke. Listener ikke tilføjet.");
    }

    if (narrativeIncreaseFontButton && narrativeStoryElement) {
        narrativeIncreaseFontButton.addEventListener('click', () => {
            updateFontSize(narrativeStoryElement, FONT_SIZE_STEP_PX, false, 'narrativeStory');
        });
    } else if (narrativeIncreaseFontButton && !narrativeStoryElement) {
        // console.warn("narrativeIncreaseFontButton findes, men #narrative-generated-story ikke. Listener ikke tilføjet.");
    }

    if (narrativeResetFontButton && narrativeStoryElement) {
        narrativeResetFontButton.addEventListener('click', () => {
            updateFontSize(narrativeStoryElement, 0, true, 'narrativeStory');
        });
    } else if (narrativeResetFontButton && !narrativeStoryElement) {
        // console.warn("narrativeResetFontButton findes, men #narrative-generated-story ikke. Listener ikke tilføjet.");
    }

    // Indlæs gemte skriftstørrelser ved sideindlæsning
loadFontSizesFromLocalStorage();

    // === NYT: Kontrol af TTS stemmevalgsdropdown synlighed baseret på brugerrolle ===
    // Denne logik forudsætter, at du har en måde at vide, om brugeren er 'basic' eller 'premium'.
    // Typisk hentes dette fra en server-side variable sat af Flask (f.eks. current_user.role).
    // Da Flask kan injicere JS-variabler via Jinja2, kan vi antage, at 'userRole' er tilgængelig.
    // Hvis userRole ikke er defineret via Jinja2, skal denne del justeres for at hente det.
    // For nu antager vi, at Flask (som du har opsat i index.html for knapper) vil styre den indledende 'display: none;'
    // og vi kan lytte efter, når brugeren logger ind/ud (som ville kræve en sidegenindlæsning).
    // Vi kan tilføje en simpel tjek ved DOMContentLoaded:
    function updateTtsVoiceSelectionVisibility() {
        const currentUserRoleElement = document.getElementById('current-user-role-data'); // En skjult div/input i HTML med brugerens rolle
        let userRole = 'free'; // Standard til 'free' hvis element ikke findes
        if (currentUserRoleElement) {
            userRole = currentUserRoleElement.dataset.role;
        } else {
             // Hvis du ikke har en skjult element med user-role, kan vi udlede det fra om 'read-aloud-button' er disabled
             // Dette er en workaround, bedre er at have en server-side JS variable
            if (readAloudButton && !readAloudButton.classList.contains('disabled-button')) {
                // Hvis knappen ikke er disabled, antager vi Basic/Premium
                userRole = 'basic'; // Eller 'premium', det er nok at vide at de har adgang
            }
        }


        if (ttsVoiceSelectionDiv) {
            if (userRole === 'basic' || userRole === 'premium') {
                ttsVoiceSelectionDiv.style.display = 'block'; // Eller 'flex' afhængig af din CSS
                console.log("TTS Voice Selection Dropdown: Synlig (Basic/Premium user).");
            } else {
                ttsVoiceSelectionDiv.style.display = 'none';
                console.log("TTS Voice Selection Dropdown: Skjult (Free user/Guest).");
            }
        } else {
            console.warn("TTS Voice Selection Div (#tts-voice-selection) not found.");
        }
    }

    // Kald funktionen ved indlæsning for at sætte korrekt synlighed
    updateTtsVoiceSelectionVisibility();

    // Lyt efter ændringer i login-status (dette kræver en sidegenindlæsning i en rigtig app)
    // For nu er det primært DOMContentLoaded, der styrer dette.
    // === SLUT: Kontrol af TTS stemmevalgsdropdown synlighed ===

    // === NYT: Fane Navigation Funktionalitet (Rettet Version) ===
    const tabButtons = document.querySelectorAll('.tab-button');
    const contentSections = document.querySelectorAll('.content-section');

    // ERSTAT HELE BLOKKEN FRA DIN FORESPØRGSEL MED DENNE:

    if (tabButtons.length > 0 && contentSections.length > 0) {
        const historieOutput = document.getElementById('historie-output');
        const imageSection = document.getElementById('billede-til-historien-sektion');

        const handleTabClick = (button) => {
            if (button.classList.contains('active')) return;

            const tabName = button.textContent.trim().replace('🔒', '').trim();
            trackGAEvent('change_tab', 'Navigation', `Tab: ${tabName}`, null);

            // Find og skjul altid quiz-sektionen, når der skiftes fane.
            // Dette fungerer som en "nulstilling".
            const quizSektion = document.getElementById('quiz-sektion');
            if (quizSektion) {
                quizSektion.classList.add('hidden');
            }

            tabButtons.forEach(btn => btn.classList.remove('active'));
            contentSections.forEach(section => section.classList.add('hidden'));

            button.classList.add('active');
            const targetId = button.dataset.tabTarget;
            const targetSection = document.querySelector(targetId);
            if (targetSection) {
                targetSection.classList.remove('hidden');
            }

            const historieOutput = document.getElementById('historie-output');
            const imageSection = document.getElementById('billede-til-historien-sektion');
            if (historieOutput) {
                historieOutput.classList.toggle('hidden', targetId !== '#generator' && targetId !== '#laesehesten-module');
            }
            if (imageSection) {
                imageSection.classList.add('hidden');
            }

            const userRole = document.getElementById('current-user-role-data')?.dataset.role || 'guest';

            if (targetId === '#logbook-module') {
                if (userRole === 'guest') {
                    document.getElementById('logbook-list-container').innerHTML = `<p style="text-align: center; padding: 20px;"><a href="/auth/login">Log venligst ind</a> for at bruge logbogen og profiler.</p>`;
                } else {
                    initializeLogbook();
                }
            } else if (targetId === '#narrative-support-module') {
                if (userRole === 'premium') {
                    listChildProfilesApi().then(populateNarrativeProfileSelector).catch(err => console.error(err));
                }
            }
        };

        // Trin 1: Sæt funktionalitet på FANE-knapperne
        tabButtons.forEach(button => {
            button.addEventListener('click', () => handleTabClick(button));
        }); // <-- Her slutter forEach-løkken

        // Trin 2: Sæt funktionalitet på "GEM I LOGBOG"-knappen (placeret KORREKT her)
        const saveToLogbookButton = document.getElementById('save-to-logbook-button');
        if (saveToLogbookButton) {
            saveToLogbookButton.addEventListener('click', async () => {
                const titleElement = document.getElementById('story-section-heading');
                const contentElement = document.getElementById('story-text-content');

                const title = titleElement ? titleElement.textContent.replace(/LIX: \d+/, '').trim() : "Uden Titel";
                const content = contentElement ? contentElement.textContent.trim() : "";

                if (!content) {
                    alert("Der er ingen historie at gemme.");
                    return;
                }

                saveToLogbookButton.disabled = true;
                saveToLogbookButton.textContent = 'Gemmer...';

                try {
                    const result = await saveHojtlasningStoryApi({ title: title, content: content });
                    if (result.success) {
                        trackGAEvent('save_to_logbook', 'Højtlæsning', `Story ID: ${result.story_id}`, null);
                    }
                    saveToLogbookButton.textContent = 'Gemt!';
                    saveToLogbookButton.style.backgroundColor = '#28a745';
                    console.log(result.message);

                } catch (error) {
                    console.error("Fejl ved gemning til logbog:", error);
                    alert(`Kunne ikke gemme historien: ${error.message}`);
                    saveToLogbookButton.disabled = false;
                    saveToLogbookButton.textContent = 'Gem i Logbog';
                }
            });
        }

        // Trin 3: Håndter den fane, der er aktiv ved sideindlæsning
        const initiallyActiveButton = document.querySelector('.tab-button.active');
        if (initiallyActiveButton) {
            handleTabClick(initiallyActiveButton);
        }
    }

// === SLUT PÅ NYT: Fane Navigation Funktionalitet ===

    // === NYT: Dropdown Funktionalitet for Narrativ Støtte ===
    const dropdownToggles = document.querySelectorAll('.narrative-info-dropdown .dropdown-toggle');

    if (dropdownToggles.length > 0) {
        dropdownToggles.forEach(toggle => {
            toggle.addEventListener('click', () => {
                const content = toggle.nextElementSibling; // .dropdown-content er lige efter knappen
                if (content && content.classList.contains('dropdown-content')) {
                    content.classList.toggle('hidden');
                    toggle.classList.toggle('open'); // For at style pilen via CSS
                    console.log(`Dropdown toggled for: ${toggle.textContent.trim().substring(0, 30)}... Is hidden: ${content.classList.contains('hidden')}`);
                } else {
                    console.error("Could not find dropdown content for toggle:", toggle);
                }
            });
        });
        console.log("Narrative info dropdown functionality initialized.");
    } else {
        console.warn("No dropdown toggles found. Narrative info dropdowns will not work.");
    }
    // === SLUT PÅ NYT: Dropdown Funktionalitet for Narrativ Støtte ===
    // Event listener for informations-dropdown om fejlårsager (i Godnathistorie-fanen)
    if (failureInfoDropdownToggle && failureInfoDropdownContent) {
        failureInfoDropdownToggle.addEventListener('click', () => {
            failureInfoDropdownContent.classList.toggle('hidden');
            failureInfoDropdownToggle.classList.toggle('open'); // Bruges til at rotere pilen via CSS

            // Valgfri logging til konsollen for at bekræfte funktionalitet
            // console.log(`Failure info dropdown toggled. Is hidden: ${failureInfoDropdownContent.classList.contains('hidden')}`);
        });
        console.log("Event listener for failure info dropdown initialized.");
    } else {
        console.warn("Elementer for 'failure info dropdown' (#failure-info-dropdown-toggle eller #failure-info-dropdown-content) blev ikke fundet i DOM.");
    }

    // === NYT: "Andet..." Funktionalitet for Dynamiske Selects ===
    const dynamicSelects = document.querySelectorAll('.dynamic-select');

    if (dynamicSelects.length > 0) {
        dynamicSelects.forEach(selectElement => {
            selectElement.addEventListener('change', function() { // Brug 'function' for at 'this' refererer til selectElement
                const otherInputId = this.dataset.otherInputId;
                const otherInputElement = document.getElementById(otherInputId);

                if (otherInputElement) {
                    if (this.value === 'other') {
                        otherInputElement.classList.remove('hidden');
                        otherInputElement.focus(); // Sæt fokus på feltet for bekvemmelighed
                        console.log(`"Andet..." valgt for ${this.id}. Viser inputfelt: ${otherInputId}`);
                    } else {
                        otherInputElement.classList.add('hidden');
                        otherInputElement.value = ''; // Ryd feltet når det skjules
                        console.log(`Anden option end "Andet..." valgt for ${this.id}. Skjuler inputfelt: ${otherInputId}`);
                    }
                } else {
                    console.error(`Could not find "other" input element with ID: ${otherInputId} for select: ${this.id}`);
                }
            });
        });
        console.log("Dynamic select 'other...' functionality initialized.");
    } else {
        console.warn("No dynamic select elements found. 'Other...' functionality will not be available.");
    }
    // === SLUT PÅ NYT: "Andet..." Funktionalitet for Dynamiske Selects ===

    // === NYT: Dynamiske Inputfelter for "Vigtige Relationer" (Narrativ Støtte) ===
    const narrativeRelationsContainer = document.getElementById('narrative-relations-container');
    const narrativeAddRelationButton = document.getElementById('narrative-add-relation-button');
    let narrativeRelationCounter = 1; // For unikke ID'er

    function createNarrativeRelationGroup() {
        narrativeRelationCounter++;
        const relationGroup = document.createElement('div');
        relationGroup.className = 'relation-group';

        // Navnefelt
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

        // Typefelt
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

        // Fjern-knap
        const removeButton = document.createElement('button');
        removeButton.type = 'button';
        removeButton.textContent = '-';
        removeButton.className = 'remove-button'; // Ikke 'initial-remove-button' her
        removeButton.addEventListener('click', () => {
            relationGroup.remove();
            // Her kunne man tilføje logik til at gemme til LocalStorage, hvis det var ønsket for relationer
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
            console.log("New narrative relation group added.");
        });

        // Gør den første fjern-knap (hvis den findes og er 'initial') funktionel
        const initialNarrativeRelationRemoveButton = narrativeRelationsContainer.querySelector('.relation-group .initial-remove-button');
        if (initialNarrativeRelationRemoveButton) {
            initialNarrativeRelationRemoveButton.addEventListener('click', (e) => {
                // Forhindr at fjerne den første gruppe helt, ryd kun dens felter,
                // da vi forventer mindst én gruppe.
                // Eller tillad fjernelse hvis det er okay at have nul relationer.
                // For nu, lad os rydde felterne.
                const parentGroup = e.target.closest('.relation-group');
                if (parentGroup) {
                    parentGroup.querySelectorAll('input[type="text"]').forEach(input => input.value = '');
                    console.log("Initial narrative relation group fields cleared.");
                }
            });
            // Overvej at fjerne 'initial-remove-button' klassen og 'aria-hidden' efter den er gjort funktionel,
            // eller bedre: Skift dens funktionalitet til at rydde felter i stedet for at fjerne gruppen.
            // For nu lader vi den være, da den er skjult via CSS.
        }
        console.log("Dynamic narrative relations functionality initialized.");
    } else {
        console.warn("Add narrative relation button or container not found. Dynamic relations will not work.");
    }
    // === SLUT PÅ NYT: Dynamiske Inputfelter for "Vigtige Relationer" (Narrativ Støtte) ===

    // === NYT: Dynamiske Inputfelter for Standard Historieelementer (Narrativ Støtte) ===

    // Funktion til at tilføje "Hovedkarakter (Narrativ)"
    const narrativeMainCharsContainer = document.getElementById('narrative-main-characters-container');
    const narrativeAddMainCharButton = document.getElementById('narrative-add-main-char-button');
    let narrativeMainCharCounter = 1; // For unikke ID'er

    function createNarrativeMainCharacterGroup() {
        narrativeMainCharCounter++;
        const characterGroup = document.createElement('div');
        characterGroup.className = 'character-group'; // Genbruger styling

        // Beskrivelsesfelt
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

        // Navnefelt
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

        // Fjern-knap
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

    if (narrativeAddMainCharButton && narrativeMainCharsContainer) {
        narrativeAddMainCharButton.addEventListener('click', () => {
            const newGroup = createNarrativeMainCharacterGroup();
            narrativeMainCharsContainer.appendChild(newGroup);
            console.log("New narrative main character group added.");
        });
        // Gør evt. første 'initial-remove-button' funktionel (f.eks. ryd felter)
        // (Lignende logik som for 'Vigtige Relationer' kan tilføjes her hvis nødvendigt)
    } else {
        console.warn("Add narrative main character button or container not found.");
    }

    // Generel funktion til at tilføje simple inputfelter (Steder, Plot)
    const genericAddButtons = document.querySelectorAll('.generic-add-button');
    let genericInputCounter = {}; // Holder styr på tællere for forskellige typer

    if (genericAddButtons.length > 0) {
        genericAddButtons.forEach(button => {
            button.addEventListener('click', function() { // Brug 'function' for 'this'
                const containerId = this.dataset.containerId;
                const inputName = this.dataset.inputName;
                const placeholder = this.dataset.inputPlaceholder;
                const idPrefix = this.dataset.inputIdPrefix;
                const container = document.getElementById(containerId);

                if (!container) {
                    console.error(`Generic add button: Container with ID '${containerId}' not found.`);
                    return;
                }

                // Initialiser tæller for denne type hvis den ikke findes
                if (genericInputCounter[idPrefix] === undefined) {
                    genericInputCounter[idPrefix] = 1;
                }
                genericInputCounter[idPrefix]++;

                const inputGroup = document.createElement('div');
                inputGroup.className = 'input-group';

                const label = document.createElement('label');
                label.htmlFor = `${idPrefix}-${genericInputCounter[idPrefix]}`;
                label.className = 'sr-only';
                label.textContent = placeholder; // Simpel label tekst

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

                inputGroup.appendChild(label); // Selvom sr-only, god praksis
                inputGroup.appendChild(newInput);
                inputGroup.appendChild(removeButton);
                container.appendChild(inputGroup);
                console.log(`Generic input added to ${containerId} with name ${inputName}`);
            });
        });
        console.log("Generic add button functionality initialized.");
    } else {
        console.warn("No generic add buttons found.");
    }
    // === SLUT PÅ NYT: Dynamiske Inputfelter for Standard Historieelementer (Narrativ Støtte) ===


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

// I static/script.js

async function handleGenerateClick(event) {
    event.preventDefault();

    // Find kun de elementer, der er uden for output-området
    const generateButton = document.getElementById('generate-button');
    const aiModelSwitch = document.getElementById('ai-model-switch');

    // Dataindsamling... (som før)
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

    // --- START PÅ NY, ROBUST LOADING-SEKVENS ---
    if(generateButton) { generateButton.disabled = true; generateButton.textContent = 'Laver historie...'; }

    // Find de dynamiske elementer her, lige før brug
    const storyDisplay = document.getElementById('story-display');
    const storySectionHeading = document.getElementById('story-section-heading');
    const storyShareButtonsContainer = document.getElementById('story-share-buttons');
    const audioPlayer = document.getElementById('audio-player');

    // Ryd output-området og opret en ny loader
    if(storyDisplay) {
        storyDisplay.innerHTML = `
            <div id="story-loading-indicator">
                <p>Historien genereres... Vent venligst.</p>
                <span class="spinner"></span>
            </div>
        `;
    }
    if(storySectionHeading) storySectionHeading.textContent = 'Jeres historie';
    if(storyShareButtonsContainer) storyShareButtonsContainer.classList.add('hidden');
    if(audioPlayer) { audioPlayer.classList.add('hidden'); audioPlayer.src = ''; }
    document.querySelectorAll('.js-generate-image').forEach(button => button.disabled = true);
    // --- SLUT PÅ NY, ROBUST LOADING-SEKVENS ---

    try {
        const result = await generateStoryApi(dataToSend);
        if (result.error) throw new Error(result.error);

        trackGAEvent('generate_story', 'Højtlæsning', `Mood: ${dataToSend.mood} - Length: ${dataToSend.laengde}`, null);

        const cleanTitle = (result.title || "Jeres historie").trim();
        const cleanStory = (result.story || "Modtog en tom historie.").replace(/^\s+/, '');

        if(storyDisplay) {
            storyDisplay.innerHTML = ''; // Ryd loading-indikator
            const newStoryContentDiv = document.createElement('div');
            newStoryContentDiv.id = 'story-text-content';
            newStoryContentDiv.textContent = cleanStory;
            storyDisplay.appendChild(newStoryContentDiv);
        }

        if(storySectionHeading) storySectionHeading.textContent = cleanTitle;
        if (storyShareButtonsContainer && cleanStory) storyShareButtonsContainer.classList.remove('hidden');

        const userRole = document.getElementById('current-user-role-data')?.dataset.role || 'guest';
        document.querySelectorAll('.js-generate-image').forEach(button => {
            if (userRole !== 'guest' && cleanStory) {
                button.disabled = false;
                button.removeAttribute('title');
            }
        });

    } catch (error) {
         if(storyDisplay) storyDisplay.innerHTML = `<p style="color: red; text-align: center;">Ups! Noget gik galt: ${error.message}.</p>`;
         if(storySectionHeading) storySectionHeading.textContent = "Fejl ved generering";
    } finally {
         if(generateButton) { generateButton.disabled = false; generateButton.textContent = 'Skab Historie'; }
    }
}

// TILFØJ DISSE 3 NYE FUNKTIONER I static/script.js

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

// ERSTAT HELE checkAnswer FUNKTIONEN I static/script.js

function checkAnswer(event) {
    const btn = event.target;
    const qIndex = parseInt(btn.dataset.qIndex, 10);
    const oIndex = parseInt(btn.dataset.oIndex, 10);

    const questionData = currentQuizData[qIndex];
    const parentOptions = btn.parentElement;

    // Deaktiver alle knapper for dette spørgsmål, så man ikke kan svare igen
    parentOptions.querySelectorAll('button').forEach(button => button.disabled = true);

    // Farv knapperne baseret på svaret
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

    // Tjek om alle spørgsmål er besvaret korrekt
    if (correctAnswersCount === currentQuizData.length) {
        // Vis succes-beskeden
        quizFeedback.textContent = "Fantastisk! Du har svaret rigtigt på alt. Du kan nu generere et billede til historien.";
        quizFeedback.className = 'flash-message flash-success';
        quizFeedback.classList.remove('hidden');

        // Først, fjern en eventuel gammel knap for at undgå dubletter
        document.getElementById('dynamic-quiz-reward-button')?.remove();

        // Opret den nye knap i hukommelsen
        const rewardButton = document.createElement('button');
        rewardButton.id = 'dynamic-quiz-reward-button'; // Giver den et unikt ID
        rewardButton.type = 'button';
        rewardButton.textContent = 'Generer Billede';
        rewardButton.className = 'utility-button quiz-success-button'; // Giver den grøn stil

        // Fortæl knappen, hvad den skal gøre, når man klikker på den
        rewardButton.addEventListener('click', handleGenerateImageFromStoryClick);

        // Indsæt den nye knap i dokumentet, lige efter feedback-beskeden
        quizFeedback.insertAdjacentElement('afterend', rewardButton);
        // --- SLUT PÅ NY KODE ---
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


    // === Lyd Generering (TTS) ===
async function handleReadAloudClick() {
    console.log("Read Aloud: Started");

    if (readAloudButton.classList.contains('disabled-button')) {
        console.log("Read Aloud: Button is disabled (user not Basic/Premium).");
        if (loginPromptAudio) {
            loginPromptAudio.classList.remove('hidden');
            setTimeout(() => loginPromptAudio.classList.add('hidden'), 5000);
        }
        return;
    }

    const storyTextContent = document.getElementById('story-text-content');
    const storyText = storyTextContent ? storyTextContent.textContent.trim() : "";

    if (!storyText || storyText === '' || storyText.includes('Historien genereres...')) {
        console.warn("Read Aloud: No valid story text found in #story-text-content.");
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
    console.log(`Read Aloud: Generating audio for voice: ${selectedVoice}`);

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
                    // KORREKTION: Vent til buffer er færdig med at opdatere FØR endOfStream kaldes
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
                        console.log("Read Aloud: Stream complete and ended correctly.");
                    }
                    break;
                }
                if (value) {
                    await appendBuffer(value);
                }
            }
        });

        mediaSource.addEventListener('sourceended', () => console.log('MediaSource ended'));
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
        console.log("Read Aloud: Finished processing.");
    }
}

// KODEN TIL HØJTLÆSNINGS-FANENS BILLEDE-KNAP

async function handleGenerateImageFromStoryClick() {
    console.log("--> handleGenerateImageFromStoryClick (FOR HØJTLÆSNING) startet");

    // RETTELSE: Hent referencen til historie-elementet her, LIGE før vi skal bruge den.
    const storyContentElement = document.getElementById('story-text-content');

    const currentStoryText = storyContentElement ? storyContentElement.textContent.trim() : "";
    if (!currentStoryText) {
        alert("Generer venligst en historie først.");
        return;
    }

    // Indsaml originale bruger-inputs fra Højtlæsnings-fanen
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
        if(v) steder.push(v);
    });

    // UI-håndtering
    imageSection.classList.remove('hidden');
    storyImageContainer.classList.remove('hidden');
    problemImageContainer.classList.add('hidden');
    storyImageLoader.classList.remove('hidden');
    storyImageDisplay.classList.add('hidden');
    storyImageError.classList.add('hidden');
    generateImageButtons.forEach(button => button.disabled = true);

    try {
        // Pak alle informationer (historie + bruger-inputs) i ét objekt
        const dataToSend = {
            story_text: currentStoryText,
            karakterer: karakterer,
            steder: steder
        };

        trackGAEvent('generate_image', 'Højtlæsning', 'Success', null);

        // Kald den opdaterede API-funktion
        const result = await generateImageApi(dataToSend);

        if (result.image_url) {
            storyImageDisplay.src = result.image_url;
            storyImageDisplay.classList.remove('hidden');
        } else {
            throw new Error(result.error || "Uventet svar fra serveren.");
        }
    } catch (error) {
        storyImageError.textContent = `Fejl: ${error.message}`;
        storyImageError.classList.remove('hidden');
    } finally {
        storyImageLoader.classList.add('hidden');
        generateImageButtons.forEach(button => button.disabled = false);
    }
}

async function handleGenerateNarrativeImagesClick() {
    if (!currentNarrativeData || !currentNarrativeData.storyContent) {
        alert("Fejl: Der er ingen genereret narrativ historie at skabe billeder fra.");
        return;
    }

    narrativeGenerateImagesButton.disabled = true;
    narrativeGenerateImagesButton.textContent = "Genererer billeder...";

    // Nulstil UI
    imageSection.classList.remove('hidden');
    storyImageContainer.classList.remove('hidden');
    problemImageContainer.classList.remove('hidden');
    storyImageLoader.classList.remove('hidden');
    problemImageLoader.classList.remove('hidden');
    [storyImageDisplay, problemImageDisplay, storyImageError, problemImageError].forEach(el => el.classList.add('hidden'));
    storyImageError.textContent = '';
    problemImageError.textContent = '';

    // --- RETTELSE LIGGER HER ---
    // Kald den nye, korrekte API funktion for historie-billedet
    const storyImagePromise = generateNarrativeStoryImageApi(currentNarrativeData);
    // Kaldet til problem-billedet er uændret, da det allerede virker
    const problemImagePromise = generateProblemImageApi(currentNarrativeData);
    // --- SLUT PÅ RETTELSE ---

    // Håndtering af resultater (er uændret)
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

    // Denne funktion samler data og starter genereringen
    function startNarrativeGeneration(strategy = null) {
        const narrativeData = collectNarrativeData();

        // Hvis en strategi er valgt, tilføj de ekstra data
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

// Den almindelige "Generer"-knap kalder nu start-funktionen uden strategi
    if (narrativeGenerateStoryButton) {
        narrativeGenerateStoryButton.addEventListener('click', () => startNarrativeGeneration(null));
    }

    // === Tilknyt Event Listeners ===
    // Indlæs gemte lyttere for historie-sektionen
    loadAndDisplaySavedListeners();
    // NYT: Initialiserer det nye Læsehesten-modul
    initializeLaesehestenModule();

    // Funktion til at forudfylde felter med AI-forslag
    function populateCharacterTraitFields(suggestions) {
        console.log("populateCharacterTraitFields kaldt med forslag:", suggestions);
        const aiSuggestionClass = 'ai-suggested-input';
        let attemptedToFillProblemCharacter = false;

        function setSimpleInput(element, value) {
            if (element && value && element.value.trim() === '') {
                element.value = value;
                element.classList.add(aiSuggestionClass);
                element.addEventListener('input', () => element.classList.remove(aiSuggestionClass), { once: true });
                return true; // Indikerer at feltet blev ændret
            } else if (element && value && element.value.trim() !== '') {
                console.log(`Skipped pre-filling ${element.id || 'element'} because it already has user input: "${element.value.trim()}"`);
            }
            return false; // Indikerer at feltet ikke blev ændret
        }

        // Problem-karakter forslag
        if (suggestions && suggestions.problem_character_suggestions) {
            const ps = suggestions.problem_character_suggestions;
            console.log("Forsøger at anvende forslag til Problem-Karakter:", ps);
            // Vi sætter attemptedToFillProblemCharacter til true, hvis der overhovedet er forslag til problem karakteren.
            // Selve udfyldningen afhænger af, om felterne er tomme.
            if (Object.keys(ps).length > 0) { // Tjek om der er nøgler i problem_character_suggestions
                attemptedToFillProblemCharacter = true; // Vi har forslag at arbejde med
                 // Kald setSimpleInput for hvert felt. Det er ikke nødvendigt at tjekke returværdien her for denne logik.
                setSimpleInput(narrativeProblemIdentityNameInput, ps.identity_name ? ps.identity_name[0] : null);
                setSimpleInput(narrativeProblemRoleFunctionInput, ps.role_function ? ps.role_function[0] : null);
                setSimpleInput(narrativeProblemPurposeIntentionInput, ps.purpose_intention ? ps.purpose_intention[0] : null);
                setSimpleInput(narrativeProblemBehaviorActionInput, ps.behavior_action ? ps.behavior_action[0] : null);
                setSimpleInput(narrativeProblemInfluenceInput, ps.influence_on_protagonist ? ps.influence_on_protagonist[0] : null);
            }
        } else {
            console.log("Ingen forslag til Problem-Karakter modtaget i suggestions objektet.");
        }

        // Protagonist-karakter forslag (bliver ignoreret som før)
        if (suggestions && suggestions.protagonist_character_suggestions) {
            console.log("Forslag til Protagonist-Karakter modtaget, men vil IKKE blive anvendt.");
        }

        console.log("populateCharacterTraitFields udført. Forsøgte at udfylde problem-karakter:", attemptedToFillProblemCharacter);
        return attemptedToFillProblemCharacter; // Returnerer true hvis der var forslag til problem-karakteren
    }

    // === Event Listeners for Narrativ Støtte Knapper ===
    if (narrativeSuggestTraitsButton) {
        narrativeSuggestTraitsButton.addEventListener('click', async () => {
            console.log("Narrative 'Suggest Traits' button clicked.");
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
                console.log("Forslag til karaktertræk modtaget fra API:", suggestions);

                if (suggestions && !suggestions.error) {
                    const attemptedProblemFill = populateCharacterTraitFields(suggestions);

                    if (attemptedProblemFill) {
                        // Tjek om nogle af problemkarakter-felterne faktisk blev udfyldt (blev ændret)
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
                             console.log("AI har foreslået karaktertræk for Problem-Karakteren, og felter er opdateret."); // Erstatter alert med console.log
                        } else if (attemptedProblemFill && !actuallyFilledSomething) {
                            console.log("AI havde forslag til Problem-Karakteren, men alle relevante felter var allerede udfyldt eller matchede forslaget.");
                        } else { // !attemptedProblemFill (bør dækkes af det ydre 'else'-tilfælde)
                            console.log("Ingen forslag til Problem-Karakteren blev anvendt (muligvis ingen forslag fra AI).");
                        }
                    } else {
                         console.log("AI returnerede ingen forslag til Problem-Karakteren (attemptedProblemFill var false).");
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

    // Historie-generator knapper
    if (generateButton) { generateButton.addEventListener('click', handleGenerateClick); } else { console.error("Generate button (#generate-button) not found!"); }
    if (resetButton && storyShareButtonsContainer) { // Sikrer at reset knappen findes i containeren
        storyShareButtonsContainer.querySelector('#reset-button').addEventListener('click', () => handleResetClick(false));
    } else { console.error("Reset button (inside #story-share-buttons) not found!"); }

    if (autofillButton) { autofillButton.addEventListener('click', autofillFields); } else { console.error("Autofill button (#autofill-button) not found!"); }
    if (addListenerButton) { addListenerButton.addEventListener('click', addListenerGroup); } else { console.error("Add listener button (#add-listener-button) not found!"); }
    if (addKarakterButton) { addKarakterButton.addEventListener('click', addCharacterGroup); } else { console.error("Add character button (#add-karakter-button) not found!"); }
    if (readAloudButton) { readAloudButton.addEventListener('click', handleReadAloudClick); } else { console.info("Read Aloud button (#read-aloud-button) not found or user not authenticated."); }
    if (toggleFeedbackButton) { toggleFeedbackButton.addEventListener('click', toggleFeedbackEmbed); } else { console.error("Toggle feedback button (#toggle-feedback-button) not found!"); }// ERSTAT DEN GAMLE KODEBLOK I static/script.js MED DENNE NYE:

    // Hent knapperne via deres unikke ID'er
    const hojtlaesningImageButton = document.getElementById('generate-image-from-output-button');
    const narrativeImagesButton = document.getElementById('narrative-generate-images-button');

    // Tilføj den korrekte listener til Højtlæsnings-knappen
    if (hojtlaesningImageButton) {
        hojtlaesningImageButton.addEventListener('click', handleGenerateImageFromStoryClick);
        console.log("Event listener tilføjet til Højtlæsnings billed-knap.");
    } else {
        console.warn("Højtlæsnings billed-knap (#generate-image-from-output-button) ikke fundet.");
    }

    // Tilføj den korrekte listener til Narrativ Støtte-knappen
    if (narrativeImagesButton) {
        narrativeImagesButton.addEventListener('click', handleGenerateNarrativeImagesClick);
        console.log("Event listener tilføjet til Narrativ Støtte billed-knap.");
    } else {
        console.warn("Narrativ Støtte billed-knap (#narrative-generate-images-button) ikke fundet.");
    }

    // Generiske "Tilføj felt" knapper for historie (sted, plot)
    document.querySelectorAll('#generator .add-button[data-container]').forEach(button => {
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

    console.log("Script loaded and all initial event listeners attached, including for Narrative Support.");

// INDSÆT DENNE KODEBLOK (f.eks. omkring linje 824)

    // Funktion til at style vejlednings-knapper direkte med JavaScript
    function styleGuidanceDropdowns() {
        // Nøgleord der identificerer en vejledningsknap
        const keywords = ['Vejledning', 'Hvad er'];
        // Den blå farve vi vil bruge (direkte farvekode for at være sikker)
        const infoColor = '#bbbe70';

        // Find alle dropdown-knapper på siden
        document.querySelectorAll('.dropdown-toggle').forEach(button => {
            const buttonText = button.textContent.trim();

            // Tjek om knappens tekst indeholder et af vores nøgleord
            if (keywords.some(keyword => buttonText.includes(keyword))) {
                // Sæt farven direkte på knappen
                button.style.color = infoColor;
            }
        });
        console.log("Vejlednings-knapper er blevet stylet med JavaScript.");
    }

    // Kald den nye funktion for at udføre stylingen
    styleGuidanceDropdowns();

    initializeInfoIcons(); // Kald funktionen for at aktivere infoknapperne


    // ===================================================================
    // START: ENDELIG LOGIK FOR BØRNEPROFILER (Version 5 - Inkl. alle rettelser)
    // ===================================================================
    let allProfilesData = []; // Cache for hentede profiler

    /**
     * Udfylder dropdown-menuen i "Narrativ Støtte"-fanen med profiler.
     */
    function populateNarrativeProfileSelector(profiles) {
        const selectorContainer = document.getElementById('narrative-profile-selector-container');
        const selector = document.getElementById('narrative-profile-select');
        if (!selector || !selectorContainer) return;

        selector.innerHTML = '<option value="">-- Vælg en gemt profil --</option>'; // Nulstil
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

    /**
     * Viser de gemte profiler som en liste i "Logbog"-fanen med rediger- og slet-knapper.
     */
    function renderSavedProfilesForEditing(profiles) {
        const listContainer = document.getElementById('saved-profiles-list');
        if (!listContainer) return;
        listContainer.innerHTML = (profiles.length === 0) ? `<p style="text-align: center; font-style: italic; margin-top:10px;">Du har endnu ikke oprettet nogen profiler.</p>` : '';

        profiles.forEach(profile => {
            const profileElement = document.createElement('div');
            profileElement.className = 'logbook-entry-header';
            profileElement.style.marginBottom = '10px';
            profileElement.innerHTML = `
                <button type="button" class="logbook-accordion-toggle edit-profile-button" data-profile-id="${profile.id}">
                    <span class="logbook-title-container"><span class="logbook-title">${profile.name}</span><span class="logbook-subtitle">Alder: ${profile.age || 'N/A'}</span></span>
                    <span>Rediger ✏️</span>
                </button>
                <button type="button" class="delete-profile-button" title="Slet Profil" data-profile-id="${profile.id}">🗑️</button>`;
            listContainer.appendChild(profileElement);
        });
        attachProfileButtonListeners();
    }

   /** Udfylder en formular (enten profil eller narrativ) med data. */
    // INDSÆT DENNE NYE FUNKTION (f.eks. omkring linje 1075)

    /**
     * Udfylder profil-formularen med data fra et valgt profil-objekt.
     * @param {object} profileData - Objektet der indeholder den valgte profils data.
     */
    function populateFormWithProfileData(profileData) {
        const profileForm = document.getElementById('child-profile-form');
        if (!profileForm || !profileData) {
            console.error("Kunne ikke udfylde profilformular: Formular eller data mangler.");
            return;
        }

        // Nulstil formularen først for at fjerne gamle data
        profileForm.reset();
        document.querySelectorAll('.other-input').forEach(input => input.classList.add('hidden'));

        // Udfyld de simple felter
        document.getElementById('profile-id').value = profileData.id || '';
        document.getElementById('profile-name').value = profileData.name || '';
        document.getElementById('profile-age').value = profileData.age || '';

        // Funktion til at håndtere dynamiske lister (styrker, værdier, etc.)
        const populateList = (containerId, items, selectName, otherInputName) => {
            const container = document.getElementById(containerId);
            container.innerHTML = ''; // Ryd eksisterende felter

            if (!items || items.length === 0) {
                // Hvis der ingen items er, tilføj et enkelt tomt felt
                createFieldGroup(container, selectName.replace('profile_', ''), '', otherInputName);
                return;
            }

            items.forEach(itemValue => {
                createFieldGroup(container, selectName.replace('profile_', ''), itemValue, otherInputName);
            });
        };

        // Hjælpefunktion til at oprette et select-felt (genbrugt fra din fil)
        const createSelectWithOptions = (name, otherId, selectedValue) => {
            const select = document.createElement('select');
            select.name = name;
            select.className = 'dynamic-select';
            select.dataset.otherInputId = otherId;

            const options = {
                'profile_strength': ['Modig', 'Klog', 'Venlig', 'Kreativ', 'Tålmodig', 'Nysgerrig', 'Omsorgsfuld', 'Sjov', 'Stærk', 'Fantasifuld', 'Hjælpsom', 'Vedholdende'],
                'profile_value': ['Retfærdighed', 'Ærlighed', 'Empati', 'Samarbejde', 'Frihed', 'Loyalitet', 'Omsorg', 'At gøre sit bedste']
            };

            const optionList = options[name] || [];
            select.innerHTML = `<option value="">-- Vælg --</option>` + optionList.map(opt => `<option value="${opt}" ${selectedValue === opt ? 'selected' : ''}>${opt}</option>`).join('') + `<option value="other">Andet...</option>`;

            // Hvis den gemte værdi ikke er en standard-option, vælg "Andet..."
            if (selectedValue && !optionList.includes(selectedValue)) {
                select.value = 'other';
            }

            select.addEventListener('change', function() {
                const otherInput = document.getElementById(this.dataset.otherInputId);
                if(otherInput) {
                    otherInput.classList.toggle('hidden', this.value !== 'other');
                }
            });

            return select;
        };

        // Hjælpefunktion til at oprette en hel gruppe af felter (genbrugt fra din fil)
        const createFieldGroup = (container, type, value = '', relType = '') => {
            const newGroup = document.createElement('div');
            const uniqueId = `other-${type}-${Date.now()}-${Math.random()}`;

            if (type === 'strength' || type === 'value') {
                newGroup.className = 'input-group';
                const select = createSelectWithOptions(`profile_${type}`, uniqueId, value);
                newGroup.appendChild(select);

                const otherInput = document.createElement('input');
                otherInput.type = 'text';
                otherInput.name = `profile_${type}_other`;
                otherInput.id = uniqueId;
                otherInput.className = 'other-input';
                otherInput.placeholder = `Beskriv anden ${type}`;

                if (select.value === 'other') {
                    otherInput.value = value;
                } else {
                    otherInput.classList.add('hidden');
                }
                newGroup.appendChild(otherInput);

            } else if (type === 'relation') {
                newGroup.className = 'relation-group';
                newGroup.innerHTML = `<div class="input-pair"><input type="text" name="profile_relation_name" value="${value}" placeholder="Navn"></div><div class="input-pair"><input type="text" name="profile_relation_type" value="${relType}" placeholder="Relation"></div>`;
            } else {
                newGroup.className = 'input-group';
                newGroup.innerHTML = `<input type="text" name="profile_${type}" value="${value}" placeholder="Beskriv her...">`;
            }

            const removeButton = document.createElement('button');
            removeButton.type = 'button';
            removeButton.textContent = '-';
            removeButton.className = 'remove-button';
            removeButton.addEventListener('click', () => newGroup.remove());
            newGroup.appendChild(removeButton);

            container.appendChild(newGroup);
        };

        // Kald populateList for alle dynamiske felter
        populateList('profile-strengths-container', profileData.strengths, 'profile_strength');
        populateList('profile-values-container', profileData.values, 'profile_value');
        populateList('profile-motivations-container', profileData.motivations, 'profile_motivation');
        populateList('profile-reactions-container', profileData.reactions, 'profile_reaction');

        // Håndter relationer separat, da de har to felter
        const relationsContainer = document.getElementById('profile-relations-container');
        relationsContainer.innerHTML = '';
        const relations = profileData.relations.length > 0 ? profileData.relations : [{ name: '', type: '' }];
        relations.forEach(rel => createFieldGroup(relationsContainer, 'relation', rel.name, rel.type));
    }

  /** Opretter en komplet gruppe af felter (enten select+other, tekst eller relation) */
    function createFieldGroup(container, type, value = '', relType = '') {
        const newGroup = document.createElement('div');
        const uniqueId = `other-${type}-${Date.now()}-${Math.random()}`; // Unikt ID for "other" felt

        // Tjek om gruppen skal være for en select-dropdown
        if (type === 'strength' || type === 'value') {
            newGroup.className = 'input-group';
            const select = createSelectWithOptions(`profile_${type}`, uniqueId, value);
            newGroup.appendChild(select);

            const otherInput = document.createElement('input');
            otherInput.type = 'text';
            otherInput.name = `profile_${type}_other`;
            otherInput.id = uniqueId;
            otherInput.className = 'other-input';
            otherInput.placeholder = `Beskriv anden ${type}`;

            // Hvis den gemte værdi ikke findes i standard-options, vælg "Andet..." og vis værdien
            if (select.value === 'other') {
                otherInput.value = value;
            } else {
                otherInput.classList.add('hidden');
            }
            newGroup.appendChild(otherInput);

        } else if (type === 'relation') {
            newGroup.className = 'relation-group';
            newGroup.innerHTML = `<div class="input-pair"><input type="text" name="profile_relation_name" value="${value}" placeholder="Navn"></div><div class="input-pair"><input type="text" name="profile_relation_type" value="${relType}" placeholder="Relation"></div>`;
        } else { // 'motivation', 'reaction'
            newGroup.className = 'input-group';
            newGroup.innerHTML = `<input type="text" name="profile_${type}" value="${value}" placeholder="Beskriv her...">`;
        }

        // Tilføj en funktionel "Fjern"-knap til alle typer grupper
        const removeButton = document.createElement('button');
        removeButton.type = 'button';
        removeButton.textContent = '-';
        removeButton.className = 'remove-button';
        removeButton.addEventListener('click', () => newGroup.remove());
        newGroup.appendChild(removeButton);

        container.appendChild(newGroup);
    }

    /** Tilføjer listeners til rediger- og slet-knapper på den renderede profilliste */
    function attachProfileButtonListeners() {
        document.querySelectorAll('.edit-profile-button').forEach(button => {
            button.addEventListener('click', () => {
                const profileId = button.dataset.profileId;
                const profileData = allProfilesData.find(p => p.id == profileId);
                if (profileData) {
                    populateFormWithProfileData(profileData, 'profile');
                }
            });
        });

        document.querySelectorAll('.delete-profile-button').forEach(button => {
            button.addEventListener('click', async (e) => {
                e.stopPropagation();
                const profileId = button.dataset.profileId;
                const profile = allProfilesData.find(p => p.id == profileId);
                if (window.confirm(`Er du sikker på, du vil slette profilen for "${profile.name}"?`)) {
                    try {
                        await deleteChildProfileApi(profileId);
                        allProfilesData = allProfilesData.filter(p => p.id != profileId);
                        renderSavedProfilesForEditing(allProfilesData);
                        populateNarrativeProfileSelector(allProfilesData);
                    } catch (error) {
                        alert(`Fejl: ${error.message}`);
                    }
                }
            });
        });
    }

    /** Hoved-initialiseringsfunktion for hele featuren */
    function initializeProfileFeature() {
        const profileForm = document.getElementById('child-profile-form');
        if (!profileForm || profileForm.dataset.initialized === 'true') return;
        profileForm.dataset.initialized = 'true';

        const saveProfileButton = document.getElementById('save-profile-button');
        const clearProfileFormButton = document.getElementById('clear-profile-form-button');
        const profileSaveFeedback = document.getElementById('profile-save-feedback');

        // Hent og vis profiler
        listChildProfilesApi().then(profiles => {
            allProfilesData = profiles;
            renderSavedProfilesForEditing(profiles);
            populateNarrativeProfileSelector(profiles);
        }).catch(err => console.error("Kunne ikke hente profiler:", err));

        // Tilføj listeners til "Tilføj"-knapper i profil-formularen
        profileForm.querySelectorAll('.add-button').forEach(button => {
            button.addEventListener('click', function() {
                const container = document.getElementById(this.dataset.container);
                if (container) {
                    const isRelation = this.id.includes('relation');
                    createFieldGroup(container, `profile_${this.dataset.name}`, '', isRelation, '');
                }
            });
        });

        // Ryd formular
        clearProfileFormButton.addEventListener('click', () => {
            profileForm.reset();
            document.getElementById('profile-id').value = '';
            // Nulstil dynamiske felter til kun én tom række
            ['motivations', 'reactions', 'relations'].forEach(type => {
                const container = document.getElementById(`profile-${type}-container`);
                if(container) {
                    container.innerHTML = '';
                    createFieldGroup(container, `profile_${type}`, '', type==='relation');
                }
            });
            profileSaveFeedback.style.display = 'none';
        });



        // Gem/Opdater profil (FORM SUBMIT)
        profileForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            const saveButton = document.getElementById('save-profile-button');
            const profileSaveFeedback = document.getElementById('profile-save-feedback');
            saveButton.disabled = true;
            saveButton.textContent = 'Gemmer...';

            // Gem ID før kald, så vi ved om det er en opdatering
            const profileIdBeforeSave = document.getElementById('profile-id').value;

            // Indsamler data fra dropdowns for Styrker
            const strengths = [];
            document.querySelectorAll('#profile-strengths-container .input-group').forEach(group => {
                const select = group.querySelector('select[name="profile_strength"]');
                if (select.value === 'other') {
                    const otherInput = group.querySelector('input[name="profile_strength_other"]');
                    if (otherInput && otherInput.value.trim()) strengths.push(otherInput.value.trim());
                } else if (select.value) {
                    strengths.push(select.value);
                }
            });

            // Indsamler data fra dropdowns for Værdier
            const values = [];
            document.querySelectorAll('#profile-values-container .input-group').forEach(group => {
                const select = group.querySelector('select[name="profile_value"]');
                if (select.value === 'other') {
                    const otherInput = group.querySelector('input[name="profile_value_other"]');
                    if (otherInput && otherInput.value.trim()) values.push(otherInput.value.trim());
                } else if (select.value) {
                    values.push(select.value);
                }
            });

            const profileData = {
                id: document.getElementById('profile-id').value,
                name: document.getElementById('profile-name').value.trim(),
                age: document.getElementById('profile-age').value.trim(),
                strengths: strengths,
                values: values,
                motivations: Array.from(document.querySelectorAll('input[name="profile_motivation"]')).map(i => i.value.trim()).filter(Boolean),
                reactions: Array.from(document.querySelectorAll('input[name="profile_reaction"]')).map(i => i.value.trim()).filter(Boolean),
                relations: Array.from(document.querySelectorAll('#profile-relations-container .relation-group')).map(g => ({
                    name: g.querySelector('input[name="profile_relation_name"]').value.trim(),
                    type: g.querySelector('input[name="profile_relation_type"]').value.trim()
                })).filter(r => r.name || r.type)
            };

            try {
                const result = await saveChildProfileApi(profileData);
                profileSaveFeedback.textContent = result.message;
                profileSaveFeedback.className = 'flash-message flash-success';

                const updatedProfiles = await listChildProfilesApi();
                allProfilesData = updatedProfiles;
                renderSavedProfilesForEditing(updatedProfiles);
                populateNarrativeProfileSelector(updatedProfiles);

                if (profileIdBeforeSave) {
                    // DETTE VAR EN OPDATERING - gør intet for at rydde formen.
                    console.log(`Profil ${profileIdBeforeSave} opdateret.`);
                    // Sørg for at den korrekte profil er valgt og vist
                    const updatedProfileData = allProfilesData.find(p => p.id == profileIdBeforeSave);
                    if(updatedProfileData) {
                        populateFormWithProfileData(updatedProfileData);
                    }
                } else {
                    // DETTE VAR EN NY PROFIL - ryd formularen.
                    clearProfileFormButton.click();
                    console.log("Ny profil oprettet, formularen er ryddet.");
                }

            } catch (error) {
                profileSaveFeedback.textContent = `Fejl: ${error.message}`;
                profileSaveFeedback.className = 'flash-message flash-error';
            } finally {
                profileSaveFeedback.style.display = 'block';
                saveButton.disabled = false;
                saveButton.textContent = 'Gem Profil';
            }
        });

        // --- Håndter valg i Narrativ Støtte dropdown ---
        const narrativeProfileSelector = document.getElementById('narrative-profile-select');
        narrativeProfileSelector?.addEventListener('change', (event) => {
            const selectedProfileId = event.target.value;
            const selectedProfile = allProfilesData.find(p => p.id == selectedProfileId);

            // Funktion til at rydde/nulstille alle felter i den narrative formular
            const clearNarrativeForm = () => {
                document.getElementById('narrative-child-name-1').value = '';
                document.getElementById('narrative-child-age-1').value = '';

                // Nulstil 'styrker' dropdown og skjul 'andet' felt
                const strengthsSelect = document.getElementById('narrative-child-strengths-select');
                strengthsSelect.value = '';
                const strengthsOther = document.getElementById('narrative-child-strengths-other');
                strengthsOther.value = '';
                strengthsOther.classList.add('hidden');

                // Nulstil 'værdier' dropdown og skjul 'andet' felt
                const valuesSelect = document.getElementById('narrative-child-values-select');
                valuesSelect.value = '';
                const valuesOther = document.getElementById('narrative-child-values-other');
                valuesOther.value = '';
                valuesOther.classList.add('hidden');

                document.getElementById('narrative-child-motivation').value = '';
                document.getElementById('narrative-child-reaction').value = '';

                // Ryd og tilføj en enkelt tom relations-gruppe
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
                // Hvis brugeren vælger den tomme "-- Vælg en gemt profil --"
                clearNarrativeForm();
                return;
            }

            // -- UDFYLD FELTERNE MED DEN VALGTE PROFIL --

            // 1. Udfyld simple tekstfelter
            document.getElementById('narrative-child-name-1').value = selectedProfile.name || '';
            document.getElementById('narrative-child-age-1').value = selectedProfile.age || '';
            document.getElementById('narrative-child-motivation').value = (selectedProfile.motivations || []).join(', ');
            document.getElementById('narrative-child-reaction').value = (selectedProfile.reactions || []).join(', ');

            // 2. Håndter dropdowns med "Andet..."-mulighed (Styrker og Værdier)
            const populateSelectWithOther = (selectId, otherId, values) => {
                const selectElement = document.getElementById(selectId);
                const otherElement = document.getElementById(otherId);
                const options = Array.from(selectElement.options).map(opt => opt.value);

                // Tag kun den første værdi fra profilen til dette simple felt
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

            // 3. Håndter den dynamiske liste af relationer
            const relationsContainer = document.getElementById('narrative-relations-container');
            relationsContainer.innerHTML = ''; // Ryd eksisterende felter

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

                // Tilføj event listener til den nye remove-knap
                newGroup.querySelector('.remove-button').addEventListener('click', () => newGroup.remove());
                relationsContainer.appendChild(newGroup);
            });
        });
    }

    /**
     * Generisk funktion, der kan udfylde BÅDE profil-formularen og narrativ-formularen.
     */
    function populateProfileForm(profileData, formType = 'profile') {
        const p = (selector) => `${formType === 'profile' ? '#child-profile-form' : '#narrative-support-module'} ${selector}`;

        // Simple felter
        document.querySelector(p('input[name*="name"]')).value = profileData.name || '';
        document.querySelector(p('input[name*="age"]')).value = profileData.age || '';

        // Funktion til dynamisk at oprette og udfylde en liste af felter
        const populateList = (containerSelector, dataList, name) => {
            const container = document.querySelector(p(containerSelector));
            if (!container) return;
            container.innerHTML = ''; // Ryd eksisterende dynamiske felter

            const items = dataList && dataList.length > 0 ? dataList : ['']; // Sørg for mindst ét tomt felt
            items.forEach(itemValue => {
                const newGroup = document.createElement('div');
                if (name === 'relation') {
                    newGroup.className = 'relation-group';
                    newGroup.innerHTML = `
                        <div class="input-pair"><input type="text" name="${formType}_relation_name" value="${itemValue.name || ''}"></div>
                        <div class="input-pair"><input type="text" name="${formType}_relation_type" value="${itemValue.type || ''}"></div>
                        <button type="button" class="remove-button">-</button>`;
                } else {
                    newGroup.className = 'input-group';
                    newGroup.innerHTML = `<input type="text" name="${formType}_${name}" value="${itemValue || ''}"><button type="button" class="remove-button">-</button>`;
                }
                newGroup.querySelector('.remove-button').addEventListener('click', () => newGroup.remove());
                container.appendChild(newGroup);
            });
        };

        // Udfyld alle lister
        populateList('#profile-strengths-container, #narrative-child-strengths-other-container', profileData.strengths, 'strength');
        populateList('#profile-values-container, #narrative-child-values-other-container', profileData.values, 'value');
        populateList('#profile-motivations-container, #narrative-child-motivation-container', profileData.motivations, 'motivation');
        populateList('#profile-reactions-container, #narrative-child-reaction-container', profileData.reactions, 'reaction');
        populateList('#profile-relations-container, #narrative-relations-container', profileData.relations, 'relation');

        // Note: Denne simple version udfylder ikke dropdowns, men indsætter værdien i tekstfelter.
        // Dette er en midlertidig, men funktionel løsning for at få det til at virke.
        // En fuld løsning ville kræve mere kompleks logik til at matche værdier med dropdown-options.
        // For nu fokuserer vi på tekstinput-delen.
        if (formType === 'narrative') {
             const motivationInput = document.getElementById('narrative-child-motivation');
             const reactionTextarea = document.getElementById('narrative-child-reaction');
             if(motivationInput) motivationInput.value = (profileData.motivations || []).join(', ');
             if(reactionTextarea) reactionTextarea.value = (profileData.reactions || []).join(', ');
        }
    }



    // Kald funktionen for at sætte alle listeners. Vi vil kalde den fra `handleTabClick`
    // for at sikre, at den kun kører, når fanen er aktiv.
    // ===================================================================
    // SLUT: KOMPLET LOGIK FOR BØRNEPROFILER
    // ===================================================================

// --- FORBEDRET: Logik til at vise/skjule Godnatsange sektionen ---
    const sangteksterSektion = document.getElementById('sangtekster-sektion');

    // En funktion, der kan genbruges, til at tjekke switchen og opdatere synligheden
    function updateSongSectionVisibility() {
        if (!bedtimeStorySwitch || !sangteksterSektion) return; // Sikkerhedstjek

        if (bedtimeStorySwitch.checked) {
            sangteksterSektion.classList.remove('hidden');
        } else {
            sangteksterSektion.classList.add('hidden');
        }
    }

    // Tilføj en event listener, der kalder funktionen, HVER GANG switchen ændres
    if (bedtimeStorySwitch) {
        bedtimeStorySwitch.addEventListener('change', updateSongSectionVisibility);
    }

    // KALD FUNKTIONEN ÉN GANG MED DET SAMME, NÅR SIDEN LOADER:
    // Dette er den vigtige linje, der sikrer, at sektionen er skjult fra start.
    updateSongSectionVisibility();

// ===================================================================
// START: FUNKTIONER TIL LÆSEHESTEN MODUL
// ===================================================================

function initializeLaesehestenModule() {
    console.log("Initializing Læsehesten Module...");
    const laesehestenSection = document.getElementById('laesehesten-module');
    if (!laesehestenSection) {
        console.log("Læsehesten module section not found, skipping initialization.");
        return;
    }
    fetchLaesehestDataAndRender();
    setupLaesehestEventListeners();
    console.log("Læsehesten Module Initialized.");
}

async function fetchLaesehestDataAndRender() {
    try {
        const response = await fetch('/static/laesehest_data.json');
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const data = await response.json();
        renderAccordion(data.categories);
    } catch (error) {
        console.error("Failed to load laesehest_data.json:", error);
        const container = document.getElementById('laesehesten-accordion-container');
        if (container) container.innerHTML = '<p style="color: red;">Fejl: Kunne ikke indlæse element-listerne.</p>';
    }
}

function renderAccordion(categories) {
    const container = document.getElementById('laesehesten-accordion-container');
    if (!container) return;
    container.innerHTML = categories.map(category => `
        <div class="accordion-item" data-category-id="${category.id}">
            <button type="button" class="accordion-header">
                <span>${category.name}</span>
                <span class="accordion-arrow">◀</span>
            </button>
            <div class="accordion-content hidden">
                <div class="element-checklist-container">
                    ${renderChecklistForCategory(category)}
                </div>
            </div>
        </div>
    `).join('');
    container.querySelectorAll('.accordion-header').forEach(header => {
        header.addEventListener('click', () => {
            header.classList.toggle('open');
            header.nextElementSibling.classList.toggle('hidden');
        });
    });
}

function renderChecklistForCategory(category) {
    return category.items.map(item => `
        <div class="element-item" data-complexity="${item.complexity}">
            <input type="checkbox" id="element-${item.id}" name="laesehest_element" value="${item.value}">
            <label for="element-${item.id}" class="element-label">
                <span class="element-emoji">${item.emoji}</span>
                <span class="element-name">${item.name}</span>
                <span class="element-complexity" title="Sværhedsgrad ${item.complexity} af 3">
                    ${'●'.repeat(item.complexity)}${'○'.repeat(3 - item.complexity)}
                </span>
            </label>
        </div>
    `).join('');
}

function setupLaesehestEventListeners() {
    const lixSlider = document.getElementById('lix-slider');
    const lixValueDisplay = document.getElementById('lix-value-display');
    const lixDescription = document.getElementById('lix-description');
    if (lixSlider && lixValueDisplay && lixDescription) {
        const updateLixDescription = (value) => {
            const val = parseInt(value, 10);
            if (val <= 19) return "Perfekt til de helt nye læsere (ca. 6-7 år).";
            if (val <= 29) return "Godt for barnet, der har knækket læsekoden (ca. 8-9 år).";
            if (val <= 39) return "Udfordrende for den sikre læser (ca. 10-11 år).";
            if (val <= 49) return "For den meget erfarne læser (ca. 12+ år).";
            return "Meget svær tekst, svarer til faglitteratur for voksne.";
        };
        lixSlider.addEventListener('input', () => {
            lixValueDisplay.textContent = lixSlider.value;
            lixDescription.textContent = updateLixDescription(lixSlider.value);
        });
        lixDescription.textContent = updateLixDescription(lixSlider.value);
    }

    const sortButtons = document.querySelectorAll('.sort-button');
    sortButtons.forEach(button => {
        button.addEventListener('click', () => {
            const sortBy = button.dataset.sort;
            sortButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            document.querySelectorAll('#laesehesten-accordion-container .element-item').forEach(item => {
                item.style.display = (sortBy === 'all' || item.dataset.complexity === sortBy) ? 'block' : 'none';
            });
        });
    });

    const addWordButton = document.getElementById('laesehest-add-word-button');
    if (addWordButton) {
        addWordButton.addEventListener('click', () => {
            const container = document.getElementById('laesehest-custom-words-container');
            const newGroup = document.createElement('div');
            newGroup.className = 'input-group';
            newGroup.innerHTML = `
                <input type="text" name="laesehest_custom_word" placeholder="f.eks. farmor, Buster...">
                <button type="button" class="remove-button">-</button>
            `;
            newGroup.querySelector('.remove-button').addEventListener('click', () => newGroup.remove());
            container.appendChild(newGroup);
        });
    }

    const generateButton = document.getElementById('generate-laesehest-button');
    if (generateButton) {
        generateButton.addEventListener('click', handleLaesehestGenerateClick);
    }
}

// I static/script.js

// ERSTAT HELE DIN GAMLE FUNKTION MED DENNE KORREKTE VERSION

async function handleLaesehestGenerateClick() {
    const generateButton = document.getElementById('generate-laesehest-button');
    if (!generateButton || generateButton.disabled) return;

    const originalButtonText = generateButton.textContent;

    // UI Håndtering for loading
    generateButton.disabled = true;
    generateButton.textContent = 'Skaber 3 historier...';

    const historieOutputSection = document.getElementById('historie-output');
    const storyDisplayContainer = document.getElementById('story-display');
    const storySectionHeading = document.getElementById('story-section-heading');
    const storyShareButtons = document.getElementById('story-share-buttons');
    const quizSektion = document.getElementById('quiz-sektion'); // Sørg for at hente reference til quiz sektion

    if (historieOutputSection) historieOutputSection.classList.remove('hidden');
    if (storySectionHeading) storySectionHeading.textContent = "Venter på historier...";
    if (storyDisplayContainer) {
        storyDisplayContainer.innerHTML = `
            <div id="story-loading-indicator">
                <p>Genererer 3 historie-forslag... Dette kan tage lidt tid.</p>
                <span class="spinner"></span>
            </div>`;
    }
    if (storyShareButtons) storyShareButtons.classList.add('hidden');
    if (quizSektion) quizSektion.classList.add('hidden'); // Skjul også quizzen fra start

    // Dataindsamling
    const dataToSend = {
        target_lix: parseInt(document.getElementById('lix-slider').value, 10),
        elements: Array.from(document.querySelectorAll('input[name="laesehest_element"]:checked')).map(el => el.value),
        custom_words: Array.from(document.querySelectorAll('input[name="laesehest_custom_word"]')).map(el => el.value.trim()).filter(Boolean),
        focus_letter: document.getElementById('laesehest-focus-letter').value.trim(),
        plot: document.getElementById('laesehest-plot').value.trim(),
        negative_prompt: document.getElementById('laesehest-negative-prompt').value.trim(),
        laengde: document.getElementById('laesehest-laengde-select').value,
        mood: document.getElementById('laesehest-mood-select').value,
    };

    try {
        const result = await generateLixStoryApi(dataToSend);
        if (result.error) throw new Error(result.error);

        trackGAEvent('generate_lix_story', 'Læsehesten', `Target LIX: ${dataToSend.target_lix}`, dataToSend.target_lix);

        if (storyDisplayContainer) storyDisplayContainer.innerHTML = ''; // Ryd loading-indikator

        if (result.stories && Array.isArray(result.stories) && result.stories.length > 0) {
            if (storySectionHeading) storySectionHeading.textContent = "Vælg din favorithistorie:";

            const accordionContainer = document.createElement('div');

            result.stories.forEach(variant => {
                const itemDiv = document.createElement('div');
                itemDiv.className = 'accordion-item';

                const headerButton = document.createElement('button');
                headerButton.type = 'button';
                headerButton.className = 'accordion-header';
                headerButton.innerHTML = `<span>${variant.title} <span class="final-lix-tag" title="Læsbarheds-score">LIX: ${variant.lix_score}</span></span><span class="accordion-arrow">◀</span>`;

                const contentDiv = document.createElement('div');
                contentDiv.className = 'accordion-content hidden';

                const storyParagraph = document.createElement('p');
                storyParagraph.textContent = variant.content;
                storyParagraph.style.whiteSpace = 'pre-wrap';
                storyParagraph.style.marginBottom = '20px';

                const selectButton = document.createElement('button');
                selectButton.type = 'button';
                selectButton.className = 'utility-button';
                selectButton.textContent = 'Vælg denne historie';

                contentDiv.append(storyParagraph, selectButton);

                headerButton.addEventListener('click', () => {
                    headerButton.classList.toggle('open');
                    contentDiv.classList.toggle('hidden');
                });

                // --- HER ER DEN KORREKTE, RENE EVENT LISTENER TIL "VÆLG"-KNAPPEN ---
                selectButton.addEventListener('click', () => {
                    const currentDisplay = document.getElementById('story-display');
                    const currentHeading = document.getElementById('story-section-heading');
                    const currentShareButtons = document.getElementById('story-share-buttons');

                    if (currentDisplay) currentDisplay.innerHTML = '';
                    if (currentHeading) currentHeading.innerHTML = `${variant.title} <span class="final-lix-tag" title="Læsbarheds-score">LIX: ${variant.lix_score}</span>`;

                    const storyContentDiv = document.createElement('div');
                    storyContentDiv.id = 'story-text-content';
                    storyContentDiv.textContent = variant.content;

                    if (currentDisplay) currentDisplay.appendChild(storyContentDiv);
                    if (currentShareButtons) currentShareButtons.classList.remove('hidden');

                    if(quizSektion) quizSektion.classList.add('hidden');

                    const imageButton = document.querySelector('#story-share-buttons #generate-image-from-output-button');
                    if(imageButton) {
                        imageButton.disabled = true;
                        imageButton.title = "Svar rigtigt på quizzen for at låse op";
                    }

                    const userRole = document.getElementById('current-user-role-data')?.dataset.role || 'guest';
                    if (userRole !== 'guest') {
                        document.querySelectorAll('#read-aloud-button, #save-to-logbook-button').forEach(btn => {
                            btn.disabled = false;
                            btn.removeAttribute('title');
                        });
                    }

                    fetchAndDisplayQuiz(variant.content, variant.lix_score);
                });
                // --- SLUT PÅ DEN KORREKTE EVENT LISTENER ---

                itemDiv.append(headerButton, contentDiv);
                accordionContainer.appendChild(itemDiv);
            });

            storyDisplayContainer.appendChild(accordionContainer);

        } else {
             throw new Error("Modtog ingen historie-varianter fra serveren.");
        }

    } catch (error) {
        console.error("Error in handleLaesehestGenerateClick:", error);
        if (storyDisplayContainer) storyDisplayContainer.innerHTML = `<p style="color: red; text-align: center;">Ups! Noget gik galt: ${error.message}.</p>`;
        if (storySectionHeading) storySectionHeading.textContent = "Fejl ved generering";
    } finally {
        if (generateButton) {
            generateButton.disabled = false;
            generateButton.textContent = originalButtonText;
        }
    }
}
// ===================================================================
// SLUT: FUNKTIONER TIL LÆSEHESTEN MODUL
// ===================================================================


    // === START: Logbog Dokumentations-Workflow ===

    const logbookSection = document.getElementById('logbook-documentation-section');
    const logbookLoader = document.getElementById('logbook-analysis-loader');
    const logbookError = document.getElementById('logbook-analysis-error');
    const logbookForm = document.getElementById('logbook-entry-form');

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

            // --- OPDATERET LOGIK FOR AT NULSTILLE "GEM"-KNAPPEN ---
            const saveButton = document.getElementById('save-logbook-entry-button');
            if (saveButton) {
                saveButton.disabled = false;
                saveButton.classList.remove('disabled-button'); // Fjerner "grå" stil
                saveButton.textContent = 'Gem Historien i Logbog';
                saveButton.style.backgroundColor = ''; // Nulstiller farven til default
            }
        }
    }

// Denne funktion udfylder selve formularen
function populateLogbookForm(storyId, data) {
    const storyIdField = document.getElementById('logbook-story-id');
    if(storyIdField) storyIdField.value = storyId;

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

    // Udfyld alle felter med data fra AI-analysen
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

    // RETTELSE: Logik til at finde og vise containeren for "Original Historie".
    const originalStoryContainer = document.getElementById('logbook-original-story-container');
    const originalStoryTitleField = document.getElementById('logbook-original-story-title');

    if (originalStoryContainer && originalStoryTitleField && data.root_story_title) {
        // Hvis der er data, indsæt titlen og vis containeren
        originalStoryTitleField.value = data.root_story_title;
        originalStoryContainer.style.display = 'block';
    } else if (originalStoryContainer) {
        // Hvis der ikke er data, sørg for at containeren er skjult
        originalStoryContainer.style.display = 'none';
    }
}

    // Tilføj event listeners til progress sliders
    document.querySelectorAll('.progress-slider input[type="range"]').forEach(slider => {
        const valueSpan = slider.nextElementSibling;
        if(valueSpan && valueSpan.classList.contains('range-value')) {
            // Sæt initial værdi
            valueSpan.textContent = slider.value;
            // Opdater ved ændring
            slider.addEventListener('input', () => {
                valueSpan.textContent = slider.value;
            });
        }
    });

// Event listener for "Gem i logbog" knappen
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
            console.log(`[DEBUG] Forsøger at gemme logbog for story_id: '${storyId}'. Fuld data:`, dataToSave);
            console.log("Logbog: Sender data til server for at gemme:", dataToSave);

            try {
                const result = await saveLogbookEntryApi(storyId, dataToSave);
                console.log("Server svar efter gem:", result);

                if (result.success) {
                    trackGAEvent('save_to_logbook', 'Narrativ Støtte', `Story ID: ${storyId}`, null);
                }

                // Opdater UI for at vise succes
                saveButton.textContent = 'Gemt i Logbog!';
                saveButton.style.backgroundColor = '#28a745'; // Grøn succesfarve
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

    // RETTELSE: Funktionen accepterer nu 'rootStoryTitle' som en tredje parameter.
async function triggerLogbookAnalysis(storyId, storyContent, rootStoryTitle) {
    console.log("Logbog: Starter analyse for story ID:", storyId);
    resetLogbookSection();

    if (!logbookSection || !logbookLoader || !logbookError || !logbookForm) {
        console.error("Logbog: Kritiske HTML-elementer til dokumentation mangler.");
        return;
    }

    logbookSection.classList.remove('hidden');
    logbookLoader.classList.remove('hidden');

    try {
        const analysisData = await analyzeStoryForLogbookApi(storyContent);
        console.log("Logbog: Analyse modtaget fra API:", analysisData);

        if (analysisData.error) {
            throw new Error(analysisData.error);
        }

        // RETTELSE: Hvis 'rootStoryTitle' blev modtaget, føjes den til de data, der skal vises i formularen.
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

    // ==========================================================
    // START PÅ NY FUNKTION
    // ==========================================================
    async function triggerAndDisplayReflectionQuestions(storyTitle, storyContent, narrativeBrief, originalInputs) {
        const reflectionSection = document.getElementById('narrative-reflection-section');
        const questionList = document.getElementById('narrative-reflection-questions-list');

        if (!reflectionSection || !questionList) {
            console.error("Elementer til refleksionsspørgsmål ikke fundet.");
            return;
        }

        // Gør sektionen klar og vis en "loader"
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

    // === Funktion til at Indsamle Data fra Narrativ Støtte Inputfelter (Samlet og korrigeret version) ===
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
            if (name || type) { // Gem kun hvis mindst et felt er udfyldt
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

    console.log("Collected All Narrative Data:", data);
    return data;
}

    // === SLUT: Logbog Dokumentations-Workflow ===idste afsluttende parentes og semikolon for DOMContentLoaded.

    // === START: Genanvendelses-flow (Fortsæt Historie) ===

    const continueStorySwitch = document.getElementById('continue-story-switch');
    const continuationOptions = document.getElementById('continuation-options');
    const parentStorySelect = document.getElementById('parent-story-select');
    const strategySelection = document.getElementById('continuation-strategy-selection');

    if (continueStorySwitch) {
        continueStorySwitch.addEventListener('change', async () => {
            if (continueStorySwitch.checked) {
                // Vis sektionen og dropdown-menuen
                continuationOptions.classList.remove('hidden');
                parentStorySelect.innerHTML = '<option value="">Henter historier...</option>';
                parentStorySelect.disabled = true;
                strategySelection.classList.add('hidden'); // Skjul strategi-knapper

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
                // Skjul og nulstil sektionen, hvis switchen slås fra
                continuationOptions.classList.add('hidden');
                strategySelection.classList.add('hidden');
                parentStorySelect.innerHTML = '<option value="">-- Henter Historier... --</option>';
            }
        });
    }

    if (parentStorySelect) {
        parentStorySelect.addEventListener('change', () => {
            // Vis strategi-knapperne, når en historie er valgt
            if (parentStorySelect.value) {
                strategySelection.classList.remove('hidden');
            } else {
                strategySelection.classList.add('hidden');
            }
        });
    }

    const strategyButtons = document.querySelectorAll('[name="continuation_strategy"]');

    // Funktion til at håndtere klik på en strategi-knap
    const handleStrategyClick = (event) => {
        const strategy = event.target.value; // 'deepen' or 'generalize'
        const parentStoryId = parentStorySelect.value;

        if (!parentStoryId) {
            alert("Vælg venligst en historie fra listen først.");
            return;
        }

        console.log(`Strategi valgt: ${strategy}, Forælder ID: ${parentStoryId}`);

        // Deaktiver alle historie-genereringsknapper
        if(narrativeGenerateStoryButton) narrativeGenerateStoryButton.disabled = true;
        strategyButtons.forEach(btn => btn.disabled = true);

        // Kald den eksisterende funktion til at generere historier, men send de nye data med
        // Vi samler de andre data fra formularen, præcis som før
        const narrativeData = collectNarrativeData();

        // Tilføj de nye oplysninger til det data-objekt, vi sender
        narrativeData.parent_story_id = parentStoryId;
        narrativeData.continuation_strategy = strategy;

        // Nu kalder vi den oprindelige 'handleNarrativeGenerateClick' funktion,
        // men giver den vores nye, udvidede data.
        // Vi omdøber funktionen for klarhedens skyld.
        executeNarrativeGeneration(narrativeData);
    };

    strategyButtons.forEach(button => {
        button.addEventListener('click', handleStrategyClick);
    });

// Denne funktion starter hele processen, når en narrativ historie genereres
async function executeNarrativeGeneration(dataToSend) {
    console.log("executeNarrativeGeneration: Starter med data:", dataToSend);
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
        console.log("Svar modtaget fra server:", result);
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
            // RETTELSE: `result.root_story_title` sendes nu med til næste funktion.
            triggerLogbookAnalysis(result.story_id, result.story, result.root_story_title);
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
    initializeProfileFeature();
});

// Slut på DOMContentLoaded listener
