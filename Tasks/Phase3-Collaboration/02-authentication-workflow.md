# Authentication Workflow

> Phase 3, Task 2 | Priority: High | Dependencies: Multi-User Support (Task 01)

## Overview

Implement a scholarly authentication workflow for artworks, allowing experts to review and authenticate works. Tracks authentication status, records expert opinions, and provides a structured review process. Essential for establishing the legitimacy of artworks in the catalogue raisonné.

## Success Criteria

- [ ] Track authentication status per artwork
- [ ] Record expert opinions with supporting documentation
- [ ] Multi-stage review workflow (unreviewed → under review → authenticated)
- [ ] Store expert credentials and qualifications
- [ ] Support conditional authentications ("if cleaned", "subject to examination")
- [ ] Generate authentication certificates
- [ ] Dashboard showing authentication progress
- [ ] Audit trail of all authentication decisions

## Database Changes

### Modify `artworks` Table

Add authentication columns:

```sql
ALTER TABLE artworks ADD COLUMN authentication_status TEXT DEFAULT 'unreviewed';
ALTER TABLE artworks ADD COLUMN authentication_date DATETIME;
ALTER TABLE artworks ADD COLUMN authenticated_by_id INTEGER REFERENCES users(id);
ALTER TABLE artworks ADD COLUMN authentication_notes TEXT;
```

### New `expert_opinions` Table

```sql
CREATE TABLE expert_opinions (
    id INTEGER PRIMARY KEY,
    artwork_id INTEGER NOT NULL REFERENCES artworks(id) ON DELETE CASCADE,
    expert_name TEXT NOT NULL,
    expert_title TEXT,
    expert_institution TEXT,
    expert_email TEXT,
    opinion_date DATETIME NOT NULL,
    opinion TEXT NOT NULL,
    confidence_level TEXT,
    reasoning TEXT,
    conditions TEXT,
    document_url TEXT,
    created_by_id INTEGER REFERENCES users(id),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_expert_opinions_artwork ON expert_opinions(artwork_id);
CREATE INDEX idx_expert_opinions_opinion ON expert_opinions(opinion);
```

### New `authentication_documents` Table

```sql
CREATE TABLE authentication_documents (
    id INTEGER PRIMARY KEY,
    artwork_id INTEGER NOT NULL REFERENCES artworks(id) ON DELETE CASCADE,
    expert_opinion_id INTEGER REFERENCES expert_opinions(id),
    document_type TEXT NOT NULL,
    title TEXT NOT NULL,
    file_path TEXT,
    url TEXT,
    notes TEXT,
    uploaded_by_id INTEGER REFERENCES users(id),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_auth_docs_artwork ON authentication_documents(artwork_id);
```

### Enums

```python
class AuthenticationStatus(str, Enum):
    UNREVIEWED = "unreviewed"
    UNDER_REVIEW = "under_review"
    AUTHENTICATED = "authenticated"
    REJECTED = "rejected"
    UNCERTAIN = "uncertain"
    CONDITIONAL = "conditional"    # "Authentic if cleaned"

class ExpertOpinion(str, Enum):
    AUTHENTICATED = "authenticated"
    REJECTED = "rejected"
    UNCERTAIN = "uncertain"
    NEEDS_EXAMINATION = "needs_examination"

class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class DocumentType(str, Enum):
    EXPERT_LETTER = "expert_letter"
    CERTIFICATE = "certificate"
    ANALYSIS_REPORT = "analysis_report"
    PROVENANCE_DOCUMENT = "provenance_document"
    PHOTOGRAPH = "photograph"
    OTHER = "other"
```

## Authentication Workflow

### Status Flow

```
┌─────────────┐     ┌───────────────┐     ┌───────────────┐
│  UNREVIEWED │────▶│ UNDER_REVIEW  │────▶│ AUTHENTICATED │
└─────────────┘     └───────────────┘     └───────────────┘
                           │                      │
                           │                      ▼
                           │              ┌───────────────┐
                           │              │  CONDITIONAL  │
                           │              └───────────────┘
                           │
                           ├─────────────▶┌───────────────┐
                           │              │   REJECTED    │
                           │              └───────────────┘
                           │
                           └─────────────▶┌───────────────┐
                                          │   UNCERTAIN   │
                                          └───────────────┘
```

