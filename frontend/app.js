// Configuration
const DEFAULT_API_URL = 'http://localhost:8000';

// Global abort controller for canceling requests
let currentAbortController = null;

function getApiUrl() {
    const apiUrlInput = document.getElementById('apiUrl');
    const url = apiUrlInput.value.trim();
    return url || DEFAULT_API_URL;
}

function getUserId() {
    let id = localStorage.getItem('mealPlannerUserId');
    if (!id) {
        if (window.crypto && window.crypto.randomUUID) {
            id = 'user-' + window.crypto.randomUUID();
        } else {
            id = 'user-' + Math.random().toString(36).slice(2) + Date.now().toString(36);
        }
        localStorage.setItem('mealPlannerUserId', id);
    }
    return id;
}

function setExample(query) {
    document.getElementById('queryInput').value = query;
    document.getElementById('queryInput').focus();
}

async function generateMealPlan() {
    const queryInput = document.getElementById('queryInput');
    const query = queryInput.value.trim();
    const btn = document.getElementById('generateBtn');
    const btnText = document.getElementById('btnText');
    const btnLoader = document.getElementById('btnLoader');
    const stopBtn = document.getElementById('stopBtn');
    const errorMessage = document.getElementById('errorMessage');
    const results = document.getElementById('results');
    
    if (!query) {
        showError('Please enter a meal plan request');
        return;
    }

    // Create new abort controller
    currentAbortController = new AbortController();

    btn.disabled = true;
    
    // Estimate time based on query
    const daysMatch = query.match(/(\d+)\s*[-\s]?day/i);
    const days = daysMatch ? parseInt(daysMatch[1]) : 3;
    const estimatedTime = days <= 3 ? '30-60 seconds' : days <= 5 ? '1-2 minutes' : '2-4 minutes';
    
    btnText.textContent = `Generating... (est. ${estimatedTime})`;
    btnLoader.style.display = 'block';
    // Reset and show stop button
    stopBtn.disabled = false;
    stopBtn.textContent = '⏹️ Stop';
    stopBtn.style.display = 'inline-block';
    errorMessage.style.display = 'none';
    results.style.display = 'none';

    try {
        const apiUrl = getApiUrl();
        const generationMode = document.getElementById('generationMode').value;
        const userId = getUserId();

        const requestBody = { query };
        if (generationMode) requestBody.generation_mode = generationMode;
        if (userId) requestBody.user_id = userId;

        // Set a longer timeout for large meal plans (10 minutes)
        const timeoutId = setTimeout(() => {
            currentAbortController.abort();
        }, 600000); // 10 minutes

        const response = await fetch(`${apiUrl}/api/generate-meal-plan`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            signal: currentAbortController.signal,
            body: JSON.stringify(requestBody),
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || error.error || 'Failed to generate meal plan');
        }

        const data = await response.json();
        displayResults(data);
        if (userId) {
            localStorage.setItem('mealPlannerUserId', userId);
            await loadUserPreferences(userId);
        }
    } catch (error) {
        if (error.name === 'AbortError') {
            showError('Generation stopped by user.');
        } else {
            console.error('Error:', error);
            let errorMsg = error.message || 'Failed to generate meal plan.';
            
            // Provide more helpful error messages
            if (error.message && error.message.includes('fetch')) {
                errorMsg = 'Connection failed. Please check:\n1. API is running\n2. API URL is correct\n3. No CORS issues';
            } else if (error.message && error.message.includes('timeout')) {
                errorMsg = 'Request timed out. Large meal plans may take 2-4 minutes. Please try again.';
            }
            
            showError(errorMsg);
        }
    } finally {
        btn.disabled = false;
        btnText.textContent = 'Generate Meal Plan';
        btnLoader.style.display = 'none';
        stopBtn.style.display = 'none';
        currentAbortController = null;
    }
}

function stopGeneration() {
    if (currentAbortController) {
        currentAbortController.abort();
        const stopBtn = document.getElementById('stopBtn');
        stopBtn.disabled = true;
        stopBtn.textContent = '⏹️ Stopping...';
    }
}

