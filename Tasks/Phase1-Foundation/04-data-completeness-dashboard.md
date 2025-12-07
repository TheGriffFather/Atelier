# Data Completeness Dashboard

> Phase 1, Task 4 | Priority: Medium | Dependencies: None

## Quick Reference

**Key files to understand before starting:**
- `src/database/models.py` - Artwork model with all fields to check
- `src/api/routes/artworks.py` - Existing artwork endpoints pattern
- `src/api/templates/dashboard.html` - Main dashboard (will add card here)
- `src/api/templates/artwork.html` - Artwork detail page (add completeness badge)
- `src/api/templates/base.html` - Template structure and JS utilities

## Overview

Create a comprehensive data quality dashboard that visualizes the completeness of artwork records, identifies gaps in documentation, and prioritizes which records need attention. Essential for systematic catalogue raisonné work where completeness is critical.

## Success Criteria

- [ ] Visual overview of data completeness across all artworks
- [ ] Per-artwork completeness score (0-100%)
- [ ] Identify which fields are most commonly missing
- [ ] Prioritized list of artworks needing attention
- [ ] Filter by completeness level
- [ ] Track completeness improvement over time
- [ ] Export list of incomplete records
- [ ] Field-specific completeness reports

## Completeness Scoring

### Field Categories and Weights

**Essential Fields (40% weight)**
| Field | Points | Description |
|-------|--------|-------------|
| `title` | 10 | Artwork title |
| `year_created` | 10 | Year or circa date |
| `medium` | 10 | Materials used |
| `dimensions` | 10 | Size in inches |

**Important Fields (35% weight)**
| Field | Points | Description |
|-------|--------|-------------|
| `has_primary_image` | 15 | At least one image |
| `description` | 5 | Artwork description |
| `signed` | 5 | Signature information |
| `subject_matter` | 5 | What's depicted |
| `category` | 5 | Classification |

**Scholarly Fields (25% weight)**
| Field | Points | Description |
|-------|--------|-------------|
| `provenance` | 8 | Ownership history |
| `exhibition_history` | 8 | Where exhibited |
| `literature` | 5 | Publication references |
| `condition` | 4 | Condition notes |

**Total: 100 points**

### Completeness Levels

| Level | Score | Color |
|-------|-------|-------|
| Excellent | 90-100% | Green |
| Good | 70-89% | Blue |
| Fair | 50-69% | Yellow |
| Poor | 25-49% | Orange |
| Critical | 0-24% | Red |

## Database Changes

No new tables required. Completeness is calculated dynamically.

Optional: Add caching table for performance with large datasets.

```sql
-- Optional: Cache completeness scores
CREATE TABLE artwork_completeness_cache (
    artwork_id INTEGER PRIMARY KEY REFERENCES artworks(id),
    completeness_score REAL,
    missing_fields TEXT,  -- JSON array
    last_calculated DATETIME
);
```

## API Endpoints

### Overview Stats

#### GET /api/completeness/overview
Get overall completeness statistics.

**Response:**
```json
{
  "total_artworks": 156,
  "average_completeness": 67.5,
  "by_level": {
    "excellent": 12,
    "good": 45,
    "fair": 58,
    "poor": 31,
    "critical": 10
  },
  "most_missing_fields": [
    {"field": "provenance", "missing_count": 89, "percentage": 57.1},
    {"field": "exhibition_history", "missing_count": 78, "percentage": 50.0},
    {"field": "literature", "missing_count": 102, "percentage": 65.4}
  ],
  "trend": {
    "last_week": 65.2,
    "current": 67.5,
    "change": 2.3
  }
}
```

#### GET /api/completeness/by-field
Get completeness breakdown by field.

**Response:**
```json
{
  "fields": [
    {"field": "title", "complete": 156, "incomplete": 0, "percentage": 100.0},
    {"field": "year_created", "complete": 145, "incomplete": 11, "percentage": 92.9},
    {"field": "medium", "complete": 142, "incomplete": 14, "percentage": 91.0},
    {"field": "provenance", "complete": 67, "incomplete": 89, "percentage": 42.9}
  ]
}
```

### Artwork-Level

#### GET /api/completeness/artworks
Get completeness scores for all artworks.