### Review Process

1. **Submit for Review**: Move artwork to "under review"
2. **Add Expert Opinion**: Record one or more expert opinions
3. **Upload Documents**: Attach supporting documentation
4. **Make Decision**: Set final authentication status
5. **Generate Certificate**: Create authentication certificate (if authenticated)

## API Endpoints

### Authentication Status

#### GET /api/artworks/{id}/authentication
Get artwork authentication details.

**Response:**
```json
{
  "artwork_id": 42,
  "authentication_status": "authenticated",
  "authentication_date": "2025-12-01T10:00:00",
  "authenticated_by": {
    "id": 1,
    "display_name": "John Smith"
  },
  "authentication_notes": "Authenticated based on provenance and expert examination",
  "expert_opinions": [
    {
      "id": 1,
      "expert_name": "Dr. Jane Wilson",
      "expert_title": "Professor of American Art",
      "expert_institution": "Yale University",
      "opinion_date": "2025-11-15T00:00:00",
      "opinion": "authenticated",
      "confidence_level": "high",
      "reasoning": "Consistent with artist's known style and technique..."
    }
  ],
  "documents": [
    {
      "id": 1,
      "document_type": "expert_letter",
      "title": "Authentication Letter - Dr. Wilson",
      "file_path": "/uploads/auth_docs/42_1.pdf"
    }
  ]
}
```

#### POST /api/artworks/{id}/authentication/submit-for-review
Submit artwork for authentication review.

**Request:**
```json
{
  "notes": "Requesting authentication review based on recent provenance discovery"
}
```

#### POST /api/artworks/{id}/authentication/set-status
Set authentication status.

**Request:**
```json
{
  "status": "authenticated",
  "notes": "Authenticated based on expert consensus",
  "conditions": null
}
```

### Expert Opinions

#### POST /api/artworks/{id}/expert-opinions
Add expert opinion.

**Request:**
```json
{
  "expert_name": "Dr. Jane Wilson",
  "expert_title": "Professor of American Art",
  "expert_institution": "Yale University",
  "expert_email": "jwilson@yale.edu",
  "opinion_date": "2025-11-15",
  "opinion": "authenticated",
  "confidence_level": "high",
  "reasoning": "The brushwork and composition are consistent with Brown's mature period...",
  "conditions": null
}
```

#### GET /api/artworks/{id}/expert-opinions
List expert opinions for artwork.

#### PATCH /api/expert-opinions/{id}
Update expert opinion.

#### DELETE /api/expert-opinions/{id}
Delete expert opinion.

### Documents

#### POST /api/artworks/{id}/authentication/documents
Upload authentication document.

**Request (multipart/form-data):**
- `file`: Document file (PDF, image)
- `document_type`: Type enum
- `title`: Document title
- `expert_opinion_id`: Link to expert opinion (optional)
- `notes`: Notes

#### GET /api/artworks/{id}/authentication/documents
List authentication documents.

#### DELETE /api/authentication/documents/{id}
Delete document.

### Certificate Generation

#### GET /api/artworks/{id}/authentication/certificate
Generate authentication certificate.

**Query Parameters:**
- `format`: pdf, html

**Response:** PDF file or HTML content

### Dashboard/Reports

#### GET /api/authentication/dashboard
Get authentication dashboard stats.

**Response:**
```json
{
  "total_artworks": 156,
  "by_status": {
    "unreviewed": 45,
    "under_review": 12,
    "authenticated": 85,
    "rejected": 5,
    "uncertain": 7,
    "conditional": 2
  },
  "recent_authentications": [
    {
      "artwork_id": 42,
      "title": "The Harbor",
      "status": "authenticated",
      "date": "2025-12-01"
    }
  ],
  "pending_reviews": [
    {
      "artwork_id": 55,
      "title": "Duck Decoy",
      "submitted_date": "2025-11-25"
    }
  ]
}
```

