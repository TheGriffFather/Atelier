# Public Tip Submission

> Phase 3, Task 4 | Priority: Medium | Dependencies: None

## Overview

Create a public-facing form for collectors, dealers, and the public to submit information about artworks they own or have encountered. Integrates with the research leads system and provides a streamlined workflow for reviewing and processing submissions.

## Success Criteria

- [ ] Public submission form (no login required)
- [ ] Image upload capability
- [ ] Anti-spam measures (CAPTCHA, rate limiting)
- [ ] Admin review queue
- [ ] Convert tips to research leads or artworks
- [ ] Email notifications for new submissions
- [ ] Status tracking for submitters
- [ ] Privacy considerations for submitter data

## Database Changes

### New `tip_submissions` Table

```sql
CREATE TABLE tip_submissions (
    id INTEGER PRIMARY KEY,
    -- Submitter info
    submitter_name TEXT NOT NULL,
    submitter_email TEXT NOT NULL,
    submitter_phone TEXT,
    submitter_location TEXT,
    -- Artwork info
    artwork_title TEXT,
    artwork_description TEXT,
    artwork_medium TEXT,
    artwork_dimensions TEXT,
    artwork_year TEXT,
    artwork_signed TEXT,
    -- Ownership/context
    ownership_status TEXT,
    provenance_info TEXT,
    how_acquired TEXT,
    purchase_date TEXT,
    purchase_price TEXT,
    -- Contact preferences
    willing_to_share_images INTEGER DEFAULT 1,
    willing_to_be_contacted INTEGER DEFAULT 1,
    -- Images (JSON array)
    images TEXT,
    -- Additional info
    message TEXT,
    -- Status
    status TEXT DEFAULT 'new',
    priority TEXT DEFAULT 'medium',
    -- Conversion tracking
    converted_to_lead_id INTEGER REFERENCES research_leads(id),
    converted_to_artwork_id INTEGER REFERENCES artworks(id),
    -- Admin notes
    internal_notes TEXT,
    reviewed_by_id INTEGER REFERENCES users(id),
    -- Tracking
    submission_token TEXT UNIQUE,
    submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    reviewed_at DATETIME
);

CREATE INDEX idx_tips_status ON tip_submissions(status);
CREATE INDEX idx_tips_email ON tip_submissions(submitter_email);
CREATE INDEX idx_tips_token ON tip_submissions(submission_token);
```

### Enums

```python
class TipStatus(str, Enum):
    NEW = "new"
    UNDER_REVIEW = "under_review"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    DUPLICATE = "duplicate"
    NEEDS_INFO = "needs_info"

class OwnershipStatus(str, Enum):
    I_OWN = "i_own"
    FAMILY_OWNS = "family_owns"
    SAW_FOR_SALE = "saw_for_sale"
    SAW_IN_COLLECTION = "saw_in_collection"
    HISTORICAL_INFO = "historical_info"
    OTHER = "other"
```

## API Endpoints

### Public Submission (No Auth)

#### POST /api/tips/submit
Submit a tip (public, no authentication).

**Request (multipart/form-data):**
```json
{
  "submitter_name": "John Smith",
  "submitter_email": "john@example.com",
  "submitter_phone": "555-123-4567",
  "submitter_location": "Boston, MA",
  "artwork_title": "Still Life with Currency",
  "artwork_description": "A trompe l'oeil painting of dollar bills...",
  "artwork_medium": "Oil on canvas",
  "artwork_dimensions": "12 x 16 inches",
  "artwork_year": "c. 1985",
  "artwork_signed": "Signed lower right",
  "ownership_status": "i_own",
  "provenance_info": "Purchased at estate sale in Connecticut",
  "how_acquired": "Estate sale",
  "purchase_date": "2015",
  "purchase_price": "$500",
  "willing_to_share_images": true,
  "willing_to_be_contacted": true,
  "message": "I believe this may be by Dan Brown...",
  "captcha_token": "..."
}
```

**Files:** `images[]` - Up to 5 images

**Response:**
```json
{
  "success": true,
  "submission_id": 123,
  "tracking_token": "abc123xyz",
  "message": "Thank you for your submission! You can track its status at /tips/status/abc123xyz"
}
```

#### GET /api/tips/status/{token}
Check submission status (public).

**Response:**
```json
{
  "status": "under_review",
  "submitted_at": "2025-12-05T10:00:00",
  "message": "Your submission is currently being reviewed by our team."
}
```

### Admin Management (Auth Required)

#### GET /api/tips
List all tip submissions.

**Query Parameters:**
- `status`: Filter by status
- `priority`: Filter by priority
- `search`: Search submitter/title
- `from_date`, `to_date`: Date range
- `limit`, `offset`: Pagination

