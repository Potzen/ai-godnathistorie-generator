import { filterLogbookApi, updateNoteApi } from './modules/api_client.js';

document.addEventListener('DOMContentLoaded', () => {
    const logbookListContainer = document.getElementById('logbook-list-container');
    const filterControls = document.querySelectorAll('.logbook-toolbar select, .logbook-toolbar input');

    // Funktion til at bygge HTML for en enkelt historie-indtastning
    const createStoryEntryHtml = (story) => {
        return `
            <div class="logbook-entry" data-story-id="${story.id}">
                <button type="button" class="logbook-accordion-toggle">
                    <span>
                        <strong>${story.title}</strong>
                        <small style="display: block; color: #555; font-weight: normal;">
                            Kilde: ${story.source || 'Ikke specificeret'} | Dato: ${story.created_at}
                        </small>
                    </span>
                    <span class="arrow">▶</span>
                </button>
                <div class="logbook-accordion-content hidden">
                    <div class="logbook-entry">
                        <button type="button" class="logbook-accordion-toggle nested-accordion-toggle">Læs Historien <span class="arrow">▶</span></button>
                        <div class="logbook-accordion-content nested-accordion-content hidden">
                            <p style="white-space: pre-wrap;">${story.content}</p>
                        </div>
                    </div>
                    <div class="logbook-entry">
                        <button type="button" class="logbook-accordion-toggle nested-accordion-toggle">Se Dokumentation <span class="arrow">▶</span></button>
                        <div class="logbook-accordion-content nested-accordion-content hidden">
                            <h4>Analyse af Historien</h4>
                            <div class="logbook-doc-item"><strong>Problemets Navn:</strong> <span>${story.problem_name || 'Ikke angivet'}</span></div>
                            <div class="logbook-doc-item"><strong>Problemets Indflydelse:</strong> <span>${story.problem_influence || 'Ikke angivet'}</span></div>
                            <div class="logbook-doc-item"><strong>Unique Outcome ("Glimtet"):</strong> <span>${story.unique_outcome || 'Ikke angivet'}</span></div>
                            <div class="logbook-doc-item"><strong>Opdaget Metode/Styrke:</strong> <span>${story.discovered_method_name || 'Ikke angivet'}</span></div>
                            <div class="logbook-doc-item"><strong>Metodens Trin:</strong> <p style="white-space: pre-wrap;">${story.discovered_method_steps || 'Ikke angivet'}</p></div>
                            <div class="logbook-doc-item"><strong>Barnets Værdier:</strong> <span>${story.child_values || 'Ikke angivet'}</span></div>
                            <div class="logbook-doc-item"><strong>Støttesystem ("Vidner"):</strong> <span>${story.support_system || 'Ikke angivet'}</span></div>
                        </div>
                    </div>
                    <div class="logbook-entry">
                        <button type="button" class="logbook-accordion-toggle nested-accordion-toggle">Mine Noter <span class="arrow">▶</span></button>
                        <div class="logbook-accordion-content nested-accordion-content hidden">
                            <textarea class="user-notes-textarea" rows="6" style="width: 100%;" placeholder="Tilføj dine egne noter her...">${story.user_notes || ''}</textarea>
                            <button type="button" class="utility-button note-save-button" style="margin-top: 10px;">Gem ændringer i noter</button>
                            <span class="note-save-feedback hidden" id="note-feedback-${story.id}"></span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    };

    // Funktion til at tilføje event listeners til dynamisk indhold
    const attachEventListeners = () => {
        // Harmonika-funktionalitet
        document.querySelectorAll('.logbook-accordion-toggle').forEach(toggle => {
            toggle.addEventListener('click', () => {
                const content = toggle.nextElementSibling;
                toggle.classList.toggle('open');
                content.classList.toggle('hidden');
            });
        });

        // Gem-note funktionalitet
        document.querySelectorAll('.note-save-button').forEach(button => {
            button.addEventListener('click', async () => {
                const entryDiv = button.closest('.logbook-entry');
                const storyId = entryDiv.dataset.storyId;
                const textarea = entryDiv.querySelector('.user-notes-textarea');
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
            });
        });
    };

    // Funktion til at hente og rendere logbogen baseret på filtre
    const fetchAndRenderLogbook = async () => {
        const filterData = {
            source: document.getElementById('filter-source').value,
            searchTerm: document.getElementById('search-term').value,
            sortBy: document.getElementById('sort-by').value
        };

        logbookListContainer.innerHTML = '<p>Henter historier...</p>';

        try {
            const stories = await filterLogbookApi(filterData);
            if (stories.length === 0) {
                logbookListContainer.innerHTML = '<p style="text-align: center; padding: 20px;">Ingen historier matchede dine filter-kriterier.</p>';
                return;
            }
            logbookListContainer.innerHTML = stories.map(createStoryEntryHtml).join('');
            attachEventListeners(); // VIGTIGT: Tilføj listeners efter HTML er indsat
        } catch (error) {
            logbookListContainer.innerHTML = `<p style="color: red; text-align: center;">Kunne ikke hente historier: ${error.message}</p>`;
        }
    };

    // Tilføj event listeners til filter-kontroller
    let searchTimeout;
    filterControls.forEach(control => {
        if (control.type === 'search') {
            control.addEventListener('input', () => {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(fetchAndRenderLogbook, 300); // Vent 300ms efter brugeren stopper med at taste
            });
        } else {
            control.addEventListener('change', fetchAndRenderLogbook);
        }
    });

});