#### GET /api/authentication/queue
Get artworks awaiting review.

## UI Requirements

### Authentication Dashboard

Location: `/authentication` (new page)

**Layout:**

1. **Stats Cards**
   - Total artworks by status (pie chart)
   - Recently authenticated
   - Pending reviews count

2. **Review Queue**
   - Table of artworks under review
   - Columns: Artwork, Submitted, Expert Opinions, Actions
   - "Review" button

3. **Quick Filters**
   - Status dropdown
   - Date range
   - Has expert opinion

### Artwork Authentication Panel

On `/artwork/{id}` - Authentication tab:

1. **Status Header**
   - Current status badge
   - Authentication date
   - Authenticated by

2. **Expert Opinions Section**
   - List of opinions with details
   - Add opinion button
   - Each opinion shows:
     - Expert info
     - Opinion verdict
     - Confidence level
     - Reasoning (expandable)

3. **Documents Section**
   - Document list with icons
   - Upload button
   - Preview/download links

4. **Actions Panel**
   - "Submit for Review" (if unreviewed)
   - "Set Status" dropdown
   - "Generate Certificate" (if authenticated)

### Add Expert Opinion Modal

**Fields:**
- Expert name (required)
- Title/position
- Institution
- Email
- Opinion date
- Opinion verdict (dropdown)
- Confidence level (dropdown)
- Reasoning (textarea)
- Conditions (if conditional)
- Upload supporting document (optional)

### Upload Document Modal

**Fields:**
- File upload
- Document type (dropdown)
- Title
- Link to expert opinion (dropdown, optional)
- Notes

### Authentication Certificate Page

Location: `/artwork/{id}/certificate`

**Layout:**
- Formal certificate design
- Artwork image
- Authentication details
- Expert opinions summary
- Date and signature area
- Print/Download buttons

## Implementation Steps

### Step 1: Database Migration

```python
# scripts/migrations/009_authentication_workflow.py
"""
Migration: Authentication Workflow
Date: YYYY-MM-DD
"""
import sqlite3
from pathlib import Path

def migrate():
    db_path = Path("data/artworks.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Add columns to artworks
    artwork_columns = [
        ("authentication_status", "TEXT DEFAULT 'unreviewed'"),
        ("authentication_date", "DATETIME"),
        ("authenticated_by_id", "INTEGER REFERENCES users(id)"),
        ("authentication_notes", "TEXT"),
    ]

    cursor.execute("PRAGMA table_info(artworks)")
    existing = [col[1] for col in cursor.fetchall()]

    for col_name, col_def in artwork_columns:
        if col_name not in existing:
            cursor.execute(f"ALTER TABLE artworks ADD COLUMN {col_name} {col_def}")
            print(f"Added {col_name} to artworks")

    # Create expert_opinions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expert_opinions (
            id INTEGER PRIMARY KEY,
            artwork_id INTEGER NOT NULL REFERENCES artworks(id) ON DELETE CASCADE,
            expert_name TEXT NOT NULL,
            expert_title TEXT,
            expert_institution TEXT,
            expert_email TEXT,
            opinion_date DATETIME NOT NULL,
            opinion TEXT NOT NULL,
            confidence_level TEXT,
            reasoning TEXT,
            conditions TEXT,
            document_url TEXT,
            created_by_id INTEGER REFERENCES users(id),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create authentication_documents table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS authentication_documents (
            id INTEGER PRIMARY KEY,
            artwork_id INTEGER NOT NULL REFERENCES artworks(id) ON DELETE CASCADE,
            expert_opinion_id INTEGER REFERENCES expert_opinions(id),
            document_type TEXT NOT NULL,
            title TEXT NOT NULL,
            file_path TEXT,
            url TEXT,
            notes TEXT,
            uploaded_by_id INTEGER REFERENCES users(id),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_expert_opinions_artwork ON expert_opinions(artwork_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_auth_docs_artwork ON authentication_documents(artwork_id)")

    conn.commit()
    conn.close()
    print("Migration completed successfully")

if __name__ == "__main__":
    migrate()
```

