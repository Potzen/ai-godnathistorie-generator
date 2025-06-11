// Fil: static/logbook.js (Endelig, robust version)
import { filterLogbookApi, updateNoteApi } from './modules/api_client.js';

// Hent referencer til elementer én gang for effektivitet
const logbookListContainer = document.getElementById('logbook-list-container');
const filterControls = document.querySelectorAll('.logbook-toolbar select, .logbook-toolbar input');

// --- Private hjælpefunktioner i dette modul ---

const createStoryEntryHtml = (story) => {
        const title = story.title || 'Uden Titel';
        const content = story.content || 'Intet indhold.';
        const source = story.source || 'Ikke specificeret';
        const createdAt = story.created_at || 'Ukendt dato';

        // --- NY LOGIK TIL AT BYGGE UNDERTITEL ---

        // Del 1: Information om serien (første linje)
        let seriesInfoParts = [];
        if (story.root_story_title) {
            seriesInfoParts.push(`Original: "${story.root_story_title}"`);
            seriesInfoParts.push(`Del ${story.series_part}`);

            // Rettelse 1: Oversæt "strategy_used"
            if (story.strategy_used) {
                let strategyText = story.strategy_used; // Default
                if (story.strategy_used.toLowerCase() === 'deepen') {
                    strategyText = 'Dyk';
                } else if (story.strategy_used.toLowerCase() === 'generalize') {
                    strategyText = 'Flyv';
                }
                seriesInfoParts.push(strategyText);
            }
        }

        // Del 2: Generel information (anden linje)
        let generalInfoParts = [];
        generalInfoParts.push(`Kilde: ${source}`);
        generalInfoParts.push(`Dato: ${createdAt}`);

        // Sammensæt den endelige HTML med et linjeskift
        let subtitleHtml = '';
        if (seriesInfoParts.length > 0) {
            subtitleHtml += seriesInfoParts.join(' | ');
            // Rettelse 2: Tilføj linjeskift før kilde/dato, HVIS der er serie-information
            subtitleHtml += '<br>';
        }
        subtitleHtml += generalInfoParts.join(' | ');

        // Pak det hele ind i den ydre span
        const finalSubtitleHtml = `<span class="logbook-subtitle">${subtitleHtml}</span>`;

        // ------------------------------------------

        const problemName = story.problem_name || 'Ikke angivet';
        const problemInfluence = story.problem_influence || 'Ikke angivet';
        const uniqueOutcome = story.unique_outcome || 'Ikke angivet';
        const discoveredMethodName = story.discovered_method_name || 'Ikke angivet';
        const discoveredMethodSteps = story.discovered_method_steps || 'Ikke angivet';
        const childValues = story.child_values || 'Ikke angivet';
        const supportSystem = story.support_system || 'Ikke angivet';
        const userNotes = story.user_notes || '';

        return `
            <div class="logbook-entry" data-story-id="${story.id}">
                <button type="button" class="logbook-accordion-toggle">
                    <span class="logbook-title-container">
                        <span class="logbook-title">${title}</span>
                        ${finalSubtitleHtml}
                    </span>
                    <span class="arrow">◀</span>
                </button>
                <div class="logbook-accordion-content hidden">
                    <div class="logbook-inner-entry">
                        <button type="button" class="logbook-accordion-toggle nested-accordion-toggle">Læs Historien <span class="arrow">◀</span></button>
                        <div class="logbook-accordion-content nested-accordion-content hidden">
                            <p style="white-space: pre-wrap;">${content}</p>
                        </div>
                    </div>
                    <div class="logbook-inner-entry">
                        <button type="button" class="logbook-accordion-toggle nested-accordion-toggle">Se Dokumentation <span class="arrow">◀</span></button>
                        <div class="logbook-accordion-content nested-accordion-content hidden">
                            <h4>Analyse af Historien</h4>
                            <div class="logbook-doc-item"><strong>Problemets Navn:</strong> <span>${problemName}</span></div>
                            <div class="logbook-doc-item"><strong>Problemets Indflydelse:</strong> <span>${problemInfluence}</span></div>
                            <div class="logbook-doc-item"><strong>Helten i Aktion ("Glimtet"):</strong> <span>${uniqueOutcome}</span></div>
                            <div class="logbook-doc-item"><strong>Opdaget Metode/Styrke:</strong> <span>${discoveredMethodName}</span></div>
                            <div class="logbook-doc-item"><strong>Fra Historie til Handling:</strong> <p style="white-space: pre-wrap;">${discoveredMethodSteps}</p></div>
                            <div class="logbook-doc-item"><strong>Barnets Værdier (f.eks. Mod, Venskab):</strong> <span>${childValues}</span></div>
                            <div class="logbook-doc-item"><strong>Støttesystem ("Vidner"):</strong> <span>${supportSystem}</span></div>
                        </div>
                    </div>
                    <div class="logbook-inner-entry">
                        <button type="button" class="logbook-accordion-toggle nested-accordion-toggle">Mine Noter <span class="arrow">◀</span></button>
                        <div class="logbook-accordion-content nested-accordion-content hidden">
                            <textarea class="user-notes-textarea" rows="6" style="width: 100%;" placeholder="Tilføj dine egne noter her...">${userNotes}</textarea>
                            <button type="button" class="utility-button note-save-button" style="margin-top: 10px;">Gem ændringer i noter</button>
                            <span class="note-save-feedback hidden" id="note-feedback-${story.id}"></span>
                        </div>
                    </div>
                </div>
            </div>`;
    };