// Display results
function displayResults(data) {
    const results = document.getElementById('results');
    results.style.display = 'block';

    // Show generation mode badge if a mode was selected
    const generationMode = document.getElementById('generationMode').value;
    const modeBadge = document.getElementById('generationModeBadge');
    if (generationMode) {
        const modeLabels = {
            'llm_only': '🤖 LLM-Only',
            'rag': '🔍 RAG',
            'hybrid': '⚡ Hybrid',
            'fast_llm': '⚡ Fast LLM'
        };
        modeBadge.textContent = modeLabels[generationMode] || generationMode.toUpperCase();
        modeBadge.style.display = 'inline-block';
    } else {
        modeBadge.style.display = 'none';
    }

    // Update summary
    document.getElementById('summaryDuration').textContent = `${data.duration_days} days`;
    document.getElementById('summaryMeals').textContent = data.summary.total_meals;
    document.getElementById('summaryCost').textContent = data.summary.estimated_cost;
    document.getElementById('summaryTime').textContent = data.summary.avg_prep_time;

    // Update compliance tags
    const complianceTags = document.getElementById('complianceTags');
    complianceTags.innerHTML = '';
    data.summary.dietary_compliance.forEach(tag => {
        const tagEl = document.createElement('span');
        tagEl.className = 'compliance-tag';
        tagEl.textContent = tag;
        complianceTags.appendChild(tagEl);
    });

    // Display meal plan days
    const mealPlanDays = document.getElementById('mealPlanDays');
    mealPlanDays.innerHTML = '';

    data.meal_plan.forEach(day => {
        const dayCard = createDayCard(day);
        mealPlanDays.appendChild(dayCard);
    });

    // Scroll to results
    results.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// Load user preferences/history
async function loadUserPreferences(userId) {
    if (!userId) {
        document.getElementById('smartSuggestions').style.display = 'none';
        document.getElementById('historySection').style.display = 'none';
        return;
    }
    try {
        const apiUrl = getApiUrl();
        const resp = await fetch(`${apiUrl}/api/user/${encodeURIComponent(userId)}/preferences?limit=10`);
        if (!resp.ok) throw new Error('Failed to load preferences');
        const data = await resp.json();
        const prefs = data.preferences || [];

        // Smart suggestions: use last 2-3 queries
        const suggestionChips = document.getElementById('suggestionChips');
        suggestionChips.innerHTML = '';
        const recent = prefs.slice(0, 3);
        if (recent.length > 0) {
            recent.forEach((p) => {
                const chip = document.createElement('button');
                chip.className = 'suggestion-chip';
                chip.textContent = p.query;
                chip.onclick = () => setExample(p.query);
                suggestionChips.appendChild(chip);
            });
            suggestionChips.classList.remove('empty-state');
        } else {
            suggestionChips.textContent = 'Start generating meal plans to see personalized suggestions.';
            suggestionChips.classList.add('empty-state');
        }
        document.getElementById('smartSuggestions').style.display = 'block';

        // History cards
        const historyCards = document.getElementById('historyCards');
        historyCards.innerHTML = '';
        if (prefs.length === 0) {
            historyCards.textContent = 'Generate a meal plan to start building your history.';
            historyCards.classList.add('empty-state');
        } else {
            prefs.forEach((p) => {
                const card = document.createElement('div');
                card.className = 'history-card';

                const queryDiv = document.createElement('div');
                queryDiv.className = 'history-query';
                queryDiv.textContent = p.query;

                const tagsDiv = document.createElement('div');
                tagsDiv.className = 'history-tags';
                const tags = []
                    .concat(p.dietary_restrictions || [])
                    .concat(p.preferences || [])
                    .concat(p.special_requirements || []);
                tags.forEach(t => {
                    const tagEl = document.createElement('span');
                    tagEl.className = 'history-tag';
                    tagEl.textContent = t;
                    tagsDiv.appendChild(tagEl);
                });

                const actionsDiv = document.createElement('div');
                actionsDiv.className = 'history-actions';
                const regenBtn = document.createElement('button');
                regenBtn.className = 'regenerate-btn';
                regenBtn.textContent = 'Regenerate';
                regenBtn.onclick = () => regenerateMealPlan(p.query);
                actionsDiv.appendChild(regenBtn);

                card.appendChild(queryDiv);
                card.appendChild(tagsDiv);
                card.appendChild(actionsDiv);
                historyCards.appendChild(card);
            });
            historyCards.classList.remove('empty-state');
        }
        document.getElementById('historySection').style.display = 'block';
    } catch (e) {
        console.warn('Failed to load preferences', e);
        document.getElementById('smartSuggestions').style.display = 'none';
        document.getElementById('historySection').style.display = 'none';
    }
}

function toggleHistory() {
    const content = document.getElementById('historyContent');
    const btn = document.getElementById('historyToggleBtn');
    const isHidden = content.style.display === 'none';
    content.style.display = isHidden ? 'block' : 'none';
    btn.textContent = isHidden ? 'Hide History' : 'View History';
}

function regenerateMealPlan(query) {
    document.getElementById('queryInput').value = query;
    generateMealPlan();
}

// Create day card
function createDayCard(day) {
    const dayCard = document.createElement('div');
    dayCard.className = 'day-card';

    const dayHeader = document.createElement('div');
    dayHeader.className = 'day-header';
    dayHeader.innerHTML = `
        <div>
            <div class="day-title">Day ${day.day}</div>
            <div class="day-date">${formatDate(day.date)}</div>
        </div>
    `;

    const mealsContainer = document.createElement('div');
    mealsContainer.className = 'meals-container';

    day.meals.forEach(meal => {
        const mealCard = createMealCard(meal);
        mealsContainer.appendChild(mealCard);
    });

    dayCard.appendChild(dayHeader);
    dayCard.appendChild(mealsContainer);

    return dayCard;
}

// Create meal card
function createMealCard(meal) {
    const mealCard = document.createElement('div');
    mealCard.className = 'meal-card';

    const mealHeader = document.createElement('div');
    mealHeader.className = 'meal-header';
    mealHeader.innerHTML = `
        <span class="meal-type">${meal.meal_type}</span>
        <span style="color: var(--text-secondary); font-size: 0.9rem;">${meal.preparation_time}</span>
    `;

    const mealName = document.createElement('div');
    mealName.className = 'meal-name';
    mealName.textContent = meal.recipe_name;

    const mealDescription = document.createElement('div');
    mealDescription.className = 'meal-description';
    mealDescription.textContent = meal.description;

    const mealDetails = document.createElement('div');
    mealDetails.className = 'meal-details';

    // Ingredients
    const ingredientsSection = document.createElement('div');
    ingredientsSection.className = 'detail-section';
    ingredientsSection.innerHTML = `
        <h4>Ingredients</h4>
        <ul>
            ${meal.ingredients.map(ing => `<li>${ing}</li>`).join('')}
        </ul>
    `;

    // Nutrition
    const nutritionSection = document.createElement('div');
    nutritionSection.className = 'detail-section';
    const nutrition = meal.nutritional_info;
    nutritionSection.innerHTML = `
        <h4>Nutrition (per serving)</h4>
        <div class="nutrition-grid">
            <div class="nutrition-item">
                <div class="nutrition-value">${nutrition.calories}</div>
                <div class="nutrition-label">Calories</div>
            </div>
            <div class="nutrition-item">
                <div class="nutrition-value">${nutrition.protein}g</div>
                <div class="nutrition-label">Protein</div>
            </div>
            <div class="nutrition-item">
                <div class="nutrition-value">${nutrition.carbs}g</div>
                <div class="nutrition-label">Carbs</div>
            </div>
            <div class="nutrition-item">
                <div class="nutrition-value">${nutrition.fat}g</div>
                <div class="nutrition-label">Fat</div>
            </div>
        </div>
    `;

    mealDetails.appendChild(ingredientsSection);
    mealDetails.appendChild(nutritionSection);

    // Instructions
    const instructions = document.createElement('div');
    instructions.className = 'instructions';
    instructions.innerHTML = `
        <h4>Instructions</h4>
        <p>${meal.instructions}</p>
    `;

    mealCard.appendChild(mealHeader);
    mealCard.appendChild(mealName);
    mealCard.appendChild(mealDescription);
    mealCard.appendChild(mealDetails);
    mealCard.appendChild(instructions);

    return mealCard;
}

// Format date
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
        weekday: 'long', 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric' 
    });
}

// Show error
function showError(message) {
    const errorMessage = document.getElementById('errorMessage');
    errorMessage.textContent = message;
    errorMessage.style.display = 'block';
    errorMessage.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

// Open API docs
function openApiDocs() {
    const apiUrl = getApiUrl();
    window.open(`${apiUrl}/docs`, '_blank');
}

// Diversity evaluation
// Allow Enter key to submit (but not Shift+Enter)
document.getElementById('queryInput').addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        generateMealPlan();
    }
});

// Auto-detect Railway URL from current page (if deployed on same domain)
if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
    // If on GitHub Pages, try to detect Railway URL from localStorage or prompt
    const savedApiUrl = localStorage.getItem('mealPlannerApiUrl');
    if (savedApiUrl) {
        document.getElementById('apiUrl').value = savedApiUrl;
    }
}

// Save API URL when changed
document.getElementById('apiUrl').addEventListener('change', (e) => {
    localStorage.setItem('mealPlannerApiUrl', e.target.value);
});

// On page load, ensure user ID exists and load preferences
(async function init() {
    const userId = getUserId();
    await loadUserPreferences(userId);
})();

