// Fil: static/logbook.js
import { filterLogbookApi, updateNoteApi, deleteStoryApi } from './modules/api_client.js';

const logbookListContainer = document.getElementById('logbook-list-container');
const filterControls = document.querySelectorAll('.logbook-toolbar select, .logbook-toolbar input');

/**
 * Escaper tekst der skal ind i HTML.
 *
 * Historieindhold, titler og noter kommer fra brugeren og fra AI'en og blev
 * tidligere sat direkte ind via innerHTML. En note med f.eks. "</textarea>"
 * eller et <script>-tag kunne dermed bryde ud af sit felt og koere som kode
 * naeste gang logbogen blev aabnet.
 */
const escapeHtml = (value) => {
    if (value === null || value === undefined) return '';
    return String(value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
};

const createStoryEntryHtml = (story) => {
    const title = escapeHtml(story.title || 'Uden Titel');
    const content = escapeHtml(story.content || 'Intet indhold.');
    const source = escapeHtml(story.source || 'Ikke specificeret');
    const createdAt = escapeHtml(story.created_at || 'Ukendt dato');

    const seriesInfoParts = [];
    if (story.root_story_title) {
        seriesInfoParts.push(`Original: "${escapeHtml(story.root_story_title)}"`);
        seriesInfoParts.push(`Del ${escapeHtml(story.series_part)}`);
        if (story.strategy_used) {
            const strategy = String(story.strategy_used).toLowerCase();
            const strategyText = strategy === 'deepen' ? 'Dyk'
                : (strategy === 'generalize' ? 'Flyv' : story.strategy_used);
            seriesInfoParts.push(escapeHtml(strategyText));
        }
    }

    let subtitleHtml = '';
    if (seriesInfoParts.length > 0) {
        subtitleHtml += seriesInfoParts.join(' | ') + '<br>';
    }
    subtitleHtml += [`Kilde: ${source}`, `Dato: ${createdAt}`].join(' | ');

    // Felter fra den narrative analyse.
    const field = (value) => escapeHtml(value || 'Ikke angivet');
    const aiSummary = field(story.ai_summary);
    const problemName = field(story.problem_name);
    const problemCategory = field(story.problem_category);
    const problemInfluence = field(story.problem_influence);
    const uniqueOutcome = field(story.unique_outcome);
    const discoveredMethodName = field(story.discovered_method_name);
    const strengthType = field(story.strength_type);
    const childValues = field(story.child_values);
    const supportSystem = field(story.support_system);
    const discoveredMethodSteps = field(story.discovered_method_steps);
    const userNotes = escapeHtml(story.user_notes || '');
    const storyId = escapeHtml(story.id);

    return `
        <div class="logbook-entry" data-story-id="${storyId}">
            <div class="logbook-entry-header">
                <button type="button" class="logbook-accordion-toggle">
                    <span class="logbook-title-container">
                        <span class="logbook-title">${title}</span>
                        <span class="logbook-subtitle">${subtitleHtml}</span>
                    </span>
                    <span class="arrow">◀</span>
                </button>
                <button type="button" class="delete-story-button" title="Slet denne historie permanent" data-story-id="${storyId}">
                    🗑️
                </button>
            </div>
            <div class="logbook-accordion-content hidden">
                <div class="logbook-inner-entry">
                    <button type="button" class="nested-accordion-toggle">Læs Historien <span class="arrow">◀</span></button>
                    <div class="nested-accordion-content hidden">
                        <p style="white-space: pre-wrap;">${content}</p>
                    </div>
                </div>
                <div class="logbook-inner-entry">
                    <button type="button" class="nested-accordion-toggle">Analyse af Historien (narrativ støtte) <span class="arrow">◀</span></button>
                    <div class="nested-accordion-content hidden">
                        <div class="logbook-doc-item"><strong>Pædagogisk Analyse:</strong> <span>${aiSummary}</span></div>
                        <div class="logbook-doc-item"><strong>Problemets Navn:</strong> <span>${problemName}</span></div>
                        <div class="logbook-doc-item"><strong>Problemets Kategori:</strong> <span>${problemCategory}</span></div>
                        <div class="logbook-doc-item"><strong>Problemets Indflydelse (Hvordan påvirkede det barnet?):</strong> <span>${problemInfluence}</span></div>
                        <div class="logbook-doc-item"><strong>Helten i Aktion ("Glimtet"):</strong> <span>${uniqueOutcome}</span></div>
                        <div class="logbook-doc-item"><strong>Opdaget Metode/Styrke:</strong> <span>${discoveredMethodName}</span></div>
                        <div class="logbook-doc-item"><strong>Styrkens Type:</strong> <span>${strengthType}</span></div>
                        <div class="logbook-doc-item"><strong>Barnets Værdier:</strong> <span>${childValues}</span></div>
                        <div class="logbook-doc-item"><strong>Støttesystem ("Vidner"):</strong> <span>${supportSystem}</span></div>
                        <div class="logbook-doc-item"><strong>Fra Historie til Handling:</strong> <p style="white-space: pre-wrap;">${discoveredMethodSteps}</p></div>
                    </div>
                </div>
                <div class="logbook-inner-entry">
                    <button type="button" class="nested-accordion-toggle">Mine Noter <span class="arrow">◀</span></button>
                    <div class="nested-accordion-content hidden">
                        <textarea class="user-notes-textarea" rows="6" style="width: 100%;" placeholder="Tilføj dine egne noter her...">${userNotes}</textarea>
                        <button type="button" class="utility-button note-save-button" style="margin-top: 10px;">Gem ændringer i noter</button>
                        <span class="note-save-feedback hidden"></span>
                    </div>
                </div>
            </div>
        </div>`;
};

const toggleAccordion = (toggle) => {
    const content = toggle.classList.contains('nested-accordion-toggle')
        ? toggle.nextElementSibling
        : toggle.parentElement.nextElementSibling;
    if (content && (content.classList.contains('logbook-accordion-content')
                 || content.classList.contains('nested-accordion-content'))) {
        toggle.classList.toggle('open');
        content.classList.toggle('hidden');
    }
};

const saveNote = async (button) => {
    const entryDiv = button.closest('.logbook-entry');
    const storyId = entryDiv.dataset.storyId;
    const textarea = entryDiv.querySelector('.user-notes-textarea');
    // Feedback-feltet findes inde i selve indgangen. Tidligere blev der slaaet
    // op paa et id bygget af en variabel, der ikke fandtes i denne funktion,
    // hvilket kastede en ReferenceError, saa noter aldrig blev gemt.
    const feedbackSpan = entryDiv.querySelector('.note-save-feedback');

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
        feedbackSpan.classList.remove('hidden');
    } finally {
        button.disabled = false;
        button.textContent = 'Gem ændringer i noter';
    }
};