**Response:**
```json
{
  "submissions": [
    {
      "id": 123,
      "submitter_name": "John Smith",
      "submitter_email": "john@example.com",
      "artwork_title": "Still Life with Currency",
      "ownership_status": "i_own",
      "status": "new",
      "priority": "medium",
      "has_images": true,
      "image_count": 3,
      "submitted_at": "2025-12-05T10:00:00"
    }
  ],
  "total": 25
}
```

#### GET /api/tips/{id}
Get full submission details.

**Response:**
```json
{
  "id": 123,
  "submitter_name": "John Smith",
  "submitter_email": "john@example.com",
  "submitter_phone": "555-123-4567",
  "submitter_location": "Boston, MA",
  "artwork_title": "Still Life with Currency",
  "artwork_description": "A trompe l'oeil painting...",
  "artwork_medium": "Oil on canvas",
  "artwork_dimensions": "12 x 16 inches",
  "ownership_status": "i_own",
  "provenance_info": "Purchased at estate sale",
  "message": "I believe this may be by Dan Brown...",
  "images": [
    {
      "url": "/uploads/tips/123_1.jpg",
      "thumbnail_url": "/uploads/tips/123_1_thumb.jpg"
    }
  ],
  "status": "new",
  "priority": "medium",
  "internal_notes": null,
  "submitted_at": "2025-12-05T10:00:00"
}
```

#### PATCH /api/tips/{id}
Update submission (status, priority, notes).

**Request:**
```json
{
  "status": "under_review",
  "priority": "high",
  "internal_notes": "Promising lead, style consistent with known works"
}
```

#### POST /api/tips/{id}/convert-to-lead
Convert submission to research lead.

**Request:**
```json
{
  "title": "Potential Dan Brown - Still Life with Currency",
  "category": "collector_tip",
  "priority": "high",
  "notes": "Submitted by John Smith, claims to own..."
}
```

**Response:**
```json
{
  "success": true,
  "research_lead_id": 45,
  "message": "Converted to research lead #45"
}
```

#### POST /api/tips/{id}/convert-to-artwork
Convert submission directly to artwork.

**Request:**
```json
{
  "title": "Still Life with Currency",
  "year_created": 1985,
  "medium": "Oil on canvas",
  "dimensions": "12 x 16 inches",
  "provenance": "...",
  "is_verified": false
}
```

#### POST /api/tips/{id}/request-info
Request additional information from submitter.

**Request:**
```json
{
  "message": "Thank you for your submission. Could you please provide clearer photos of the signature?"
}
```

Sends email to submitter with request.

#### DELETE /api/tips/{id}
Delete submission (admin only).

### Statistics

#### GET /api/tips/stats
Get tip submission statistics.

**Response:**
```json
{
  "total": 150,
  "by_status": {
    "new": 12,
    "under_review": 8,
    "accepted": 95,
    "rejected": 25,
    "needs_info": 10
  },
  "by_ownership": {
    "i_own": 80,
    "saw_for_sale": 45,
    "historical_info": 25
  },
  "this_month": 15,
  "conversion_rate": 0.63
}
```

## UI Requirements

### Public Submission Form

Location: `/submit` (public page)

**Layout:**

1. **Introduction**
   - Explanation of what we're looking for
   - Privacy statement
   - What happens after submission

2. **Your Information**
   - Name (required)
   - Email (required)
   - Phone (optional)
   - Location (optional)

3. **About the Artwork**
   - Title (if known)
   - Description
   - Medium
   - Dimensions
   - Approximate year
   - Signature details

4. **Your Relationship**
   - Ownership status (radio buttons)
   - How acquired
   - Purchase date/price (optional)
   - Provenance information

5. **Images**
   - Drag-and-drop upload zone
   - Up to 5 images
   - Guidelines for good photos
   - Image preview

6. **Additional Information**
   - Message textarea
   - Consent checkboxes:
     - [ ] I agree to be contacted
     - [ ] I agree to share images for research

7. **CAPTCHA**
   - reCAPTCHA or hCaptcha

8. **Submit Button**

### Status Check Page

Location: `/tips/status/{token}` (public)

**Layout:**
- Status badge
- Submission date
- Current status message
- Contact info if they have questions

### Admin Tips Queue

Location: `/admin/tips`

**Layout:**

1. **Stats Cards**
   - New submissions count
   - Under review count
   - This month total

2. **Filters Bar**
   - Status dropdown
   - Priority dropdown
   - Date range
   - Search

3. **Submissions Table**
   - Columns: Date, Submitter, Title, Status, Priority, Images, Actions
   - Row click to expand/view
   - Quick action buttons

### Tip Detail Modal/Page

**Layout:**

1. **Submitter Info**
   - Contact details
   - Contact preferences

2. **Artwork Info**
   - All submitted fields
   - Description