**Query Parameters:**
- `level`: Filter by level (excellent, good, fair, poor, critical)
- `missing_field`: Filter by specific missing field
- `sort`: Sort by (completeness, title, year)
- `order`: asc or desc
- `limit`: Default 50
- `offset`: Pagination

**Response:**
```json
{
  "artworks": [
    {
      "id": 42,
      "title": "The Harbor",
      "year_created": 1985,
      "completeness_score": 45.0,
      "level": "poor",
      "missing_fields": ["provenance", "exhibition_history", "literature", "condition"],
      "has_image": true
    }
  ],
  "total": 156,
  "average_score": 67.5
}
```

#### GET /api/artworks/{id}/completeness
Get completeness details for single artwork.

**Response:**
```json
{
  "artwork_id": 42,
  "title": "The Harbor",
  "completeness_score": 45.0,
  "level": "poor",
  "field_scores": {
    "title": {"filled": true, "points": 10, "max": 10},
    "year_created": {"filled": true, "points": 10, "max": 10},
    "medium": {"filled": true, "points": 10, "max": 10},
    "dimensions": {"filled": false, "points": 0, "max": 10},
    "has_primary_image": {"filled": true, "points": 15, "max": 15},
    "description": {"filled": false, "points": 0, "max": 5},
    "provenance": {"filled": false, "points": 0, "max": 8}
  },
  "total_points": 45,
  "max_points": 100,
  "priority_fields": ["provenance", "dimensions", "description"]
}
```

### Export

#### GET /api/completeness/export
Export incomplete records as CSV.

**Query Parameters:**
- `max_level`: Include records at or below this level
- `format`: csv (default) or json

**Response:** CSV file download

## UI Requirements

### Completeness Dashboard Page

Location: `/completeness` or integrate into main dashboard

**Layout:**

1. **Summary Cards Row**
   - Total Artworks
   - Average Completeness (with gauge)
   - Most Incomplete Field
   - Improvement This Week (+/- %)

2. **Completeness Distribution Chart**
   - Horizontal bar chart or pie chart
   - Color-coded by level
   - Click to filter list below

3. **Field Completeness Chart**
   - Horizontal bar chart
   - Show each field's completion percentage
   - Sort by least complete

4. **Artworks Needing Attention**
   - Table sorted by completeness (lowest first)
   - Columns: Title, Year, Completeness, Missing Fields, Actions
   - Color-coded completeness badge
   - "Edit" button links to artwork
   - Checkbox for bulk selection

5. **Filters**
   - Completeness level dropdown
   - Missing field multi-select
   - Search by title

6. **Actions**
   - Export Incomplete Records (CSV)
   - Recalculate Scores

### Artwork Detail Integration

On `/artwork/{id}` page:

1. **Completeness Badge**
   - Show score and level in header
   - Color-coded

2. **Completeness Panel** (collapsible)
   - List missing fields
   - "Fill this field" links scroll to field
   - Progress bar visualization

### Dashboard Integration

On main dashboard `/`:

1. **Completeness Summary Card**
   - Average completeness
   - "X records need attention"
   - Link to completeness page

## Implementation Steps

### Step 1: Create Completeness Service

Create `src/services/completeness_service.py`:

```python
from typing import Optional
from dataclasses import dataclass

@dataclass
class FieldScore:
    field: str
    filled: bool
    points: int
    max_points: int
    category: str

class CompletenessService:
    """Calculate and report data completeness."""

    FIELD_CONFIG = {
        # Essential (40%)
        'title': {'points': 10, 'category': 'essential'},
        'year_created': {'points': 10, 'category': 'essential'},
        'medium': {'points': 10, 'category': 'essential'},
        'dimensions': {'points': 10, 'category': 'essential'},
        # Important (35%)
        'has_primary_image': {'points': 15, 'category': 'important', 'special': True},
        'description': {'points': 5, 'category': 'important'},
        'signed': {'points': 5, 'category': 'important'},
        'subject_matter': {'points': 5, 'category': 'important'},
        'category': {'points': 5, 'category': 'important'},
        # Scholarly (25%)
        'provenance': {'points': 8, 'category': 'scholarly'},
        'exhibition_history': {'points': 8, 'category': 'scholarly'},
        'literature': {'points': 5, 'category': 'scholarly'},
        'condition': {'points': 4, 'category': 'scholarly'},
    }

    def calculate_score(self, artwork: dict) -> dict:
        """Calculate completeness score for an artwork."""
        field_scores = []
        total_points = 0
        max_points = 100

        for field, config in self.FIELD_CONFIG.items():
            if config.get('special') and field == 'has_primary_image':
                filled = self._has_primary_image(artwork['id'])
            else:
                value = artwork.get(field)
                filled = value is not None and value != '' and value != []

            points = config['points'] if filled else 0
            total_points += points

            field_scores.append(FieldScore(
                field=field,
                filled=filled,
                points=points,
                max_points=config['points'],
                category=config['category']
            ))

        return {
            'score': round((total_points / max_points) * 100, 1),
            'level': self._get_level(total_points),
            'field_scores': field_scores,
            'missing_fields': [fs.field for fs in field_scores if not fs.filled]
        }

    def _get_level(self, score: float) -> str:
        if score >= 90:
            return 'excellent'
        elif score >= 70:
            return 'good'
        elif score >= 50:
            return 'fair'
        elif score >= 25:
            return 'poor'
        return 'critical'

    async def get_overview(self) -> dict:
        """Get completeness overview stats."""
        pass

    async def get_by_field(self) -> list[dict]:
        """Get completeness breakdown by field."""
        pass

    async def get_artworks(
        self,
        level: Optional[str] = None,
        missing_field: Optional[str] = None,
        sort: str = 'completeness',
        order: str = 'asc',
        limit: int = 50,
        offset: int = 0
    ) -> dict:
        """Get artworks with completeness scores."""
        pass

    async def export_incomplete(
        self,
        max_level: str = 'fair',
        format: str = 'csv'
    ) -> bytes:
        """Export incomplete records."""
        pass
```

### Step 2: Create API Routes

Create `src/api/routes/completeness.py`:

```python
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from typing import Optional

router = APIRouter(prefix="/api/completeness", tags=["completeness"])

@router.get("/overview")
async def get_overview():
    """Get completeness overview."""
    pass

@router.get("/by-field")
async def get_by_field():
    """Get completeness by field."""
    pass

@router.get("/artworks")
async def get_artworks(
    level: Optional[str] = None,
    missing_field: Optional[str] = None,
    sort: str = 'completeness',
    order: str = 'asc',
    limit: int = 50,
    offset: int = 0
):
    """Get artworks with scores."""
    pass

@router.get("/export")
async def export_incomplete(
    max_level: str = 'fair',
    format: str = 'csv'
):
    """Export incomplete records."""
    pass
```

Add to `src/api/routes/artworks.py`:

```python
@router.get("/{id}/completeness")
async def get_artwork_completeness(id: int):
    """Get artwork completeness details."""
    pass
```

### Step 3: Register Routes

Update `src/api/main.py`:
```python
from src.api.routes.completeness import router as completeness_router
app.include_router(completeness_router)
```

### Step 4: Create Completeness Page

Create `src/api/templates/completeness.html`:
- Summary cards
- Charts (use Chart.js)
- Artwork table
- Filters

### Step 5: Add JavaScript

Create `src/api/static/js/completeness.js`:
- Load data
- Render charts
- Filter handling
- Export functionality

### Step 6: Dashboard Integration

Update `src/api/templates/dashboard.html`:
- Add completeness summary card

### Step 7: Artwork Detail Integration

Update `src/api/templates/artwork.html`:
- Add completeness badge
- Add completeness panel

## Testing Requirements

### Unit Tests

```python
# tests/test_completeness_service.py

def test_full_record_scores_100():
    """Complete record scores 100%."""

def test_empty_record_scores_0():
    """Empty record scores near 0%."""

def test_partial_record_correct_score():
    """Partial record calculates correctly."""

def test_level_assignment():
    """Correct level assigned for score ranges."""

def test_missing_fields_identified():
    """Missing fields correctly identified."""

def test_image_check_special_handling():
    """has_primary_image checks images table."""
```

### Integration Tests