const attachEventListeners = () => {
    const toggles = logbookListContainer.querySelectorAll('.logbook-accordion-toggle');
    console.log(`[logbook.js] Tilknytter listeners til ${toggles.length} harmonika-knapper.`);
    toggles.forEach(toggle => {
        toggle.addEventListener('click', (event) => {
            event.stopPropagation();
            const content = toggle.nextElementSibling;
            if (content && content.classList.contains('logbook-accordion-content')) {
                toggle.classList.toggle('open');
                content.classList.toggle('hidden');
            }
        });
    });

    const saveButtons = logbookListContainer.querySelectorAll('.note-save-button');
    console.log(`[logbook.js] Tilknytter listeners til ${saveButtons.length} 'Gem note'-knapper.`);
    saveButtons.forEach(button => {
        button.addEventListener('click', async () => {
            const entryDiv = button.closest('.logbook-entry');
            const storyId = entryDiv.dataset.storyId;
            const textarea = entryDiv.querySelector('.user-notes-textarea');
            const feedbackSpan = document.getElementById(`note-feedback-${storyId}`);
            button.disabled = true;
            button.textContent = 'Gemmer...';
            try {
                await updateNoteApi(storyId, textarea.value);
                feedbackSpan.textContent = 'Gemt!';
                feedbackSpan.style.color = 'green';
                feedbackSpan.classList.remove('hidden');
                setTimeout(() => feedbackSpan.classList.add('hidden'), 2000);
            } catch (error) {
                feedbackSpan.textContent = `Fejl: ${error.message}`;
                feedbackSpan.style.color = 'red';
            } finally {
                button.disabled = false;
                button.textContent = 'Gem ændringer i noter';
            }
        });
    });
};

// --- Hovedfunktion, der eksporteres ---

export async function initializeLogbook() {
    console.log('[logbook.js] initializeLogbook kaldes.');
    if (!logbookListContainer) {
        console.error('[logbook.js] Fejl: Container for logbogsliste (#logbook-list-container) blev ikke fundet.');
        return;
    }

    const filterData = {
        source: document.getElementById('filter-source').value,
        searchTerm: document.getElementById('search-term').value,
        sortBy: document.getElementById('sort-by').value
    };

    logbookListContainer.innerHTML = '<p>Henter historier...</p>';

    try {
        const stories = await filterLogbookApi(filterData);
        console.log(`[logbook.js] Modtog ${stories.length} historier fra API.`);
        if (stories.length === 0) {
            logbookListContainer.innerHTML = '<p style="text-align: center; padding: 20px;">Ingen historier matchede dine filter-kriterier.</p>';
        } else {
            logbookListContainer.innerHTML = stories.map(createStoryEntryHtml).join('');
            attachEventListeners();
        }
    } catch (error) {
        console.error('[logbook.js] Fejl under hentning eller rendering af logbog:', error);
        logbookListContainer.innerHTML = `<p style="color: red; text-align: center;">Kunne ikke hente historier: ${error.message}</p>`;
    }
}

// --- Tilknyt listeners til filter-kontrollerne med det samme ---
let searchTimeout;
filterControls.forEach(control => {
    const eventType = control.type === 'search' ? 'input' : 'change';
    control.addEventListener(eventType, () => {
        console.log(`[logbook.js] Filter '${control.id}' aktiveret.`);
        if (eventType === 'input') {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(initializeLogbook, 300);
        } else {
            initializeLogbook();
        }
    });
});