3. **Images**
   - Gallery view
   - Full-size on click

4. **Status Panel**
   - Current status
   - Priority selector
   - Internal notes (admin only)

5. **Actions**
   - Set status
   - Set priority
   - Convert to lead
   - Convert to artwork
   - Request more info
   - Delete

## Implementation Steps

### Step 1: Database Migration

```python
# scripts/migrations/010_tip_submissions.py
"""
Migration: Public Tip Submissions
Date: YYYY-MM-DD
"""
import sqlite3
from pathlib import Path

def migrate():
    db_path = Path("data/artworks.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tip_submissions (
            id INTEGER PRIMARY KEY,
            submitter_name TEXT NOT NULL,
            submitter_email TEXT NOT NULL,
            submitter_phone TEXT,
            submitter_location TEXT,
            artwork_title TEXT,
            artwork_description TEXT,
            artwork_medium TEXT,
            artwork_dimensions TEXT,
            artwork_year TEXT,
            artwork_signed TEXT,
            ownership_status TEXT,
            provenance_info TEXT,
            how_acquired TEXT,
            purchase_date TEXT,
            purchase_price TEXT,
            willing_to_share_images INTEGER DEFAULT 1,
            willing_to_be_contacted INTEGER DEFAULT 1,
            images TEXT,
            message TEXT,
            status TEXT DEFAULT 'new',
            priority TEXT DEFAULT 'medium',
            converted_to_lead_id INTEGER REFERENCES research_leads(id),
            converted_to_artwork_id INTEGER REFERENCES artworks(id),
            internal_notes TEXT,
            reviewed_by_id INTEGER REFERENCES users(id),
            submission_token TEXT UNIQUE,
            submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            reviewed_at DATETIME
        )
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tips_status ON tip_submissions(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tips_email ON tip_submissions(submitter_email)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tips_token ON tip_submissions(submission_token)")

    conn.commit()
    conn.close()
    print("Migration completed successfully")

if __name__ == "__main__":
    migrate()
```

### Step 2: Update Models

Add to `src/database/models.py`:
- `TipStatus`, `OwnershipStatus` enums
- `TipSubmission` model

### Step 3: Create Tips Service

Create `src/services/tips_service.py`:

```python
import secrets
from typing import Optional
from pathlib import Path

class TipsService:
    """Handle public tip submissions."""

    UPLOADS_DIR = Path("data/uploads/tips")

    async def submit_tip(
        self,
        form_data: dict,
        images: list = None
    ) -> dict:
        """Process public tip submission."""
        # Generate tracking token
        token = secrets.token_urlsafe(16)

        # Save images
        image_paths = []
        if images:
            for i, image in enumerate(images):
                path = await self._save_image(image, token, i)
                image_paths.append(path)

        # Create submission
        pass

    async def _save_image(
        self,
        image,
        token: str,
        index: int
    ) -> str:
        """Save uploaded image."""
        pass

    async def get_status(self, token: str) -> dict:
        """Get submission status for public view."""
        pass

    async def list_submissions(
        self,
        status: str = None,
        priority: str = None,
        search: str = None,
        limit: int = 50,
        offset: int = 0
    ) -> dict:
        """List submissions for admin."""
        pass

    async def get_submission(self, submission_id: int) -> dict:
        """Get full submission details."""
        pass

    async def update_submission(
        self,
        submission_id: int,
        data: dict,
        user_id: int = None
    ) -> TipSubmission:
        """Update submission status/notes."""
        pass

    async def convert_to_lead(
        self,
        submission_id: int,
        lead_data: dict,
        user_id: int = None
    ) -> int:
        """Convert submission to research lead."""
        pass

    async def convert_to_artwork(
        self,
        submission_id: int,
        artwork_data: dict,
        user_id: int = None
    ) -> int:
        """Convert submission to artwork."""
        pass

    async def request_more_info(
        self,
        submission_id: int,
        message: str,
        user_id: int = None
    ) -> None:
        """Send email requesting more info."""
        pass

    async def get_stats(self) -> dict:
        """Get submission statistics."""
        pass

    async def verify_captcha(self, token: str) -> bool:
        """Verify CAPTCHA token."""
        pass
```

### Step 4: Create API Routes

Create `src/api/routes/tips.py`:

```python
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, EmailStr
from typing import Optional, List

router = APIRouter(prefix="/api/tips", tags=["tips"])

class TipSubmitRequest(BaseModel):
    submitter_name: str
    submitter_email: EmailStr
    submitter_phone: Optional[str] = None
    submitter_location: Optional[str] = None
    artwork_title: Optional[str] = None
    artwork_description: Optional[str] = None
    artwork_medium: Optional[str] = None
    artwork_dimensions: Optional[str] = None
    artwork_year: Optional[str] = None
    artwork_signed: Optional[str] = None
    ownership_status: Optional[str] = None
    provenance_info: Optional[str] = None
    how_acquired: Optional[str] = None
    purchase_date: Optional[str] = None
    purchase_price: Optional[str] = None
    willing_to_share_images: bool = True
    willing_to_be_contacted: bool = True
    message: Optional[str] = None
    captcha_token: str

# Public endpoints (no auth)
@router.post("/submit")
async def submit_tip(
    submitter_name: str = Form(...),
    submitter_email: str = Form(...),
    artwork_title: str = Form(None),
    artwork_description: str = Form(None),
    ownership_status: str = Form(None),
    message: str = Form(None),
    captcha_token: str = Form(...),
    images: List[UploadFile] = File(None)
):
    """Public tip submission."""
    pass

@router.get("/status/{token}")
async def get_status(token: str):
    """Public status check."""
    pass

# Admin endpoints (auth required)
@router.get("")
async def list_tips(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    user = Depends(require_editor)
):
    pass

@router.get("/stats")
async def get_stats(user = Depends(require_editor)):
    pass

@router.get("/{id}")
async def get_tip(id: int, user = Depends(require_editor)):
    pass

@router.patch("/{id}")
async def update_tip(id: int, data: dict, user = Depends(require_editor)):
    pass

@router.post("/{id}/convert-to-lead")
async def convert_to_lead(id: int, data: dict, user = Depends(require_editor)):
    pass

@router.post("/{id}/convert-to-artwork")
async def convert_to_artwork(id: int, data: dict, user = Depends(require_editor)):
    pass

@router.post("/{id}/request-info")
async def request_info(id: int, message: str, user = Depends(require_editor)):
    pass

@router.delete("/{id}")
async def delete_tip(id: int, user = Depends(require_admin)):
    pass
```

### Step 5: Create Templates

Create `src/api/templates/submit-tip.html`:
- Public submission form

Create `src/api/templates/tip-status.html`:
- Public status check page

Create `src/api/templates/admin/tips.html`:
- Admin queue interface

### Step 6: Add JavaScript

Create `src/api/static/js/submit-tip.js`:
- Form validation
- Image upload preview
- CAPTCHA integration
- Submission handling

Create `src/api/static/js/admin-tips.js`:
- Queue management
- Status updates
- Conversion modals

## Testing Requirements

### Unit Tests

```python
# tests/test_tips_service.py

def test_submit_tip():
    """Tip submits correctly."""

def test_generate_token():
    """Token is unique."""

def test_save_images():
    """Images save correctly."""

def test_convert_to_lead():
    """Conversion creates lead."""

def test_convert_to_artwork():
    """Conversion creates artwork."""
```

### Integration Tests

```python
# tests/test_tips_api.py

def test_public_submit():
    """Public submission works."""

def test_status_check():
    """Status returns correctly."""

def test_admin_list():
    """Admin can list tips."""

def test_update_status():
    """Status updates correctly."""

def test_request_info_sends_email():
    """Email sent to submitter."""
```

### Manual Testing Checklist

- [ ] Submit tip with images
- [ ] Submit tip without images
- [ ] Check status with token
- [ ] CAPTCHA prevents spam
- [ ] Admin view tip queue
- [ ] Filter by status
- [ ] Update tip status
- [ ] Convert to research lead
- [ ] Convert to artwork
- [ ] Request more information
- [ ] Delete tip

## Security Considerations

1. **Rate Limiting**: Limit submissions per IP/email
2. **CAPTCHA**: Require for all submissions
3. **File Validation**: Validate image types and sizes
4. **Email Verification**: Consider for high-priority tips
5. **Data Privacy**: Handle submitter info carefully
6. **XSS Prevention**: Sanitize all text input
7. **CSRF Protection**: Token-based protection

## Dependencies

- CAPTCHA service (reCAPTCHA or hCaptcha)
- Email service for notifications

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `scripts/migrations/010_tip_submissions.py` | Create | Database migration |
| `src/database/models.py` | Modify | Add enums and model |
| `src/services/tips_service.py` | Create | Business logic |
| `src/api/routes/tips.py` | Create | API endpoints |
| `src/api/main.py` | Modify | Register routes |
| `src/api/templates/submit-tip.html` | Create | Public form |
| `src/api/templates/tip-status.html` | Create | Status page |
| `src/api/templates/admin/tips.html` | Create | Admin queue |
| `src/api/static/js/submit-tip.js` | Create | Form handling |
| `src/api/static/js/admin-tips.js` | Create | Admin logic |
| `tests/test_tips_service.py` | Create | Unit tests |
| `tests/test_tips_api.py` | Create | API tests |

---

*Last updated: December 5, 2025*