### Step 2: Update Models

Add to `src/database/models.py`:
- `AuthenticationStatus`, `ExpertOpinion`, `ConfidenceLevel`, `DocumentType` enums
- `ExpertOpinion` model (rename to avoid confusion with enum)
- `AuthenticationDocument` model
- Update `Artwork` with authentication columns

### Step 3: Create Authentication Service

Create `src/services/authentication_service.py`:

```python
from typing import Optional
from datetime import datetime

class AuthenticationService:
    """Manage artwork authentication workflow."""

    async def get_authentication(self, artwork_id: int) -> dict:
        """Get artwork authentication details."""
        pass

    async def submit_for_review(
        self,
        artwork_id: int,
        notes: str = None,
        user_id: int = None
    ) -> None:
        """Submit artwork for authentication review."""
        pass

    async def set_status(
        self,
        artwork_id: int,
        status: str,
        notes: str = None,
        conditions: str = None,
        user_id: int = None
    ) -> None:
        """Set authentication status."""
        pass

    async def add_expert_opinion(
        self,
        artwork_id: int,
        opinion_data: dict,
        user_id: int = None
    ) -> ExpertOpinion:
        """Add expert opinion."""
        pass

    async def update_expert_opinion(
        self,
        opinion_id: int,
        opinion_data: dict
    ) -> ExpertOpinion:
        """Update expert opinion."""
        pass

    async def delete_expert_opinion(self, opinion_id: int) -> None:
        """Delete expert opinion."""
        pass

    async def upload_document(
        self,
        artwork_id: int,
        file_path: str,
        document_data: dict,
        user_id: int = None
    ) -> AuthenticationDocument:
        """Upload authentication document."""
        pass

    async def delete_document(self, document_id: int) -> None:
        """Delete document."""
        pass

    async def get_dashboard(self) -> dict:
        """Get authentication dashboard stats."""
        pass

    async def get_review_queue(
        self,
        limit: int = 50,
        offset: int = 0
    ) -> dict:
        """Get artworks awaiting review."""
        pass

    async def generate_certificate(
        self,
        artwork_id: int,
        format: str = 'pdf'
    ) -> bytes:
        """Generate authentication certificate."""
        pass

    def _generate_certificate_html(self, artwork: dict) -> str:
        """Generate certificate HTML."""
        pass

    def _convert_to_pdf(self, html: str) -> bytes:
        """Convert HTML to PDF."""
        pass
```

### Step 4: Create API Routes

Create `src/api/routes/authentication.py`:

```python
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

router = APIRouter(prefix="/api", tags=["authentication"])

class ExpertOpinionCreate(BaseModel):
    expert_name: str
    expert_title: Optional[str] = None
    expert_institution: Optional[str] = None
    expert_email: Optional[str] = None
    opinion_date: datetime
    opinion: str
    confidence_level: Optional[str] = None
    reasoning: Optional[str] = None
    conditions: Optional[str] = None

class SetStatusRequest(BaseModel):
    status: str
    notes: Optional[str] = None
    conditions: Optional[str] = None

@router.get("/artworks/{id}/authentication")
async def get_authentication(id: int):
    pass

@router.post("/artworks/{id}/authentication/submit-for-review")
async def submit_for_review(id: int, notes: Optional[str] = None, user = Depends(get_current_user)):
    pass

@router.post("/artworks/{id}/authentication/set-status")
async def set_status(id: int, request: SetStatusRequest, user = Depends(require_editor)):
    pass

@router.post("/artworks/{id}/expert-opinions")
async def add_expert_opinion(id: int, opinion: ExpertOpinionCreate, user = Depends(require_editor)):
    pass

@router.get("/artworks/{id}/expert-opinions")
async def list_expert_opinions(id: int):
    pass

@router.patch("/expert-opinions/{id}")
async def update_expert_opinion(id: int, opinion: ExpertOpinionCreate, user = Depends(require_editor)):
    pass

@router.delete("/expert-opinions/{id}")
async def delete_expert_opinion(id: int, user = Depends(require_admin)):
    pass

@router.post("/artworks/{id}/authentication/documents")
async def upload_document(
    id: int,
    file: UploadFile = File(...),
    document_type: str = None,
    title: str = None,
    expert_opinion_id: Optional[int] = None,
    notes: Optional[str] = None,
    user = Depends(require_editor)
):
    pass

@router.get("/artworks/{id}/authentication/documents")
async def list_documents(id: int):
    pass

@router.delete("/authentication/documents/{id}")
async def delete_document(id: int, user = Depends(require_admin)):
    pass

@router.get("/artworks/{id}/authentication/certificate")
async def get_certificate(id: int, format: str = "pdf"):
    pass

@router.get("/authentication/dashboard")
async def get_dashboard():
    pass

@router.get("/authentication/queue")
async def get_queue(limit: int = 50, offset: int = 0):
    pass
```

### Step 5: Create Templates

Create `src/api/templates/authentication-dashboard.html`
Create `src/api/templates/authentication-certificate.html`
Update `src/api/templates/artwork.html` - Add Authentication tab

### Step 6: Add JavaScript

Create `src/api/static/js/authentication.js`:
- Status changes
- Expert opinion modal
- Document upload
- Certificate generation

## Testing Requirements

### Unit Tests

```python
# tests/test_authentication_service.py

def test_submit_for_review():
    """Status changes to under_review."""

def test_set_authenticated():
    """Can set authenticated status."""

def test_add_expert_opinion():
    """Opinion adds correctly."""

def test_get_dashboard():
    """Dashboard returns correct counts."""

def test_certificate_generation():
    """Certificate generates correctly."""
```

### Integration Tests

```python
# tests/test_authentication_api.py

def test_submit_for_review():
    """POST changes status."""

def test_add_opinion():
    """POST creates opinion."""

def test_upload_document():
    """POST uploads document."""

def test_set_status():
    """Status change works."""

def test_get_certificate():
    """Certificate returns PDF."""
```

### Manual Testing Checklist

- [ ] View authentication dashboard
- [ ] Submit artwork for review
- [ ] Add expert opinion
- [ ] Edit expert opinion
- [ ] Upload authentication document
- [ ] Set status to authenticated
- [ ] Set conditional authentication
- [ ] Generate certificate PDF
- [ ] View review queue
- [ ] Filter by authentication status

## Edge Cases

1. **Missing Expert Info**: Allow partial expert information
2. **Status Rollback**: Allow reverting status with audit
3. **Multiple Opinions**: Aggregate confidence levels
4. **Conflicting Opinions**: Highlight disagreements
5. **Large Documents**: Limit file size, compress
6. **Certificate Without Image**: Handle gracefully

## Dependencies

- `weasyprint` or `reportlab` - PDF generation
- File storage for documents

```bash
pip install weasyprint
```

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `scripts/migrations/009_authentication.py` | Create | Database migration |
| `src/database/models.py` | Modify | Add enums and models |
| `src/services/authentication_service.py` | Create | Business logic |
| `src/api/routes/authentication.py` | Create | API endpoints |
| `src/api/main.py` | Modify | Register routes |
| `src/api/templates/authentication-dashboard.html` | Create | Dashboard |
| `src/api/templates/authentication-certificate.html` | Create | Certificate template |
| `src/api/templates/artwork.html` | Modify | Add Authentication tab |
| `src/api/static/js/authentication.js` | Create | Client logic |
| `tests/test_authentication_service.py` | Create | Unit tests |
| `tests/test_authentication_api.py` | Create | API tests |

---

*Last updated: December 5, 2025*
