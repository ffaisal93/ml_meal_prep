// Configuration
const DEFAULT_API_URL = 'http://localhost:8000';

// Get API URL from input or use default
function getApiUrl() {
    const apiUrlInput = document.getElementById('apiUrl');
    const url = apiUrlInput.value.trim();
    return url || DEFAULT_API_URL;
}

// Set example query
function setExample(query) {
    document.getElementById('queryInput').value = query;
    document.getElementById('queryInput').focus();
}

// Generate meal plan
async function generateMealPlan() {
    const queryInput = document.getElementById('queryInput');
    const query = queryInput.value.trim();
    const btn = document.getElementById('generateBtn');
    const btnText = document.getElementById('btnText');
    const btnLoader = document.getElementById('btnLoader');
    const errorMessage = document.getElementById('errorMessage');
    const results = document.getElementById('results');

    // Validate input
    if (!query) {
        showError('Please enter a meal plan request');
        return;
    }

    // Show loading state
    btn.disabled = true;
    btnText.textContent = 'Generating...';
    btnLoader.style.display = 'block';
    errorMessage.style.display = 'none';
    results.style.display = 'none';

    try {
        const apiUrl = getApiUrl();
        const generationMode = document.getElementById('generationMode').value;
        
        // Build request body
        const requestBody = { query };
        if (generationMode) {
            requestBody.generation_mode = generationMode;
        }
        
        const response = await fetch(`${apiUrl}/api/generate-meal-plan`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestBody),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || error.error || 'Failed to generate meal plan');
        }

        const data = await response.json();
        displayResults(data);

    } catch (error) {
        console.error('Error:', error);
        showError(error.message || 'Failed to generate meal plan. Please check your API URL and try again.');
    } finally {
        // Reset button state
        btn.disabled = false;
        btnText.textContent = 'Generate Meal Plan';
        btnLoader.style.display = 'none';
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
            'hybrid': '⚡ Hybrid'
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