```python
# tests/test_completeness_api.py

def test_overview_endpoint():
    """Overview returns correct structure."""

def test_by_field_endpoint():
    """By-field returns all fields."""

def test_artworks_filter_by_level():
    """Level filter works correctly."""

def test_artworks_filter_by_missing_field():
    """Missing field filter works."""

def test_export_csv():
    """Export returns valid CSV."""

def test_artwork_completeness():
    """Single artwork completeness correct."""
```

### Manual Testing Checklist

- [ ] View completeness dashboard
- [ ] Check summary cards show correct data
- [ ] Charts render correctly
- [ ] Filter by completeness level
- [ ] Filter by missing field
- [ ] Sort artwork table
- [ ] Click through to edit artwork
- [ ] Export incomplete records
- [ ] View completeness on artwork detail page
- [ ] Verify score updates when fields filled

## Edge Cases

1. **No Artworks**: Handle empty database gracefully
2. **All Complete**: Show congratulations message
3. **All Incomplete**: Don't overwhelm UI
4. **NULL vs Empty String**: Both count as incomplete
5. **Very Long Missing Fields List**: Truncate with "and X more"
6. **Performance**: Cache scores for large datasets
7. **Deleted Images**: Recalculate has_primary_image

## Chart.js Configuration

Include Chart.js from CDN:
```html
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
```

### Distribution Chart

```javascript
const distributionChart = new Chart(ctx, {
  type: 'doughnut',
  data: {
    labels: ['Excellent', 'Good', 'Fair', 'Poor', 'Critical'],
    datasets: [{
      data: [12, 45, 58, 31, 10],
      backgroundColor: [
        '#22c55e', // green
        '#3b82f6', // blue
        '#eab308', // yellow
        '#f97316', // orange
        '#ef4444'  // red
      ]
    }]
  },
  options: {
    plugins: {
      legend: {
        position: 'bottom'
      }
    }
  }
});
```

### Field Completeness Chart

```javascript
const fieldChart = new Chart(ctx, {
  type: 'bar',
  data: {
    labels: ['provenance', 'exhibition_history', 'literature', ...],
    datasets: [{
      label: 'Complete %',
      data: [42.9, 50.0, 34.6, ...],
      backgroundColor: '#3b82f6'
    }]
  },
  options: {
    indexAxis: 'y',
    scales: {
      x: {
        max: 100
      }
    }
  }
});
```

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `src/services/completeness_service.py` | Create | Calculation logic |
| `src/api/routes/completeness.py` | Create | API endpoints |
| `src/api/routes/artworks.py` | Modify | Add completeness endpoint |
| `src/api/main.py` | Modify | Register routes |
| `src/api/templates/completeness.html` | Create | Dashboard page |
| `src/api/templates/dashboard.html` | Modify | Add summary card |
| `src/api/templates/artwork.html` | Modify | Add badge/panel |
| `src/api/static/js/completeness.js` | Create | Client logic |
| `tests/test_completeness_service.py` | Create | Unit tests |
| `tests/test_completeness_api.py` | Create | API tests |

## Future Enhancements

- **Trend Tracking**: Store historical scores for trend analysis
- **Completeness Targets**: Set goals per category
- **Automated Reminders**: Alert when records fall below threshold
- **Field Suggestions**: AI-powered suggestions for missing data
- **Comparison View**: Compare completeness across artists

---

## Existing Code Reference

### Artwork Model Fields to Check

From `src/database/models.py`, these are the fields included in completeness scoring:

```python
class Artwork(Base):
    __tablename__ = "artworks"

    # Essential Fields (40 points total)
    title: Mapped[str]                              # 10 points - always filled
    year_created: Mapped[Optional[int]]             # 10 points
    medium: Mapped[Optional[str]]                   # 10 points
    dimensions: Mapped[Optional[str]]               # 10 points

    # Important Fields (35 points total)
    # has_primary_image: special check              # 15 points - check images relationship
    description: Mapped[Optional[str]]              # 5 points
    signed: Mapped[Optional[str]]                   # 5 points
    subject_matter: Mapped[Optional[str]]           # 5 points
    category: Mapped[Optional[str]]                 # 5 points

    # Scholarly Fields (25 points total)
    provenance: Mapped[Optional[str]]               # 8 points
    exhibition_history: Mapped[Optional[str]]       # 8 points
    literature: Mapped[Optional[str]]               # 5 points
    condition: Mapped[Optional[str]]                # 4 points

    # Relationship for image check
    images: Mapped[list["ArtworkImage"]] = relationship(back_populates="artwork")
```

