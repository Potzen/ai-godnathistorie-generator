// Fil: static/logbook.js (Endelig, Komplet Version)
import { filterLogbookApi, updateNoteApi, deleteStoryApi } from './modules/api_client.js';

const logbookListContainer = document.getElementById('logbook-list-container');
const filterControls = document.querySelectorAll('.logbook-toolbar select, .logbook-toolbar input');

const createStoryEntryHtml = (story) => {
    const title = story.title || 'Uden Titel';
    const content = story.content || 'Intet indhold.';
    const source = story.source || 'Ikke specificeret';
    const createdAt = story.created_at || 'Ukendt dato';

    let seriesInfoParts = [];
    if (story.root_story_title) {
        seriesInfoParts.push(`Original: "${story.root_story_title}"`);
        seriesInfoParts.push(`Del ${story.series_part}`);
        if (story.strategy_used) {
            let strategyText = story.strategy_used.toLowerCase() === 'deepen' ? 'Dyk' : (story.strategy_used.toLowerCase() === 'generalize' ? 'Flyv' : story.strategy_used);
            seriesInfoParts.push(strategyText);
        }
    }

    let generalInfoParts = [`Kilde: ${source}`, `Dato: ${createdAt}`];
    let subtitleHtml = '';
    if (seriesInfoParts.length > 0) {
        subtitleHtml += seriesInfoParts.join(' | ') + '<br>';
    }
    subtitleHtml += generalInfoParts.join(' | ');

    const finalSubtitleHtml = `<span class="logbook-subtitle">${subtitleHtml}</span>`;

    // Udvidet dataindsamling til analysen
    const aiSummary = story.ai_summary || 'Ikke angivet';
    const problemName = story.problem_name || 'Ikke angivet';
    const problemCategory = story.problem_category || 'Ikke angivet';
    const problemInfluence = story.problem_influence || 'Ikke angivet';
    const uniqueOutcome = story.unique_outcome || 'Ikke angivet';
    const discoveredMethodName = story.discovered_method_name || 'Ikke angivet';
    const strengthType = story.strength_type || 'Ikke angivet';
    const childValues = story.child_values || 'Ikke angivet';
    const supportSystem = story.support_system || 'Ikke angivet';
    const discoveredMethodSteps = story.discovered_method_steps || 'Ikke angivet';
    const userNotes = story.user_notes || '';

    return `
        <div class="logbook-entry" data-story-id="${story.id}">
            <div class="logbook-entry-header">
                <button type="button" class="logbook-accordion-toggle">
                    <span class="logbook-title-container">
                        <span class="logbook-title">${title}</span>
                        ${finalSubtitleHtml}
                    </span>
                    <span class="arrow">◀</span>
                </button>
                <button type="button" class="delete-story-button" title="Slet denne historie permanent" data-story-id="${story.id}">
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
                        <span class="note-save-feedback hidden" id="note-feedback-${story.id}"></span>
                    </div>
                </div>
            </div>
        </div>`;
};

const attachEventListeners = () => {
    // Event listeners for at åbne/lukke indholdet
    const toggles = logbookListContainer.querySelectorAll('.logbook-accordion-toggle, .nested-accordion-toggle');
    toggles.forEach(toggle => {
        toggle.addEventListener('click', () => {
            let content;
            if (toggle.classList.contains('nested-accordion-toggle')) {
                // For nested toggles, content is the next sibling
                content = toggle.nextElementSibling;
            } else {
                // For the main toggle, content is the next sibling of its parent header
                content = toggle.parentElement.nextElementSibling;
            }

            if (content && (content.classList.contains('logbook-accordion-content') || content.classList.contains('nested-accordion-content'))) {
                toggle.classList.toggle('open');
                content.classList.toggle('hidden');
            }
        });
    });

    // Event listeners for 'Gem note'-knapper
    const saveButtons = logbookListContainer.querySelectorAll('.note-save-button');
    saveButtons.forEach(button => {
        button.addEventListener('click', async () => {
            const entryDiv = button.closest('.logbook-entry');
            const storyId = entryDiv.dataset.storyId;
            const textarea = entryDiv.querySelector('.user-notes-textarea');
            const feedbackSpan = document.getElementById(`note-feedback-${story.id}`);
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

    // Event listeners for 'Slet historie'-knapper
    const deleteButtons = logbookListContainer.querySelectorAll('.delete-story-button');
    deleteButtons.forEach(button => {
        button.addEventListener('click', async (event) => {
            event.stopPropagation();
            const storyId = button.dataset.storyId;
            const entryElement = button.closest('.logbook-entry');
            const storyTitle = entryElement.querySelector('.logbook-title').textContent;

            if (window.confirm(`Er du sikker på, at du vil slette historien "${storyTitle}" permanent?`)) {
                try {
                    await deleteStoryApi(storyId);
                    entryElement.style.transition = 'opacity 0.5s ease';
                    entryElement.style.opacity = '0';
                    setTimeout(() => entryElement.remove(), 500);
                } catch (error) {
                    alert(`Fejl: Kunne ikke slette historien. ${error.message}`);
                }
            }
        });
    });
};

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