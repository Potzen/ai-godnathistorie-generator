// Fil: static/skole.js
// ES6 module for the /skole page (Læsehesten + Logbog + Classroom)
import { generateLixStoryApi, generateQuizApi, generateImageApi, saveHojtlasningStoryApi, saveQuizResultApi, listClassroomsApi, createClassroomApi, listClassroomStudentsApi, joinClassroomApi } from './modules/api_client.js';
import { listChildProfilesApi, saveChildProfileApi, deleteChildProfileApi } from './modules/api_client.js';
import { initializeLogbook } from './logbook.js';

document.addEventListener('DOMContentLoaded', () => {

    // === Module-level state ===
    let currentQuizData = [];
    let correctAnswersCount = 0;
    let currentLaesehestStoryId = null; // tracks saved story ID for quiz result submission

    // === Tooltip system ===
    const tooltipElement = document.getElementById('info-tooltip');
    const tooltipTextElement = document.getElementById('info-tooltip-text');
    const tooltipCloseButton = document.getElementById('info-tooltip-close');
    let currentVisibleTooltipIcon = null;
    let clickOpensTooltip = false;

    const tooltipTexts = {};

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

    // === Google Analytics ===
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

    // === Font size controls (storyDisplay only) ===
    const DEFAULT_FONT_SIZE_PX = 16;
    const FONT_SIZE_STEP_PX = 1;
    const MIN_FONT_SIZE_PX = 10;
    const MAX_FONT_SIZE_PX = 30;
    const STORY_DISPLAY_FONT_KEY = 'storyDisplayFontSize';

    let currentStoryDisplayFontSize = DEFAULT_FONT_SIZE_PX;

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
            const savedStoryDisplaySize = localStorage.getItem(STORY_DISPLAY_FONT_KEY);
            if (savedStoryDisplaySize) {
                const newSize = parseInt(savedStoryDisplaySize, 10);
                if (!isNaN(newSize) && newSize >= MIN_FONT_SIZE_PX && newSize <= MAX_FONT_SIZE_PX) {
                    currentStoryDisplayFontSize = newSize;
                }
            }
            const storyDisplay = document.getElementById('story-display');
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

    // === Quiz functions ===
    function renderQuiz(quizData) {
        const quizSektion = document.getElementById('quiz-sektion');
        const quizContainer = document.getElementById('quiz-container');
        const quizFeedback = document.getElementById('quiz-feedback');
        if (!quizSektion || !quizContainer) return;
        currentQuizData = quizData;
        correctAnswersCount = 0;
        quizContainer.innerHTML = '';
        if (quizFeedback) quizFeedback.classList.add('hidden');

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
        const quizFeedback = document.getElementById('quiz-feedback');
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
            if (quizFeedback) {
                quizFeedback.textContent = "Fantastisk! Du har svaret rigtigt på alt. Du kan nu generere et billede til historien.";
                quizFeedback.className = 'flash-message flash-success';
                quizFeedback.classList.remove('hidden');
            }

            document.getElementById('dynamic-quiz-reward-button')?.remove();

            const rewardButton = document.createElement('button');
            rewardButton.id = 'dynamic-quiz-reward-button';
            rewardButton.type = 'button';
            rewardButton.textContent = 'Generer Billede';
            rewardButton.className = 'utility-button quiz-success-button';

            rewardButton.addEventListener('click', handleGenerateImageFromStoryClick);

            if (quizFeedback) {
                quizFeedback.insertAdjacentElement('afterend', rewardButton);
            }

            // Also save quiz result if user is logged in
            const userRoleEl = document.getElementById('current-user-role-data');
            const userRole = userRoleEl ? userRoleEl.dataset.role : 'guest';
            if (userRole !== 'guest') {
                saveQuizResultApi({
                    score: correctAnswersCount,
                    total_questions: currentQuizData.length,
                    story_id: currentLaesehestStoryId || null
                }).catch(err => console.warn('Kunne ikke gemme quizresultat:', err));
            }
        }
    }

    async function fetchAndDisplayQuiz(storyContent, lixScore) {
        const quizSektion = document.getElementById('quiz-sektion');
        const quizContainer = document.getElementById('quiz-container');
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

    // === Image generation ===
    async function handleGenerateImageFromStoryClick() {
        const storyContentElement = document.getElementById('story-text-content');
        const imageSection = document.getElementById('billede-til-historien-sektion');
        const storyImageContainer = document.getElementById('story-image-container');
        const storyImageLoader = document.getElementById('story-image-loader');
        const storyImageDisplay = document.getElementById('story-image-display');
        const storyImageError = document.getElementById('story-image-error');
        const generateImageButtons = document.querySelectorAll('.js-generate-image');

        const currentStoryText = storyContentElement ? storyContentElement.textContent.trim() : "";
        if (!currentStoryText) {
            alert("Generer venligst en historie først.");
            return;
        }

        if (imageSection) imageSection.classList.remove('hidden');
        if (storyImageContainer) storyImageContainer.classList.remove('hidden');
        if (storyImageLoader) storyImageLoader.classList.remove('hidden');
        if (storyImageDisplay) storyImageDisplay.classList.add('hidden');
        if (storyImageError) storyImageError.classList.add('hidden');
        generateImageButtons.forEach(button => button.disabled = true);

        try {
            const dataToSend = {
                story_text: currentStoryText,
                karakterer: [],
                steder: []
            };

            trackGAEvent('generate_image', 'Læsehesten', 'Success', null);

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

    // === Save to logbook button ===
    const saveToLogbookButton = document.getElementById('save-to-logbook-button');
    if (saveToLogbookButton) {
        saveToLogbookButton.addEventListener('click', async () => {
            const titleEl = document.getElementById('story-section-heading');
            const contentEl = document.getElementById('story-text-content');
            const title = titleEl ? titleEl.textContent.replace(/LIX: \d+/, '').trim() : "Uden Titel";
            const content = contentEl ? contentEl.textContent.trim() : "";
            if (!content) { alert("Der er ingen historie at gemme."); return; }
            saveToLogbookButton.disabled = true;
            saveToLogbookButton.textContent = 'Gemmer...';
            try {
                const result = await saveHojtlasningStoryApi({ title, content, source: 'Læsehesten' });
                if (result.story_id) currentLaesehestStoryId = result.story_id;
                saveToLogbookButton.textContent = 'Gemt!';
                saveToLogbookButton.style.backgroundColor = '#28a745';
            } catch (error) {
                alert(`Kunne ikke gemme: ${error.message}`);
                saveToLogbookButton.disabled = false;
                saveToLogbookButton.textContent = 'Gem i Logbog';
            }
        });
    }

    // === Copy story button ===
    const copyStoryButton = document.getElementById('copy-story-button');
    if (copyStoryButton) {
        copyStoryButton.addEventListener('click', async () => {
            const title = document.getElementById('story-section-heading')?.textContent?.replace(/LIX: \d+/, '').trim() || 'Min Historie';
            const content = document.getElementById('story-text-content')?.textContent?.trim() || '';
            const text = `${title}\n\n${content}\n\n---\nSkabt med Read Me A Story (${window.location.origin})`;
            try {
                await navigator.clipboard.writeText(text);
                const orig = copyStoryButton.textContent;
                copyStoryButton.textContent = 'Kopieret!';
                copyStoryButton.disabled = true;
                setTimeout(() => { copyStoryButton.textContent = orig; copyStoryButton.disabled = false; }, 2000);
            } catch { alert('Kopier teksten manuelt.'); }
        });
    }

    // ===================================================================
    // START: FUNKTIONER TIL LÆSEHESTEN MODUL
    // ===================================================================

    function initializeLaesehestenModule() {
        const laesehestenSection = document.getElementById('laesehesten-module');
        if (!laesehestenSection) {
            return;
        }
        fetchLaesehestDataAndRender();
        setupLaesehestEventListeners();
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

    async function handleLaesehestGenerateClick() {
        const generateButton = document.getElementById('generate-laesehest-button');
        if (!generateButton || generateButton.disabled) return;

        const originalButtonText = generateButton.textContent;

        generateButton.disabled = true;
        generateButton.textContent = 'Skaber 3 historier...';

        const historieOutputSection = document.getElementById('historie-output');
        const storyDisplayContainer = document.getElementById('story-display');
        const storySectionHeading = document.getElementById('story-section-heading');
        const storyShareButtons = document.getElementById('story-share-buttons');
        const quizSektion = document.getElementById('quiz-sektion');

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
        if (quizSektion) quizSektion.classList.add('hidden');

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

            if (storyDisplayContainer) storyDisplayContainer.innerHTML = '';

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

                        if (quizSektion) quizSektion.classList.add('hidden');

                        const imageButton = document.querySelector('#story-share-buttons #generate-image-from-output-button');
                        if (imageButton) {
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

                        // Auto-save story to get story_id for quiz result
                        saveHojtlasningStoryApi({ title: variant.title, content: variant.content, source: 'Læsehesten' })
                            .then(r => { if (r.story_id) currentLaesehestStoryId = r.story_id; })
                            .catch(() => {}); // fail silently

                        fetchAndDisplayQuiz(variant.content, variant.lix_score);
                    });

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

    // ===================================================================
    // START: CLASSROOM TEACHER DASHBOARD
    // ===================================================================

    async function loadTeacherDashboard() {
        const container = document.getElementById('classroom-list-container');
        if (!container) return;
        try {
            const data = await listClassroomsApi();
            const classrooms = data.classrooms || [];
            if (classrooms.length === 0) {
                container.innerHTML = '<p>Du har ikke oprettet nogen klasser endnu.</p>';
                return;
            }
            container.innerHTML = classrooms.map(c => `
                <div class="classroom-item" style="border: 1px solid var(--border-color); border-radius: var(--border-radius); padding: 15px; margin-bottom: 10px;">
                    <strong>${c.name}</strong> — ${c.member_count} elever
                    <br><small>Invitationskode: <code style="background:#f0f0f0;padding:2px 6px;border-radius:3px;">${c.invite_code}</code>
                    <button type="button" class="utility-button" style="padding:2px 8px;font-size:0.8em;margin-left:8px;" onclick="navigator.clipboard.writeText('${c.invite_code}').then(()=>this.textContent='Kopieret!').catch(()=>{})">Kopiér</button>
                    </small>
                    <button type="button" class="utility-button" style="margin-top:8px;font-size:0.85em;" data-classroom-id="${c.id}" data-classroom-name="${c.name}">Se Elever</button>
                </div>
            `).join('');
            container.querySelectorAll('[data-classroom-id]').forEach(btn => {
                btn.addEventListener('click', () => loadStudentList(btn.dataset.classroomId, btn.dataset.classroomName));
            });
        } catch (e) {
            container.innerHTML = `<p style="color:red;">Fejl: ${e.message}</p>`;
        }
    }

    async function loadStudentList(classroomId, classroomName) {
        const panel = document.getElementById('student-list-panel');
        const heading = document.getElementById('student-list-heading');
        const container = document.getElementById('student-list-container');
        if (!panel || !container) return;
        panel.classList.remove('hidden');
        if (heading) heading.textContent = `Elever i ${classroomName}`;
        container.innerHTML = '<p>Henter elever...</p>';
        try {
            const data = await listClassroomStudentsApi(classroomId);
            const students = data.students || [];
            if (students.length === 0) {
                container.innerHTML = '<p>Ingen elever tilmeldt endnu.</p>';
                return;
            }
            const trendIcon = t => t === 'up' ? '↑' : t === 'down' ? '↓' : t === 'same' ? '→' : '–';
            container.innerHTML = `
                <table style="width:100%;border-collapse:collapse;font-size:0.9em;">
                    <thead><tr style="background:#f0f0f0;">
                        <th style="padding:8px;text-align:left;border-bottom:1px solid #ddd;">Navn</th>
                        <th style="padding:8px;text-align:center;border-bottom:1px solid #ddd;">Seneste LIX</th>
                        <th style="padding:8px;text-align:center;border-bottom:1px solid #ddd;">Trend</th>
                        <th style="padding:8px;text-align:center;border-bottom:1px solid #ddd;">Quiz snit</th>
                        <th style="padding:8px;text-align:center;border-bottom:1px solid #ddd;">Historier</th>
                    </tr></thead>
                    <tbody>
                        ${students.map(s => `
                            <tr style="border-bottom:1px solid #eee;">
                                <td style="padding:8px;">${s.name}</td>
                                <td style="padding:8px;text-align:center;">${s.latest_lix ?? '–'}</td>
                                <td style="padding:8px;text-align:center;font-size:1.2em;">${trendIcon(s.lix_trend)}</td>
                                <td style="padding:8px;text-align:center;">${s.avg_quiz_pct != null ? s.avg_quiz_pct + '%' : '–'}</td>
                                <td style="padding:8px;text-align:center;">${s.story_count}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>`;
        } catch (e) {
            container.innerHTML = `<p style="color:red;">Fejl: ${e.message}</p>`;
        }
    }

    // Create classroom
    const createClassroomButton = document.getElementById('create-classroom-button');
    const newClassroomName = document.getElementById('new-classroom-name');
    const classroomCreateFeedback = document.getElementById('classroom-create-feedback');
    if (createClassroomButton && newClassroomName) {
        createClassroomButton.addEventListener('click', async () => {
            const name = newClassroomName.value.trim();
            if (!name) { alert('Angiv et klassenavn.'); return; }
            createClassroomButton.disabled = true;
            try {
                await createClassroomApi(name);
                newClassroomName.value = '';
                if (classroomCreateFeedback) {
                    classroomCreateFeedback.textContent = `Klasse "${name}" oprettet!`;
                    classroomCreateFeedback.className = 'flash-message flash-success';
                    classroomCreateFeedback.style.display = 'block';
                    setTimeout(() => { classroomCreateFeedback.style.display = 'none'; }, 3000);
                }
                await loadTeacherDashboard();
            } catch (e) {
                if (classroomCreateFeedback) {
                    classroomCreateFeedback.textContent = `Fejl: ${e.message}`;
                    classroomCreateFeedback.className = 'flash-message flash-error';
                    classroomCreateFeedback.style.display = 'block';
                }
            } finally {
                createClassroomButton.disabled = false;
            }
        });
    }

    // Student join classroom
    const joinClassroomButton = document.getElementById('join-classroom-button');
    const joinClassroomCode = document.getElementById('join-classroom-code');
    const joinClassroomFeedback = document.getElementById('join-classroom-feedback');
    if (joinClassroomButton && joinClassroomCode) {
        joinClassroomButton.addEventListener('click', async () => {
            const code = joinClassroomCode.value.trim().toUpperCase();
            if (!code) { alert('Indtast en invitationskode.'); return; }
            joinClassroomButton.disabled = true;
            try {
                const result = await joinClassroomApi(code);
                if (joinClassroomFeedback) {
                    joinClassroomFeedback.textContent = result.message;
                    joinClassroomFeedback.className = 'flash-message flash-success';
                    joinClassroomFeedback.style.display = 'block';
                }
                joinClassroomCode.value = '';
            } catch (e) {
                if (joinClassroomFeedback) {
                    joinClassroomFeedback.textContent = e.message;
                    joinClassroomFeedback.className = 'flash-message flash-error';
                    joinClassroomFeedback.style.display = 'block';
                }
            } finally {
                joinClassroomButton.disabled = false;
            }
        });
    }

    // ===================================================================
    // SLUT: CLASSROOM TEACHER DASHBOARD
    // ===================================================================

    // ===================================================================
    // START: PROFILE MANAGEMENT (for logbook profile section)
    // ===================================================================

    let allProfilesData = [];

    /**
     * Helper: creates a select element with standard options.
     * Used by createFieldGroup.
     */
    function createSelectWithOptions(name, otherId, selectedValue) {
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

        if (selectedValue && !optionList.includes(selectedValue)) {
            select.value = 'other';
        }

        select.addEventListener('change', function() {
            const otherInput = document.getElementById(this.dataset.otherInputId);
            if (otherInput) {
                otherInput.classList.toggle('hidden', this.value !== 'other');
            }
        });

        return select;
    }

    /** Opretter en komplet gruppe af felter (enten select+other, tekst eller relation) */
    function createFieldGroup(container, type, value = '', relType = '') {
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
    }

    /** Viser de gemte profiler som en liste med rediger- og slet-knapper. */
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

    /** Tilføjer listeners til rediger- og slet-knapper på den renderede profilliste */
    function attachProfileButtonListeners() {
        document.querySelectorAll('.edit-profile-button').forEach(button => {
            button.addEventListener('click', () => {
                const profileId = button.dataset.profileId;
                const profileData = allProfilesData.find(p => p.id == profileId);
                if (profileData) {
                    populateFormWithProfileData(profileData);
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
                    } catch (error) {
                        alert(`Fejl: ${error.message}`);
                    }
                }
            });
        });
    }

    /**
     * Udfylder profil-formularen med data fra et valgt profil-objekt.
     */
    function populateFormWithProfileData(profileData) {
        const profileForm = document.getElementById('child-profile-form');
        if (!profileForm || !profileData) {
            console.error("Kunne ikke udfylde profilformular: Formular eller data mangler.");
            return;
        }

        profileForm.reset();
        document.querySelectorAll('.other-input').forEach(input => input.classList.add('hidden'));

        document.getElementById('profile-id').value = profileData.id || '';
        document.getElementById('profile-name').value = profileData.name || '';
        document.getElementById('profile-age').value = profileData.age || '';

        // Helper to create a select with options (nested, used only here)
        const createSelectWithOptionsLocal = (name, otherId, selectedValue) => {
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

            if (selectedValue && !optionList.includes(selectedValue)) {
                select.value = 'other';
            }

            select.addEventListener('change', function() {
                const otherInput = document.getElementById(this.dataset.otherInputId);
                if (otherInput) {
                    otherInput.classList.toggle('hidden', this.value !== 'other');
                }
            });

            return select;
        };

        // Inner createFieldGroup using the local select helper
        const createFieldGroupLocal = (container, type, value = '', relType = '') => {
            const newGroup = document.createElement('div');
            const uniqueId = `other-${type}-${Date.now()}-${Math.random()}`;

            if (type === 'strength' || type === 'value') {
                newGroup.className = 'input-group';
                const select = createSelectWithOptionsLocal(`profile_${type}`, uniqueId, value);
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

        const populateList = (containerId, items, selectName, otherInputName) => {
            const container = document.getElementById(containerId);
            if (!container) return;
            container.innerHTML = '';

            if (!items || items.length === 0) {
                createFieldGroupLocal(container, selectName.replace('profile_', ''), '', otherInputName);
                return;
            }

            items.forEach(itemValue => {
                createFieldGroupLocal(container, selectName.replace('profile_', ''), itemValue, otherInputName);
            });
        };

        populateList('profile-strengths-container', profileData.strengths, 'profile_strength');
        populateList('profile-values-container', profileData.values, 'profile_value');
        populateList('profile-motivations-container', profileData.motivations, 'profile_motivation');
        populateList('profile-reactions-container', profileData.reactions, 'profile_reaction');

        const relationsContainer = document.getElementById('profile-relations-container');
        if (relationsContainer) {
            relationsContainer.innerHTML = '';
            const relations = (profileData.relations && profileData.relations.length > 0) ? profileData.relations : [{ name: '', type: '' }];
            relations.forEach(rel => createFieldGroupLocal(relationsContainer, 'relation', rel.name || '', rel.type || ''));
        }
    }

    /** Hoved-initialiseringsfunktion for hele profile-featuren */
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
        }).catch(err => console.error("Kunne ikke hente profiler:", err));

        // Tilføj listeners til "Tilføj"-knapper i profil-formularen
        profileForm.querySelectorAll('.add-button').forEach(button => {
            button.addEventListener('click', function() {
                const container = document.getElementById(this.dataset.container);
                if (container) {
                    const isRelation = this.id.includes('relation');
                    createFieldGroup(container, `profile_${this.dataset.name}`, '', isRelation ? '' : '');
                }
            });
        });

        // Ryd formular
        if (clearProfileFormButton) {
            clearProfileFormButton.addEventListener('click', () => {
                profileForm.reset();
                const profileIdEl = document.getElementById('profile-id');
                if (profileIdEl) profileIdEl.value = '';
                ['motivations', 'reactions', 'relations'].forEach(type => {
                    const container = document.getElementById(`profile-${type}-container`);
                    if (container) {
                        container.innerHTML = '';
                        createFieldGroup(container, `profile_${type}`, '', type === 'relation' ? '' : '');
                    }
                });
                if (profileSaveFeedback) profileSaveFeedback.style.display = 'none';
            });
        }

        // Gem/Opdater profil (FORM SUBMIT)
        profileForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            const saveButton = document.getElementById('save-profile-button');
            const feedbackEl = document.getElementById('profile-save-feedback');
            if (saveButton) { saveButton.disabled = true; saveButton.textContent = 'Gemmer...'; }

            const profileIdBeforeSave = document.getElementById('profile-id')?.value;

            // Indsamler data fra dropdowns for Styrker
            const strengths = [];
            document.querySelectorAll('#profile-strengths-container .input-group').forEach(group => {
                const select = group.querySelector('select[name="profile_strength"]');
                if (!select) return;
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
                if (!select) return;
                if (select.value === 'other') {
                    const otherInput = group.querySelector('input[name="profile_value_other"]');
                    if (otherInput && otherInput.value.trim()) values.push(otherInput.value.trim());
                } else if (select.value) {
                    values.push(select.value);
                }
            });

            const profileData = {
                id: document.getElementById('profile-id')?.value,
                name: document.getElementById('profile-name')?.value.trim(),
                age: document.getElementById('profile-age')?.value.trim(),
                strengths: strengths,
                values: values,
                motivations: Array.from(document.querySelectorAll('input[name="profile_motivation"]')).map(i => i.value.trim()).filter(Boolean),
                reactions: Array.from(document.querySelectorAll('input[name="profile_reaction"]')).map(i => i.value.trim()).filter(Boolean),
                relations: Array.from(document.querySelectorAll('#profile-relations-container .relation-group')).map(g => ({
                    name: g.querySelector('input[name="profile_relation_name"]')?.value.trim() || '',
                    type: g.querySelector('input[name="profile_relation_type"]')?.value.trim() || ''
                })).filter(r => r.name || r.type)
            };

            try {
                const result = await saveChildProfileApi(profileData);
                if (feedbackEl) {
                    feedbackEl.textContent = result.message;
                    feedbackEl.className = 'flash-message flash-success';
                }

                const updatedProfiles = await listChildProfilesApi();
                allProfilesData = updatedProfiles;
                renderSavedProfilesForEditing(updatedProfiles);

                if (profileIdBeforeSave) {
                    const updatedProfileData = allProfilesData.find(p => p.id == profileIdBeforeSave);
                    if (updatedProfileData) {
                        populateFormWithProfileData(updatedProfileData);
                    }
                } else {
                    if (clearProfileFormButton) clearProfileFormButton.click();
                }

            } catch (error) {
                if (feedbackEl) {
                    feedbackEl.textContent = `Fejl: ${error.message}`;
                    feedbackEl.className = 'flash-message flash-error';
                }
            } finally {
                if (feedbackEl) feedbackEl.style.display = 'block';
                if (saveButton) { saveButton.disabled = false; saveButton.textContent = 'Gem Profil'; }
            }
        });
    }

    // ===================================================================
    // SLUT: PROFILE MANAGEMENT
    // ===================================================================

    // ===================================================================
    // INITIALIZATION
    // ===================================================================

    // Font sizes
    loadFontSizesFromLocalStorage();

    // Info icons
    initializeInfoIcons();

    // Læsehesten module
    initializeLaesehestenModule();

    // Font size controls (for story display)
    const storyDisplay = document.getElementById('story-display');
    const decreaseFontButton = document.getElementById('decrease-font-button');
    const increaseFontButton = document.getElementById('increase-font-button');
    const resetFontButton = document.getElementById('reset-font-button');

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

    // Image button
    const imageButton = document.getElementById('generate-image-from-output-button');
    if (imageButton) imageButton.addEventListener('click', handleGenerateImageFromStoryClick);

    // Teacher dashboard
    if (document.getElementById('teacher-classroom-section')) loadTeacherDashboard();

    // Profile feature (logbook)
    initializeProfileFeature();

    // Logbook
    const logbookListContainer = document.getElementById('logbook-list-container');
    if (logbookListContainer) {
        const userRoleEl = document.getElementById('current-user-role-data');
        const userRole = userRoleEl ? userRoleEl.dataset.role : 'guest';
        if (userRole !== 'guest') {
            initializeLogbook();
        }
    }

    // Dropdown toggles for profile section
    document.querySelectorAll('.narrative-info-dropdown .dropdown-toggle').forEach(toggle => {
        toggle.addEventListener('click', () => {
            const content = toggle.nextElementSibling;
            if (content && content.classList.contains('dropdown-content')) {
                content.classList.toggle('hidden');
                toggle.classList.toggle('open');
            }
        });
    });

}); // end DOMContentLoaded