### Existing ArtworkResponse Pattern

From `src/api/routes/artworks.py`:

```python
class ArtworkResponse(BaseModel):
    """Response model for artwork data."""
    id: int
    title: str
    description: Optional[str]
    # ... all fields ...

    class Config:
        from_attributes = True
```

### Pydantic Models for Completeness API

```python
from pydantic import BaseModel
from typing import Optional, List, Dict
from enum import Enum

class CompletenessLevel(str, Enum):
    EXCELLENT = "excellent"  # 90-100%
    GOOD = "good"           # 70-89%
    FAIR = "fair"           # 50-69%
    POOR = "poor"           # 25-49%
    CRITICAL = "critical"   # 0-24%

class FieldScore(BaseModel):
    """Score for a single field."""
    field: str
    filled: bool
    points: int
    max_points: int
    category: str  # "essential", "important", "scholarly"

class MissingFieldInfo(BaseModel):
    """Info about a commonly missing field."""
    field: str
    missing_count: int
    percentage: float

class TrendInfo(BaseModel):
    """Completeness trend over time."""
    last_week: float
    current: float
    change: float

class OverviewResponse(BaseModel):
    """Overall completeness statistics."""
    total_artworks: int
    average_completeness: float
    by_level: Dict[str, int]  # {"excellent": 12, "good": 45, ...}
    most_missing_fields: List[MissingFieldInfo]
    trend: Optional[TrendInfo] = None

class FieldCompletenessResponse(BaseModel):
    """Completeness by field."""
    fields: List[Dict[str, any]]  # {"field": "provenance", "complete": 67, "incomplete": 89, "percentage": 42.9}

class ArtworkCompletenessItem(BaseModel):
    """Artwork with completeness info."""
    id: int
    title: str
    year_created: Optional[int]
    completeness_score: float
    level: str
    missing_fields: List[str]
    has_image: bool

    class Config:
        from_attributes = True

class ArtworkListResponse(BaseModel):
    """List of artworks with completeness."""
    artworks: List[ArtworkCompletenessItem]
    total: int
    average_score: float

class ArtworkCompletenessDetail(BaseModel):
    """Detailed completeness for single artwork."""
    artwork_id: int
    title: str
    completeness_score: float
    level: str
    field_scores: Dict[str, Dict[str, any]]  # {"title": {"filled": true, "points": 10, "max": 10}}
    total_points: int
    max_points: int
    missing_fields: List[str]
    priority_fields: List[str]  # Most important missing fields
```

### Route Pattern

```python
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from typing import Optional

router = APIRouter(prefix="/api/completeness", tags=["completeness"])

@router.get("/overview")
async def get_overview() -> OverviewResponse:
    """Get completeness overview."""
    pass

@router.get("/by-field")
async def get_by_field() -> FieldCompletenessResponse:
    """Get completeness by field."""
    pass

@router.get("/artworks")
async def get_artworks(
    level: Optional[str] = None,
    missing_field: Optional[str] = None,
    sort: str = Query("completeness", regex="^(completeness|title|year)$"),
    order: str = Query("asc", regex="^(asc|desc)$"),
    limit: int = Query(50, le=200),
    offset: int = 0
) -> ArtworkListResponse:
    """Get artworks with completeness scores."""
    pass

@router.get("/export")
async def export_incomplete(
    max_level: str = "fair",
    format: str = "csv"
) -> StreamingResponse:
    """Export incomplete records."""
    pass
```

### Template Structure

**New page: `src/api/templates/completeness.html`**

