// Fil: static/script.js
import { generateStoryApi, generateImageApi, suggestCharacterTraitsApi, generateNarrativeStoryApi, getGuidingQuestionsApi, generateAudioApi, generateLixStoryApi } from './modules/api_client.js';

// Kør først koden, når hele HTML dokumentet er færdigindlæst og klar
document.addEventListener('DOMContentLoaded', () => {
    console.log("DOMContentLoaded event fired. Initializing Read Me A Story script.");

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
const storyLoadingIndicator = document.getElementById('story-loading-indicator');

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
    const imageSection = document.getElementById('billede-til-historien-sektion');
    const imageLoadingIndicator = document.getElementById('image-loading-indicator');
    const storyImageDisplay = document.getElementById('story-image-display');
    const imageGenerationError = document.getElementById('image-generation-error');
    const storyDisplay = document.getElementById('story-display');
    const storySectionHeading = document.getElementById('story-section-heading'); // Til opdatering af historietitel
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
    // resetButton er allerede defineret, men er en del af denne container nu.

    // --- NYT: Sangtekst Sektion Elementer ---
    const sangDropdown = document.getElementById('sang-dropdown');
    const sangtekstTitel = document.getElementById('sangtekst-titel'); // Overskriften for sangteksten
    const sangtekstVisning = document.getElementById('sangtekst-visning'); // Hvor selve teksten vises
    let allSongsData = []; // Global variabel til at gemme sangdata

    // === Referencer for Narrativ Støtte Modul ===
    const narrativeFocusInput = document.getElementById('narrative-focus-input');
    const narrativeGoalInput = document.getElementById('narrative-goal-input');
    const narrativeChildNameInput = document.getElementById('narrative-child-name-1'); // Antager det første barns navn
    const narrativeChildAgeInput = document.getElementById('narrative-child-age-1');   // Antager det første barns alder
    const narrativeChildStrengthsSelect = document.getElementById('narrative-child-strengths-select');
    const narrativeChildStrengthsOther = document.getElementById('narrative-child-strengths-other');
    const narrativeChildValuesSelect = document.getElementById('narrative-child-values-select');
    const narrativeChildValuesOther = document.getElementById('narrative-child-values-other');
    const narrativeChildMotivationInput = document.getElementById('narrative-child-motivation');
    const narrativeChildReactionTextarea = document.getElementById('narrative-child-reaction');

    // NYT: Felter for Problem-Karakter
    const narrativeProblemIdentityNameInput = document.getElementById('narrative-problem-identity-name');
    const narrativeProblemRoleFunctionInput = document.getElementById('narrative-problem-role-function');
    const narrativeProblemPurposeIntentionInput = document.getElementById('narrative-problem-purpose-intention');
    const narrativeProblemBehaviorActionInput = document.getElementById('narrative-problem-behavior-action');
    const narrativeProblemInfluenceInput = document.getElementById('narrative-problem-influence');

    // Tilføjelse af main characters, places, plot for narrative
    const narrativeMainCharactersContainer = document.getElementById('narrative-main-characters-container');
    const narrativePlacesContainer = document.getElementById('narrative-places-container');
    const narrativePlotContainer = document.getElementById('narrative-plot-container');
    const narrativeNegativePromptInput = document.getElementById('narrative-negative-prompt-input');
    const narrativeLengthSelect = document.getElementById('narrative-length-select');
    const narrativeMoodSelect = document.getElementById('narrative-mood-select');
    const narrativeSuggestTraitsButton = document.getElementById('narrative-suggest-traits-button');
    const narrativeGenerateStoryButton = document.getElementById('narrative-generate-story-button');
    const narrativeStoryOutputDiv = document.getElementById('narrative-story-output'); // Hvor den narrative historie skal vises
    // Output elementer for Narrativ Støtte
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

    // === NYT: Fane Navigation Funktionalitet ===
    const tabButtons = document.querySelectorAll('.tab-button');
    const contentSections = document.querySelectorAll('.content-section');

    if (tabButtons.length > 0 && contentSections.length > 0) {
    const historieOutput = document.getElementById('historie-output');

    const handleTabClick = (button) => {
        tabButtons.forEach(btn => btn.classList.remove('active'));
        contentSections.forEach(section => section.classList.add('hidden'));

        button.classList.add('active');
        const targetId = button.dataset.tabTarget;
        const targetSection = document.querySelector(targetId);
        if (targetSection) {
            targetSection.classList.remove('hidden');
        }

        // Styr synlighed af den delte output sektion
        if (targetId === '#generator' || targetId === '#laesehesten-module') {
            if (historieOutput) historieOutput.classList.remove('hidden');
        } else {
            if (historieOutput) historieOutput.classList.add('hidden');
        }
    };

    tabButtons.forEach(button => {
        button.addEventListener('click', () => handleTabClick(button));
    });

    // Sørg for at den korrekte tilstand er sat ved sideindlæsning
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

// === Funktion til at Indsamle Data fra Narrativ Støtte Inputfelter ===
    function collectNarrativeData() {
        const narrativeData = {};

        // 1. Centrale Narrative Input
        if (narrativeFocusInput) narrativeData.narrative_focus = narrativeFocusInput.value.trim();
        if (narrativeGoalInput) narrativeData.story_goal = narrativeGoalInput.value.trim();

        // 2. Information om Barnet
        if (narrativeChildNameInput) narrativeData.child_name = narrativeChildNameInput.value.trim();
        if (narrativeChildAgeInput) narrativeData.child_age = narrativeChildAgeInput.value.trim();

        if (narrativeChildStrengthsSelect) {
            if (narrativeChildStrengthsSelect.value === 'other' && narrativeChildStrengthsOther) {
                narrativeData.child_strengths = narrativeChildStrengthsOther.value.trim() ? [narrativeChildStrengthsOther.value.trim()] : [];
            } else if (narrativeChildStrengthsSelect.value) {
                narrativeData.child_strengths = [narrativeChildStrengthsSelect.value];
            } else {
                narrativeData.child_strengths = [];
            }
        }

        if (narrativeChildValuesSelect) {
            if (narrativeChildValuesSelect.value === 'other' && narrativeChildValuesOther) {
                narrativeData.child_values = narrativeChildValuesOther.value.trim() ? [narrativeChildValuesOther.value.trim()] : [];
            } else if (narrativeChildValuesSelect.value) {
                narrativeData.child_values = [narrativeChildValuesSelect.value];
            } else {
                narrativeData.child_values = [];
            }
        }

        if (narrativeChildMotivationInput) narrativeData.child_motivation = narrativeChildMotivationInput.value.trim();
        if (narrativeChildReactionTextarea) narrativeData.child_typical_reaction = narrativeChildReactionTextarea.value.trim();

        // Vigtige Relationer
        narrativeData.important_relations = [];
        if (narrativeRelationsContainer) {
            narrativeRelationsContainer.querySelectorAll('.relation-group').forEach(group => {
                const nameInput = group.querySelector('input[name="narrative_relation_name"]');
                const typeInput = group.querySelector('input[name="narrative_relation_type"]');
                const name = nameInput ? nameInput.value.trim() : '';
                const type = typeInput ? typeInput.value.trim() : '';
                if (name || type) { // Gem kun hvis mindst et felt er udfyldt
                    narrativeData.important_relations.push({ name: name, type: type });
                }
            });
        }

        // 3. Generelle Historieelementer (Narrativ Støtte sektion)
        narrativeData.main_characters = [];
        if (narrativeMainCharactersContainer) {
            narrativeMainCharactersContainer.querySelectorAll('.character-group').forEach(group => {
                const descInput = group.querySelector('input[name="narrative_main_char_desc"]');
                const nameInput = group.querySelector('input[name="narrative_main_char_name"]');
                const description = descInput ? descInput.value.trim() : '';
                const name = nameInput ? nameInput.value.trim() : '';
                if (description || name) {
                    narrativeData.main_characters.push({ description: description, name: name });
                }
            });
        }

        narrativeData.places = [];
        if (narrativePlacesContainer) {
            narrativePlacesContainer.querySelectorAll('.input-group input[name="narrative_place"]').forEach(input => {
                const value = input.value.trim();
                if (value) narrativeData.places.push(value);
            });
        }

        narrativeData.plot_elements = [];
        if (narrativePlotContainer) {
            narrativePlotContainer.querySelectorAll('.input-group input[name="narrative_plot"]').forEach(input => {
                const value = input.value.trim();
                if (value) narrativeData.plot_elements.push(value);
            });
        }

        if (narrativeNegativePromptInput) narrativeData.negative_prompt = narrativeNegativePromptInput.value.trim();
        if (narrativeLengthSelect) narrativeData.length = narrativeLengthSelect.value;
        if (narrativeMoodSelect) narrativeData.mood = narrativeMoodSelect.value;

        console.log("Collected Narrative Data:", narrativeData);
        return narrativeData;
    }


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

    // --- Dataindsamling (uændret) ---
    const karakterer = [];
    if(karakterContainer) { karakterContainer.querySelectorAll('.character-group').forEach(group => { const descInput = group.querySelector('input[name="karakter_desc"]'); const nameInput = group.querySelector('input[name="karakter_navn"]'); const description = descInput ? descInput.value.trim() : ''; const name = nameInput ? nameInput.value.trim() : ''; if (description) { karakterer.push({ description: description, name: name }); } }); }
    const steder = []; document.querySelectorAll('#sted-container .input-group input[name="sted"]').forEach(input => { const v = input.value.trim(); if(v) steder.push(v); });
    const plots = []; document.querySelectorAll('#plot-container .input-group input[name="plot"]').forEach(input => { const v = input.value.trim(); if(v) plots.push(v); });
    const listeners = [];
    if(listenerContainer) { listenerContainer.querySelectorAll('.listener-group').forEach(group => { const nameInput = group.querySelector('input[name="listener_name_single"]'); const ageInput = group.querySelector('input[name="listener_age_single"]'); const name = nameInput ? nameInput.value.trim() : ''; const age = ageInput ? ageInput.value.trim() : ''; if (name || age) { listeners.push({ name: name, age: age }); } }); }
    const selectedLaengde = laengdeSelect ? laengdeSelect.value : 'kort';
    const selectedMoodValue = moodSelect ? moodSelect.value : 'neutral';
    const isInteractive = interactiveStorySwitch ? interactiveStorySwitch.checked : false;
    const isBedtimeStory = bedtimeStorySwitch ? bedtimeStorySwitch.checked : false;
    const negativePromptText = negativePromptInput ? negativePromptInput.value.trim() : '';
    let selectedModel = 'gemini-1.5-flash-latest';
    if (aiModelSwitch && !aiModelSwitch.disabled && aiModelSwitch.checked) {
        selectedModel = 'gemini-2.5-pro-preview-05-06';
    }
    saveCurrentListeners();
    const dataToSend = { karakterer, steder, plots, laengde: selectedLaengde, mood: selectedMoodValue, listeners, interactive: isInteractive, is_bedtime_story: isBedtimeStory, negative_prompt: negativePromptText, selected_model: selectedModel };

    // --- UI Opdatering: Loading State ---
    if(generateButton) { generateButton.disabled = true; generateButton.textContent = 'Laver historie...'; }

    // ==================================================================
    // ### NY AGGRESSIV OP RYDNING ###
    // Vi bruger .innerHTML = '' til at slette ALT indhold (både tekst og skjulte elementer)
    // fra historie-boksen, før vi starter.
    if(storyDisplay) {
        storyDisplay.innerHTML = '';
    }
    // ==================================================================

    // Vis loading-indikatoren ved at tilføje den til den (nu tomme) boks
    if(storyLoadingIndicator) storyDisplay.appendChild(storyLoadingIndicator);
    if(storyLoadingIndicator) storyLoadingIndicator.classList.remove('hidden');

    if(storySectionHeading) storySectionHeading.textContent = 'Jeres historie';
    if (storyShareButtonsContainer) storyShareButtonsContainer.classList.add('hidden');
    if(audioPlayer) { audioPlayer.classList.add('hidden'); audioPlayer.pause(); audioPlayer.src = ''; }
    if (generateImageButtons.length > 0) generateImageButtons.forEach(button => button.disabled = true);

    try {
        const result = await generateStoryApi(dataToSend);

        // Rens både titel og historie for en sikkerheds skyld
        const cleanTitle = (result.title || "Jeres historie").trim();
        const cleanStory = (result.story || "Modtog en tom historie fra serveren.").replace(/^\s+/, '');

        // ==================================================================
        // ### NY INDSÆTTELSE AF INDHOLD ###
        // Igen, slet ALT i boksen først for at være helt sikker
        if(storyDisplay) {
            storyDisplay.innerHTML = '';
        }
        // Tilføj den nye, rene tekst
        if(storyTextContent) {
            storyTextContent.textContent = cleanStory;
            storyDisplay.appendChild(storyTextContent);
        }
        // ==================================================================

        if(storySectionHeading) storySectionHeading.textContent = cleanTitle;

        if (storyShareButtonsContainer && cleanStory) {
            storyShareButtonsContainer.classList.remove('hidden');
            const resetButton = storyShareButtonsContainer.querySelector('#reset-button');
            if(resetButton) resetButton.style.display = 'inline-block';
        }
        if (generateImageButtons.length > 0 && cleanStory) {
            generateImageButtons.forEach(button => { button.disabled = false; button.removeAttribute('title'); });
        }

    } catch (error) {
         if(storyDisplay) {
            storyDisplay.innerHTML = `<p style="color: red; text-align: center;">Ups! Noget gik galt: ${error.message}. Prøv igen.</p>`;
         }
         if(storySectionHeading) storySectionHeading.textContent = "Fejl ved generering";
         if (storyShareButtonsContainer) {
            storyShareButtonsContainer.classList.remove('hidden');
            const resetButton = storyShareButtonsContainer.querySelector('#reset-button');
            if (resetButton) resetButton.style.display = 'inline-block';
         }
    } finally {
         if(generateButton) { generateButton.disabled = false; generateButton.textContent = 'Skab Historie'; }
         // Skjul loading-indikatoren, uanset hvor den er.
         if(storyLoadingIndicator) storyLoadingIndicator.classList.add('hidden');
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
    if (generateImageButtons.length > 0) generateImageButtons.forEach(button => button.disabled = true); // Deaktiver knapper under kørsel

    try {
    // Kald den nye API funktion og vent på resultatet
        const result = await generateImageApi(currentStoryText);
        // console.log("Image Generation: Result received from generateImageApi:", result); // God til debugging

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
        if (generateImageButtons.length > 0) generateImageButtons.forEach(button => button.disabled = false);
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
async function handleNarrativeGenerateClick() {
    console.log("Narrative Story Generation: Started");

    // Sikkerhedstjek for output-elementer (beholdes)
    if (!narrativeLoadingIndicator || !narrativeErrorDisplay ||
        !narrativeGeneratedStorySection || !narrativeGeneratedTitle || !narrativeGeneratedStory ||
        !narrativeReflectionSection || !narrativeReflectionQuestionsList ||
        !narrativeDebugSection || !narrativeDebugStatus || !narrativeDebugBrief ||
        !narrativeDebugDraftTitle || !narrativeDebugDraftContent) {
        console.error("Narrative Story Generation: One or more critical output elements are missing from the DOM. Please check HTML IDs.");
        if (narrativeErrorDisplay) {
            narrativeErrorDisplay.textContent = "Intern fejl: Nødvendige output-elementer mangler på siden. Kontakt support.";
            narrativeErrorDisplay.classList.remove('hidden');
        } else {
            alert("Intern fejl: Nødvendige output-elementer mangler. Prøv at genindlæse siden eller kontakt support.");
        }
        return;
    }

    // Validering af narrativeFocusInput (vigtigt!)
    const focusText = narrativeFocusInput ? narrativeFocusInput.value.trim() : "";
    if (!focusText) {
        alert("Udfyld venligst det obligatoriske felt 'Tema, Udfordring eller Fokus for Historien' før du genererer en narrativ historie.");
        if (narrativeFocusInput) narrativeFocusInput.focus();
        return;
    }

    // Gem knappens originale tekst og deaktiver den
    const originalButtonText = narrativeGenerateStoryButton.textContent;
    narrativeGenerateStoryButton.disabled = true;
    narrativeGenerateStoryButton.textContent = "Genererer...";

    // UI Opdatering: Skjul output-sektioner, ryd fejl, vis loader
    if (narrativeErrorDisplay) {
        narrativeErrorDisplay.classList.add('hidden');
        narrativeErrorDisplay.textContent = '';
    }
    if (narrativeGeneratedStorySection) narrativeGeneratedStorySection.classList.add('hidden');
    if (narrativeReflectionSection) narrativeReflectionSection.classList.add('hidden');
    if (narrativeDebugSection) narrativeDebugSection.classList.add('hidden');

    // Ryd tidligere specifikt indhold
    if (narrativeGeneratedTitle) narrativeGeneratedTitle.textContent = '';
    if (narrativeGeneratedStory) narrativeGeneratedStory.textContent = 'Vent venligst, historie forberedes...'; // Opdateret placeholder
    if (narrativeReflectionQuestionsList) narrativeReflectionQuestionsList.innerHTML = '<li>Vent venligst...</li>';
    if (narrativeDebugStatus) narrativeDebugStatus.textContent = 'Venter på data...';
    if (narrativeDebugBrief) narrativeDebugBrief.textContent = 'Venter på data...';
    if (narrativeDebugDraftTitle) narrativeDebugDraftTitle.textContent = 'Venter på data...';
    if (narrativeDebugDraftContent) narrativeDebugDraftContent.textContent = 'Venter på data...';

    if (narrativeLoadingIndicator) narrativeLoadingIndicator.classList.remove('hidden');

    // Indsaml data (din eksisterende logik for dataindsamling)
    const childStrengths = [];
    if (narrativeChildStrengthsSelect) {
        if (narrativeChildStrengthsSelect.value && narrativeChildStrengthsSelect.value !== 'other' && narrativeChildStrengthsSelect.value !== '') {
            childStrengths.push(narrativeChildStrengthsSelect.value);
        }
        if (narrativeChildStrengthsSelect.value === 'other' && narrativeChildStrengthsOther && narrativeChildStrengthsOther.value.trim()) {
            childStrengths.push(narrativeChildStrengthsOther.value.trim());
        }
    }
    const childValues = [];
    if (narrativeChildValuesSelect) {
        if (narrativeChildValuesSelect.value && narrativeChildValuesSelect.value !== 'other' && narrativeChildValuesSelect.value !== '') {
            childValues.push(narrativeChildValuesSelect.value);
        }
        if (narrativeChildValuesSelect.value === 'other' && narrativeChildValuesOther && narrativeChildValuesOther.value.trim()) {
            childValues.push(narrativeChildValuesOther.value.trim());
        }
    }
    const importantRelations = [];
    if (document.getElementById('narrative-relations-container')) {
        document.querySelectorAll('#narrative-relations-container .relation-group').forEach(group => {
            const nameInput = group.querySelector('input[name="narrative_relation_name"]');
            const typeInput = group.querySelector('input[name="narrative_relation_type"]');
            const name = nameInput ? nameInput.value.trim() : '';
            const type = typeInput ? typeInput.value.trim() : '';
            if (name || type) importantRelations.push({ name: name, type: type });
        });
    }
    const mainCharacters = [];
    if (document.getElementById('narrative-main-characters-container')) {
        document.querySelectorAll('#narrative-main-characters-container .character-group').forEach(group => {
            const descInput = group.querySelector('input[name="narrative_main_char_desc"]');
            const nameInput = group.querySelector('input[name="narrative_main_char_name"]');
            const description = descInput ? descInput.value.trim() : '';
            const name = nameInput ? nameInput.value.trim() : '';
            if (description) mainCharacters.push({ description: description, name: name });
        });
    }
    const places = [];
    if (document.getElementById('narrative-places-container')) {
        document.querySelectorAll('#narrative-places-container .input-group input[name="narrative_place"]').forEach(input => {
            const value = input.value.trim();
            if (value) places.push(value);
        });
    }
    const plotElements = [];
    if (document.getElementById('narrative-plot-container')) {
        document.querySelectorAll('#narrative-plot-container .input-group input[name="narrative_plot"]').forEach(input => {
            const value = input.value.trim();
            if (value) plotElements.push(value);
        });
    }
    const dataToSend = {
        narrative_focus: narrativeFocusInput ? narrativeFocusInput.value.trim() : '',
        story_goal: narrativeGoalInput ? narrativeGoalInput.value.trim() : '',
        child_name: narrativeChildNameInput ? narrativeChildNameInput.value.trim() : '',
        child_age: narrativeChildAgeInput ? narrativeChildAgeInput.value.trim() : '',
        child_strengths: childStrengths,
        child_values: childValues,
        child_motivation: narrativeChildMotivationInput ? narrativeChildMotivationInput.value.trim() : '',
        child_typical_reaction: narrativeChildReactionTextarea ? narrativeChildReactionTextarea.value.trim() : '',
        important_relations: importantRelations,
        main_characters: mainCharacters,
        places: places,
        plot_elements: plotElements,
        negative_prompt: narrativeNegativePromptInput ? narrativeNegativePromptInput.value.trim() : '',
        length: narrativeLengthSelect ? narrativeLengthSelect.value : 'mellem',
        mood: narrativeMoodSelect ? narrativeMoodSelect.value : 'neutral'
    };
    console.log("Narrative Story Generation: Data prepared for sending (Full Function):", dataToSend);

    try {
        const result = await generateNarrativeStoryApi(dataToSend);
        console.log("DEBUG: Værdi af result efter API kald:", JSON.stringify(result, null, 2));
        console.log("Narrative Story Generation: Server Result RAW (Full Function):", JSON.stringify(result, null, 2));

        // Opdater DEBUG sektion først, da den altid skal vises hvis der er et resultat (også ved fejl i Trin 3)
        if (narrativeDebugStatus) narrativeDebugStatus.textContent = result.status || "Status ikke angivet.";
        if (narrativeDebugBrief) narrativeDebugBrief.textContent = result.narrative_brief_for_reference || "Narrativt brief ikke tilgængeligt.";
        if (narrativeDebugDraftTitle) narrativeDebugDraftTitle.textContent = result.draft_title_from_step2_for_reference || "Udkasttitel (Trin 2) ikke tilgængelig.";
        if (narrativeDebugDraftContent) narrativeDebugDraftContent.textContent = result.draft_content_from_step2_for_reference || "Udkastindhold (Trin 2) ikke tilgængeligt.";
        if (narrativeDebugSection && (result.status || result.narrative_brief_for_reference)) { // Vis kun debug hvis der er noget at vise
            narrativeDebugSection.classList.remove('hidden');
        }


        if (result.error) {
            let errorMessageToDisplay = `Fejl: ${result.error}`;
            if (result.details) errorMessageToDisplay += ` (Detaljer: ${result.details})`;

            if (result.warning && result.title && result.story) { // Specifik Trin 3 fejl-håndtering
                if(narrativeErrorDisplay) {
                    narrativeErrorDisplay.innerHTML = `<strong>Advarsel:</strong> ${result.warning}<br><em>Detaljer om fejl i Trin 3: ${result.error_details_step3 || 'Ukendt fejl i Trin 3.'}</em>`;
                    narrativeErrorDisplay.classList.remove('hidden');
                }
                // Vis stadig udkastet
                if(narrativeGeneratedTitle) narrativeGeneratedTitle.textContent = result.title;
                if(narrativeGeneratedStory) narrativeGeneratedStory.innerHTML = result.story ? result.story.replace(/\n/g, '<br>') : 'Historieudkast mangler.';
                if(narrativeGeneratedStorySection) narrativeGeneratedStorySection.classList.remove('hidden');

                // Og refleksionsspørgsmål for udkastet
                if(narrativeReflectionQuestionsList) narrativeReflectionQuestionsList.innerHTML = '';
                if (result.reflection_questions && Array.isArray(result.reflection_questions) && result.reflection_questions.length > 0) {
                    result.reflection_questions.forEach(question => {
                        const li = document.createElement('li');
                        li.textContent = question;
                        if(narrativeReflectionQuestionsList) narrativeReflectionQuestionsList.appendChild(li);
                    });
                } else {
                    const li = document.createElement('li');
                    li.textContent = "Ingen refleksionsspørgsmål genereret til udkastet.";
                    if(narrativeReflectionQuestionsList) narrativeReflectionQuestionsList.appendChild(li);
                }
                if(narrativeReflectionSection) narrativeReflectionSection.classList.remove('hidden');

            } else { // Generel fejl
                if (narrativeErrorDisplay) {
                    narrativeErrorDisplay.textContent = errorMessageToDisplay;
                    narrativeErrorDisplay.classList.remove('hidden');
                }
            }
} else if (result.title && typeof result.title === 'string' && result.story && typeof result.story === 'string') {
            // SUCCES MED AT HENTE HISTORIEN (TRIN 1-3 FULDFØRT I BACKEND)
            if(narrativeGeneratedTitle) narrativeGeneratedTitle.textContent = result.title;
            if(narrativeGeneratedStory) narrativeGeneratedStory.innerHTML = result.story.replace(/\n/g, '<br>');
            if(narrativeGeneratedStorySection) narrativeGeneratedStorySection.classList.remove('hidden');

            // Nulstil og forbered sektion for refleksionsspørgsmål
            if(narrativeReflectionQuestionsList) {
                narrativeReflectionQuestionsList.innerHTML = '<li>Henter refleksionsspørgsmål... <span class="spinner"></span></li>';
            }
            if(narrativeReflectionSection) narrativeReflectionSection.classList.remove('hidden'); // Sørg for sektionen er synlig

            // Forbered data til at hente spørgsmål
            // VIGTIGT: Sørg for at 'dataToSend' er tilgængelig i dette scope.
            // 'dataToSend' blev defineret tidligere i handleNarrativeGenerateClick funktionen.
            const contextForQuestions = {
                final_story_title: result.title,
                final_story_content: result.story, // Send den rå historie, ikke innerHTML-versionen
                narrative_brief: result.narrative_brief_for_reference,
                original_user_inputs: dataToSend // Hele det oprindelige input-objekt
            };

            // Start asynkront kald for at hente spørgsmål
            console.log("Narrative Story Generation: Initiating call to getGuidingQuestionsApi with context:", contextForQuestions);
            getGuidingQuestionsApi(contextForQuestions)
                .then(questionsResult => {
                    if(narrativeReflectionQuestionsList) narrativeReflectionQuestionsList.innerHTML = ''; // Ryd "Henter..."
                    if (questionsResult.error) {
                        const li = document.createElement('li');
                        li.textContent = `Fejl under hentning af spørgsmål: ${questionsResult.error}`;
                        li.style.color = 'red';
                        if(narrativeReflectionQuestionsList) narrativeReflectionQuestionsList.appendChild(li);
                        console.error("Fejl fra getGuidingQuestionsApi:", questionsResult.error);
                    } else if (questionsResult.reflection_questions && Array.isArray(questionsResult.reflection_questions) && questionsResult.reflection_questions.length > 0) {
                        questionsResult.reflection_questions.forEach(question => {
                            const li = document.createElement('li');
                            li.textContent = question;
                            if(narrativeReflectionQuestionsList) narrativeReflectionQuestionsList.appendChild(li);
                        });
                        console.log("Refleksionsspørgsmål hentet og vist.");
                    } else {
                        const li = document.createElement('li');
                        li.textContent = questionsResult.message || "Ingen refleksionsspørgsmål blev returneret.";
                        if(narrativeReflectionQuestionsList) narrativeReflectionQuestionsList.appendChild(li);
                        console.log("Ingen refleksionsspørgsmål modtaget eller tom liste.");
                    }
                })
                .catch(error => {
                    console.error('Fejl ved kald til getGuidingQuestionsApi (catch):', error);
                    if(narrativeReflectionQuestionsList) {
                        narrativeReflectionQuestionsList.innerHTML = ''; // Ryd "Henter..."
                        const li = document.createElement('li');
                        li.textContent = `Klientfejl under hentning af spørgsmål: ${error.message}`;
                        li.style.color = 'red';
                        narrativeReflectionQuestionsList.appendChild(li);
                    }
                });

        } else { // Uventet, men ikke-fejlende, svarstruktur fra generateNarrativeStoryApi
            if(narrativeErrorDisplay) {
                narrativeErrorDisplay.textContent = "Modtog et uventet eller ufuldstændigt svar fra serveren. Tjek debug-info.";
                narrativeErrorDisplay.classList.remove('hidden');
            }
            console.warn("Narrative Story Generation: Titel eller historie mangler/er ugyldig i serverens svar.", result);
        }

    } catch (error) {
        console.error('Narrative Story Generation: Error during API call or processing:', error);
        if(narrativeErrorDisplay) {
            narrativeErrorDisplay.textContent = `Ups! Noget gik galt: ${error.message}. Prøv igen.`;
            narrativeErrorDisplay.classList.remove('hidden');
        }
    } finally {
        if (narrativeLoadingIndicator) narrativeLoadingIndicator.classList.add('hidden');
        if (narrativeGenerateStoryButton) {
            narrativeGenerateStoryButton.disabled = false;
            narrativeGenerateStoryButton.textContent = originalButtonText; // Gendan original tekst
        }
        console.log("Narrative Story Generation: Finished");
    }
}

    // Tilknyt event listener
    if (narrativeGenerateStoryButton) {
        narrativeGenerateStoryButton.addEventListener('click', handleNarrativeGenerateClick);
    } else {
        console.error("Narrative generate story button (#narrative-generate-story-button) not found!");
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
    if (toggleFeedbackButton) { toggleFeedbackButton.addEventListener('click', toggleFeedbackEmbed); } else { console.error("Toggle feedback button (#toggle-feedback-button) not found!"); }
    if (generateImageButtons.length > 0) {
        generateImageButtons.forEach(button => {
            button.addEventListener('click', handleGenerateImageFromStoryClick);
        });
    } else {
        console.warn("Ingen knapper med klassen '.js-generate-image' blev fundet for event listeners.");
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
// === Event Listeners for Narrativ Støtte Knapper ===
    if (narrativeSuggestTraitsButton) {
        narrativeSuggestTraitsButton.addEventListener('click', async () => {
            console.log("Narrative 'Suggest Traits' button clicked.");
            const focusText = narrativeFocusInput ? narrativeFocusInput.value.trim() : "";

            if (!focusText) {
                alert("Udfyld venligst 'Tema, Udfordring eller Fokus for Historien' først.");
                narrativeFocusInput.focus();
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
                        console.log("Forsøg på at forudfylde problem-karakter felter er udført baseret på AI forslag.");
                        // Ingen alert her - brugeren ser den visuelle ændring.
                    } else {
                        console.log("Ingen forslag til Problem-Karakteren blev anvendt (enten ingen forslag eller felter var allerede udfyldt).");
                        // Ingen alert her heller.
                    }
                } else if (suggestions && suggestions.error) {
                    // Denne alert er en fejlmeddelelse og bør blive for nu.
                    alert(`Fejl under forslag til karaktertræk: ${suggestions.error}`);
                    console.error("Fejl fra suggestCharacterTraitsApi:", suggestions.error);
                } else {
                    // Dette dækker tilfælde, hvor 'suggestions' er null, undefined, eller en anden uventet (men ikke-fejl) struktur.
                    console.warn("Uventet eller tomt svar (uden fejl) fra suggestCharacterTraitsApi:", suggestions);
                    // Ingen alert her. Brugeren ser blot, at intet sker.
                }

            } catch (error) {
                console.error("Fejl ved API kald til suggestCharacterTraitsApi:", error);
                // Denne alert er en fejlmeddelelse og bør blive for nu.
                alert(`Der opstod en fejl under hentning af karaktertræk-forslag: ${error.message}`);
            } finally {
                narrativeSuggestTraitsButton.disabled = false;
                narrativeSuggestTraitsButton.textContent = originalButtonText;
            }
        });
    } else {
        console.warn("Knappen '#narrative-suggest-traits-button' blev ikke fundet.");
    }

    console.log("Script loaded and all initial event listeners attached, including for Narrative Support.");

    initializeInfoIcons(); // Kald funktionen for at aktivere infoknapperne

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
});
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
                <span class="accordion-arrow">▶</span>
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

async function handleLaesehestGenerateClick() {
    const generateButton = document.getElementById('generate-laesehest-button');
    if (!generateButton || generateButton.disabled) return;

    const originalButtonText = generateButton.textContent;
    generateButton.disabled = true;
    generateButton.textContent = 'Skaber historie...';

    const storyDisplay = document.getElementById('story-display');
    const storyTextContent = document.getElementById('story-text-content');
    const storyLoadingIndicator = document.getElementById('story-loading-indicator');
    const storySectionHeading = document.getElementById('story-section-heading');

    storyDisplay.innerHTML = '';
    storyDisplay.appendChild(storyLoadingIndicator);
    storyLoadingIndicator.classList.remove('hidden');
    storyLoadingIndicator.querySelector('p').textContent = 'Historien genereres... Vent venligst.';
    storySectionHeading.textContent = "Jeres historie";
    document.getElementById('story-share-buttons').classList.add('hidden');

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

    const loadingTextTimeout = setTimeout(() => {
        if (generateButton.disabled) {
            storyLoadingIndicator.querySelector('p').textContent = 'Justerer teksten til at passe lixtallet...';
        }
    }, 7000);

    try {
        const result = await generateLixStoryApi(dataToSend);
        clearTimeout(loadingTextTimeout);
        if (result.error) throw new Error(result.error);

        // Tjek om der er en advarselsbesked fra backend
        if (result.warning_message) {
            const storyDisplay = document.getElementById('story-display');
            const warningDiv = document.createElement('div');
            warningDiv.className = 'flash-message flash-warning'; // Genbruger din flash-besked styling
            warningDiv.style.marginBottom = '15px'; // Lidt luft ned til historien
            warningDiv.textContent = result.warning_message;
            storyDisplay.prepend(warningDiv); // Indsætter advarslen øverst i historie-boksen
        }

        const cleanTitle = (result.title || "Uden Titel").trim();
        const cleanStory = (result.story || "Modtog en tom historie.").replace(/^\s+/, '');

        storyLoadingIndicator.classList.add('hidden');

        // Sørg for at tilføje selve historieteksten efter en eventuel advarsel
        const storyContentDiv = document.createElement('div');
        storyContentDiv.id = 'story-text-content'; // Genskab ID for font-styling
        storyContentDiv.textContent = cleanStory;
        storyDisplay.appendChild(storyContentDiv);

        storySectionHeading.innerHTML = `${cleanTitle} <span class="final-lix-tag" title="Beregnet Læsbarhedsindeks">LIX: ${result.final_lix_score}</span>`;
        document.getElementById('story-share-buttons').classList.remove('hidden');
        document.querySelectorAll('.js-generate-image, #read-aloud-button').forEach(btn => btn.disabled = false);

    } catch (error) {
        clearTimeout(loadingTextTimeout);
        console.error("Error in handleLaesehestGenerateClick:", error);
        storyLoadingIndicator.classList.add('hidden');
        storyDisplay.innerHTML = `<p style="color: red; text-align: center;">Ups! Noget gik galt: ${error.message}.</p>`;
        storySectionHeading.textContent = "Fejl ved generering";
    } finally {
        generateButton.disabled = false;
        generateButton.textContent = originalButtonText;
    }
}
// ===================================================================
// SLUT: FUNKTIONER TIL LÆSEHESTEN MODUL
// ===================================================================



// Slut på DOMContentLoaded listener
