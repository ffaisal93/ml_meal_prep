# Architecture Diagrams for Slides

## Diagram 1: LLM-Only Strategy

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER QUERY                                    │
│         "I need a week of budget-friendly meals"                │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              QUERY PARSER (OpenAI GPT-4o-mini)                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Extract: duration, dietary restrictions, preferences      │   │
│  │ Output: Structured requirements (JSON)                   │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              MEAL PLAN GENERATOR                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ • Resolve contradictions                                  │   │
│  │ • Generate variety hints (Mediterranean, Asian, etc.)    │   │
│  │ • Track used recipes for diversity                       │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│         RECIPE GENERATION (Day-by-Day Batch)                     │
│                                                                  │
│  Day 1: ┌──────────────────────────────────────┐               │
│         │ OpenAI API Call (Batch)              │               │
│         │ Input: Requirements + Variety Hint   │               │
│         │ Output: Breakfast + Lunch + Dinner  │               │
│         └──────────────────────────────────────┘               │
│                                                                  │
│  Day 2: ┌──────────────────────────────────────┐               │
│         │ OpenAI API Call (Batch)              │               │
│         │ Different variety hint                │               │
│         │ Output: Breakfast + Lunch + Dinner  │               │
│         └──────────────────────────────────────┘               │
│                                                                  │
│  ... (Days 3-7)                                                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    MEAL PLAN RESPONSE                            │
│  • 21 recipes (7 days × 3 meals)                                 │
│  • Ingredients, instructions, nutrition                         │
│  • 90-100% unique meals (diversity tracking)                    │
└─────────────────────────────────────────────────────────────────┘

API Calls: 8 total (1 parse + 7 day batches)
Speed: ~60s for 7-day plan
```

## Diagram 2: RAG Strategy

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER QUERY                                    │
│         "I need a week of budget-friendly meals"                │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              QUERY PARSER (OpenAI GPT-4o-mini)                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Extract: duration, dietary restrictions, preferences      │   │
│  │ Output: Structured requirements (JSON)                   │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              MEAL PLAN GENERATOR                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ • Resolve contradictions                                  │   │
│  │ • Prepare for RAG retrieval                               │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│         STEP 1: FETCH REAL RECIPE CANDIDATES (Day 1)            │
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐│
│  │ Edamam API      │  │ Edamam API      │  │ Edamam API     ││
│  │ Breakfast       │  │ Lunch           │  │ Dinner         ││
│  │ → 5-10 recipes  │  │ → 5-10 recipes  │  │ → 5-10 recipes ││
│  │ with nutrition  │  │ with nutrition  │  │ with nutrition ││
│  └──────────────────┘  └──────────────────┘  └────────────────┘│
│         │                    │                    │             │
│         └────────────────────┴────────────────────┘             │
│                            │                                     │
│                            ▼                                     │
│              ┌─────────────────────────────┐                    │
│              │ Cache (TTL: 1 hour)         │                    │
│              │ Days 2-7: Use cached        │                    │
│              └─────────────────────────────┘                    │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│         STEP 2: LLM SELECTION & REFINEMENT (Per Day)            │
│                                                                  │
│  Day 1: ┌──────────────────────────────────────┐               │
│         │ OpenAI API Call (Batch)               │               │
│         │ Input:                                │               │
│         │   • All Edamam candidates            │               │
│         │   • User requirements                │               │
│         │ Output:                              │               │
│         │   • Breakfast (from candidate)       │               │
│         │   • Lunch (from candidate)          │               │
│         │   • Dinner (from candidate)         │               │
│         │   • Uses exact Edamam nutrition     │               │
│         └──────────────────────────────────────┘               │
│                                                                  │
│  Day 2-7: Same process, using cached candidates                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    MEAL PLAN RESPONSE                            │
│  • 21 recipes (7 days × 3 meals)                                 │
│  • Real recipes from Edamam database                            │
│  • Accurate nutrition data                                       │
│  • 85-95% unique meals (candidate filtering)                    │
└─────────────────────────────────────────────────────────────────┘

API Calls: 11 total (1 parse + 3 Edamam + 7 OpenAI batches)
Speed: ~60-90s for 7-day plan
Caching: Days 2-7 use cached candidates (0 Edamam calls)
```

## Comparison Table for Slides

| Aspect | LLM-Only | RAG |
|--------|----------|-----|
| **Data Source** | Pure AI generation | Real recipe database (Edamam) |
| **Nutrition Accuracy** | AI-estimated | Exact from database |
| **Recipe Realism** | Creative, may be novel | Real, verified recipes |
| **API Calls (7-day)** | 8 OpenAI | 3 Edamam + 8 OpenAI |
| **Speed** | ~60s | ~60-90s |
| **Diversity Method** | Variety hints + tracking | Candidate filtering + shuffling |
| **Diversity Score** | 90-100% | 85-95% |
| **Cost** | Lower | Higher (external API) |
| **Best For** | Creativity, flexibility | Accuracy, real recipes |

## Key Differences Summary

**LLM-Only:**
- ✅ No external dependencies
- ✅ Maximum creativity
- ✅ Faster (no external API wait)
- ❌ Nutrition may be estimated
- ❌ Recipes may be novel/untested

**RAG:**
- ✅ Real, verified recipes
- ✅ Accurate nutrition data
- ✅ Database of 1M+ recipes
- ❌ Requires Edamam API
- ❌ Slightly slower (external calls)