```html
{% extends "base.html" %}

{% block title %}Data Completeness | Dan Brown Catalogue Raisonné{% endblock %}

{% block nav_completeness %}nav-item-active{% endblock %}

{% block head %}
<!-- Chart.js for visualizations -->
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
{% endblock %}

{% block content %}
<div class="p-8">
    <!-- Summary Cards -->
    <div class="grid grid-cols-4 gap-4 mb-8">
        <div class="bg-gray-800 p-4 rounded-lg">
            <div class="text-2xl font-bold text-white" id="total-artworks">0</div>
            <div class="text-sm text-gray-400">Total Artworks</div>
        </div>
        <div class="bg-gray-800 p-4 rounded-lg">
            <div class="text-2xl font-bold text-gold-500" id="avg-completeness">0%</div>
            <div class="text-sm text-gray-400">Average Completeness</div>
        </div>
        <!-- More cards -->
    </div>

    <!-- Charts Row -->
    <div class="grid grid-cols-2 gap-6 mb-8">
        <div class="bg-gray-800 p-4 rounded-lg">
            <h3 class="text-lg font-medium text-white mb-4">Distribution</h3>
            <canvas id="distribution-chart"></canvas>
        </div>
        <div class="bg-gray-800 p-4 rounded-lg">
            <h3 class="text-lg font-medium text-white mb-4">By Field</h3>
            <canvas id="field-chart"></canvas>
        </div>
    </div>

    <!-- Artworks Table -->
    <div class="bg-gray-800 rounded-lg p-4">
        <div class="flex justify-between items-center mb-4">
            <h3 class="text-lg font-medium text-white">Artworks Needing Attention</h3>
            <button onclick="exportIncomplete()" class="btn-secondary">Export CSV</button>
        </div>
        <table class="w-full">
            <thead>
                <tr class="text-left text-gray-400 text-sm">
                    <th class="pb-2">Title</th>
                    <th class="pb-2">Year</th>
                    <th class="pb-2">Completeness</th>
                    <th class="pb-2">Missing</th>
                    <th class="pb-2">Actions</th>
                </tr>
            </thead>
            <tbody id="artworks-table">
                <!-- Populated by JS -->
            </tbody>
        </table>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script src="/api/static/js/completeness.js"></script>
{% endblock %}
```

### Adding Navigation Link

Add to `src/api/templates/base.html`:

```html
<a href="/completeness" class="nav-item {% block nav_completeness %}{% endblock %}" data-nav="completeness">
    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
    </svg>
    <span>Completeness</span>
</a>
```

### Adding Completeness Badge to Artwork Detail

In `src/api/templates/artwork.html`, add this in the header section:

```html
<!-- Completeness Badge -->
<div id="completeness-badge" class="hidden items-center gap-2 px-3 py-1 rounded-full text-sm">
    <span id="completeness-score"></span>
    <span id="completeness-level" class="uppercase text-xs"></span>
</div>

<script>
// Load completeness on page load
async function loadCompleteness(artworkId) {
    const response = await API.get(`/artworks/${artworkId}/completeness`);
    const badge = document.getElementById('completeness-badge');
    const score = document.getElementById('completeness-score');
    const level = document.getElementById('completeness-level');

    score.textContent = `${response.completeness_score}%`;
    level.textContent = response.level;

    // Color based on level
    const colors = {
        excellent: 'bg-green-500/20 text-green-400',
        good: 'bg-blue-500/20 text-blue-400',
        fair: 'bg-yellow-500/20 text-yellow-400',
        poor: 'bg-orange-500/20 text-orange-400',
        critical: 'bg-red-500/20 text-red-400'
    };
    badge.className = `flex items-center gap-2 px-3 py-1 rounded-full text-sm ${colors[response.level]}`;
}
</script>
```

### Database Query Pattern

```python
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from src.database import get_session_context, Artwork, ArtworkImage

async def calculate_completeness_for_artwork(artwork_id: int) -> dict:
    async with get_session_context() as session:
        result = await session.execute(
            select(Artwork)
            .options(selectinload(Artwork.images))
            .where(Artwork.id == artwork_id)
        )
        artwork = result.scalar_one_or_none()

        if not artwork:
            return None

        # Calculate score based on FIELD_CONFIG
        # See CompletenessService in main spec
        return {
            "artwork_id": artwork.id,
            "score": 75.0,
            "level": "good",
            "missing_fields": ["provenance", "literature"]
        }
```

---

*Last updated: December 2025*