const deleteEntry = async (button) => {
    const storyId = button.dataset.storyId;
    const entryElement = button.closest('.logbook-entry');
    const storyTitle = entryElement.querySelector('.logbook-title').textContent;

    if (!window.confirm(`Er du sikker på, at du vil slette historien "${storyTitle}" permanent?`)) return;

    try {
        await deleteStoryApi(storyId);
        entryElement.style.transition = 'opacity 0.5s ease';
        entryElement.style.opacity = '0';
        setTimeout(() => entryElement.remove(), 500);
    } catch (error) {
        alert(`Fejl: Kunne ikke slette historien. ${error.message}`);
    }
};

// Én listener paa containeren i stedet for tre pr. historie. Listen bygges om
// ved hver filtrering, saa den gamle model tilfoejede nye listeners hver gang.
if (logbookListContainer) {
    logbookListContainer.addEventListener('click', (event) => {
        const deleteButton = event.target.closest('.delete-story-button');
        if (deleteButton) {
            event.stopPropagation();
            deleteEntry(deleteButton);
            return;
        }
        const saveButton = event.target.closest('.note-save-button');
        if (saveButton) {
            saveNote(saveButton);
            return;
        }
        const toggle = event.target.closest('.logbook-accordion-toggle, .nested-accordion-toggle');
        if (toggle) toggleAccordion(toggle);
    });
}

export async function initializeLogbook() {
    if (!logbookListContainer) return;

    const filterData = {
        source: document.getElementById('filter-source')?.value ?? '',
        searchTerm: document.getElementById('search-term')?.value ?? '',
        sortBy: document.getElementById('sort-by')?.value ?? 'newest'
    };

    logbookListContainer.innerHTML = '<p>Henter historier...</p>';

    try {
        const stories = await filterLogbookApi(filterData);
        if (stories.length === 0) {
            logbookListContainer.innerHTML = '<p style="text-align: center; padding: 20px;">Ingen historier matchede dine filter-kriterier.</p>';
        } else {
            logbookListContainer.innerHTML = stories.map(createStoryEntryHtml).join('');
        }
    } catch (error) {
        console.error('[logbook.js] Kunne ikke hente logbogen:', error);
        logbookListContainer.innerHTML = `<p style="color: red; text-align: center;">Kunne ikke hente historier: ${escapeHtml(error.message)}</p>`;
    }
}

let searchTimeout;
filterControls.forEach(control => {
    const eventType = control.type === 'search' ? 'input' : 'change';
    control.addEventListener(eventType, () => {
        if (eventType === 'input') {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(initializeLogbook, 300);
        } else {
            initializeLogbook();
        }
    });
});
