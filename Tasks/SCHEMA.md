# Atelier Master Schema Reference

This document defines all database schemas for Atelier features. **ALL implementations must follow these schemas exactly** to ensure consistency across development sessions.

## Table of Contents

1. [Existing Schema (Current)](#existing-schema-current)
2. [Phase 1: Foundation](#phase-1-foundation)
3. [Phase 2: Professional](#phase-2-professional)
4. [Phase 3: Collaboration](#phase-3-collaboration)
5. [Phase 4: Discovery](#phase-4-discovery)
6. [Enum Definitions](#enum-definitions)
7. [Migration Guidelines](#migration-guidelines)

---

## Existing Schema (Current)

These tables already exist in `src/database/models.py`. Do not recreate them.

### Existing Tables

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `artworks` | Core artwork records | id, title, source_url, confidence_score, is_verified |
| `artwork_images` | Images per artwork | artwork_id, url, local_path, is_primary |
| `artists` | Artist biographical data | name, birth_year, death_year, biography |
| `exhibitions` | Exhibition records | artist_id, year, venue_name, is_solo |
| `artwork_exhibitions` | Artwork-Exhibition junction | artwork_id, exhibition_id |
| `contacts` | Outreach contacts | name, organization, email, contact_type |
| `outreach` | Communication records | contact_id, outreach_type, status |
| `research_leads` | Research lead tracking | title, category, priority, status |
| `saved_searches` | Alert search configs | name, query, platform, is_active |
| `alert_results` | Search alert results | search_id, title, source_url, status |
| `notifications` | Notification history | artwork_id, channel, sent_at |
| `search_filters` | Confidence filter rules | filter_type, pattern, weight |

### Existing Enums

```python
# In src/database/models.py
class AcquisitionStatus(str, Enum):
    NEW = "new"
    WATCHING = "watching"
    CONTACTED = "contacted"
    ACQUIRED = "acquired"
    PASSED = "passed"
    UNAVAILABLE = "unavailable"

class SourcePlatform(str, Enum):
    EBAY = "ebay"
    ETSY = "etsy"
    LIVEAUCTIONEERS = "liveauctioneers"
    INVALUABLE = "invaluable"
    # ... etc
```

---

## Phase 1: Foundation

### 1.1 Enhanced Image Management

**Modify existing `artwork_images` table** - Add columns:

```python
class ArtworkImage(Base):
    __tablename__ = "artwork_images"

    # Existing columns
    id: Mapped[int] = mapped_column(primary_key=True)
    artwork_id: Mapped[int] = mapped_column(ForeignKey("artworks.id"))
    url: Mapped[str] = mapped_column(Text)
    local_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_primary: Mapped[bool] = mapped_column(default=False)
    width: Mapped[Optional[int]] = mapped_column(nullable=True)
    height: Mapped[Optional[int]] = mapped_column(nullable=True)
    date_downloaded: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # NEW COLUMNS
    image_type: Mapped[str] = mapped_column(default=ImageType.GENERAL.value)  # See enum below
    sort_order: Mapped[int] = mapped_column(default=0)  # For manual ordering
    caption: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_attribution: Mapped[Optional[str]] = mapped_column(nullable=True)  # "Photo: Susan Powell Fine Art"
    date_taken: Mapped[Optional[datetime]] = mapped_column(nullable=True)  # When photo was taken
    perceptual_hash: Mapped[Optional[str]] = mapped_column(nullable=True)  # For duplicate detection
```

**NEW TABLE: `image_annotations`**

```python
class ImageAnnotation(Base):
    """Annotations/markups on images (signature locations, damage, etc.)"""
    __tablename__ = "image_annotations"

    id: Mapped[int] = mapped_column(primary_key=True)
    image_id: Mapped[int] = mapped_column(ForeignKey("artwork_images.id"))

    # Position (percentage of image dimensions for responsiveness)
    x_percent: Mapped[float] = mapped_column()  # 0.0 to 100.0
    y_percent: Mapped[float] = mapped_column()
    width_percent: Mapped[Optional[float]] = mapped_column(nullable=True)  # For rectangles
    height_percent: Mapped[Optional[float]] = mapped_column(nullable=True)

    # Annotation details
    annotation_type: Mapped[str] = mapped_column()  # See AnnotationType enum
    label: Mapped[str] = mapped_column()  # Display label
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    color: Mapped[str] = mapped_column(default="#FFD700")  # Hex color for display

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Relationship
    image: Mapped["ArtworkImage"] = relationship(back_populates="annotations")
```

### 1.2 Import/Migration Tools

**NEW TABLE: `import_jobs`**

```python
class ImportJob(Base):
    """Tracks import operations for auditing and rollback."""
    __tablename__ = "import_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Job info
    name: Mapped[str] = mapped_column()  # User-provided name
    source_type: Mapped[str] = mapped_column()  # csv, json, excel, system
    source_file: Mapped[Optional[str]] = mapped_column(nullable=True)  # Original filename

    # Status
    status: Mapped[str] = mapped_column(default=ImportStatus.PENDING.value)

    # Results
    total_rows: Mapped[int] = mapped_column(default=0)
    imported_count: Mapped[int] = mapped_column(default=0)
    skipped_count: Mapped[int] = mapped_column(default=0)
    error_count: Mapped[int] = mapped_column(default=0)

    # Mapping configuration (JSON)
    field_mapping: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Error details
    errors: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Row-by-row errors

    # Timestamps
    started_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Relationships
    imported_artworks: Mapped[list["ImportedArtwork"]] = relationship(back_populates="import_job")
```

**NEW TABLE: `imported_artworks`**

```python
class ImportedArtwork(Base):
    """Links imported artworks to their import job for tracking/rollback."""
    __tablename__ = "imported_artworks"

    id: Mapped[int] = mapped_column(primary_key=True)
    import_job_id: Mapped[int] = mapped_column(ForeignKey("import_jobs.id"))
    artwork_id: Mapped[int] = mapped_column(ForeignKey("artworks.id"))
    source_row: Mapped[Optional[int]] = mapped_column(nullable=True)  # Row number in source file

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Relationships
    import_job: Mapped["ImportJob"] = relationship(back_populates="imported_artworks")
    artwork: Mapped["Artwork"] = relationship()
```

### 1.3 Duplicate Detection

**NEW TABLE: `duplicate_candidates`**

```python
class DuplicateCandidate(Base):
    """Potential duplicate artwork pairs for review."""
    __tablename__ = "duplicate_candidates"

    id: Mapped[int] = mapped_column(primary_key=True)

    # The two potentially duplicate artworks
    artwork_id_1: Mapped[int] = mapped_column(ForeignKey("artworks.id"))
    artwork_id_2: Mapped[int] = mapped_column(ForeignKey("artworks.id"))

    # Detection method and confidence
    detection_method: Mapped[str] = mapped_column()  # image_hash, title_similarity, etc.
    confidence_score: Mapped[float] = mapped_column()  # 0.0 to 1.0

    # Status
    status: Mapped[str] = mapped_column(default=DuplicateStatus.PENDING.value)
    resolution: Mapped[Optional[str]] = mapped_column(nullable=True)  # merged, not_duplicate, etc.

    # If merged, which artwork survived
    merged_into_id: Mapped[Optional[int]] = mapped_column(ForeignKey("artworks.id"), nullable=True)

    # Timestamps
    detected_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # Relationships
    artwork_1: Mapped["Artwork"] = relationship(foreign_keys=[artwork_id_1])
    artwork_2: Mapped["Artwork"] = relationship(foreign_keys=[artwork_id_2])
```

---

## Phase 2: Professional

### 2.1 Provenance Chain Builder

**NEW TABLE: `provenance_entries`**

```python
class ProvenanceEntry(Base):
    """Individual entries in an artwork's ownership chain."""
    __tablename__ = "provenance_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    artwork_id: Mapped[int] = mapped_column(ForeignKey("artworks.id"))

    # Sequence in the chain (1 = earliest known)
    sequence_order: Mapped[int] = mapped_column()

    # Owner/Holder information
    owner_name: Mapped[str] = mapped_column()  # Person, gallery, institution
    owner_type: Mapped[str] = mapped_column(default=OwnerType.PRIVATE.value)
    owner_location: Mapped[Optional[str]] = mapped_column(nullable=True)  # City, State/Country

    # Dating
    date_acquired: Mapped[Optional[str]] = mapped_column(nullable=True)  # Can be "c. 1985" or "1985-1990"
    date_acquired_precision: Mapped[str] = mapped_column(default=DatePrecision.UNKNOWN.value)
    date_departed: Mapped[Optional[str]] = mapped_column(nullable=True)
    date_departed_precision: Mapped[str] = mapped_column(default=DatePrecision.UNKNOWN.value)

    # How acquired
    acquisition_method: Mapped[str] = mapped_column(default=AcquisitionMethod.UNKNOWN.value)

    # Sale details (if applicable)
    sale_venue: Mapped[Optional[str]] = mapped_column(nullable=True)  # "Christie's", "Susan Powell Fine Art"
    sale_lot_number: Mapped[Optional[str]] = mapped_column(nullable=True)
    sale_price: Mapped[Optional[float]] = mapped_column(nullable=True)
    sale_currency: Mapped[str] = mapped_column(default="USD")

    # Documentation
    source_citation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Where we learned this
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_verified: Mapped[bool] = mapped_column(default=False)

    # Flags for gaps/uncertainty
    is_gap: Mapped[bool] = mapped_column(default=False)  # Unknown ownership period

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    artwork: Mapped["Artwork"] = relationship(back_populates="provenance_entries")
```

**NEW TABLE: `known_owners`**

```python
class KnownOwner(Base):
    """Database of known collectors, dealers, institutions for linking."""
    __tablename__ = "known_owners"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column()
    owner_type: Mapped[str] = mapped_column()

    # Details
    location: Mapped[Optional[str]] = mapped_column(nullable=True)
    active_years: Mapped[Optional[str]] = mapped_column(nullable=True)  # "1970-2000"
    website: Mapped[Optional[str]] = mapped_column(nullable=True)

    # Notes
    biography: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
```

### 2.2 Literature & Bibliography

**NEW TABLE: `publications`**

```python
class Publication(Base):
    """Books, articles, exhibition catalogs referencing artworks."""
    __tablename__ = "publications"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Basic info
    title: Mapped[str] = mapped_column(Text)
    publication_type: Mapped[str] = mapped_column()  # See PublicationType enum

    # Authors (comma-separated or use separate author table)
    authors: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    editors: Mapped[Optional[str]] = mapped_column(nullable=True)

    # Publication details
    publisher: Mapped[Optional[str]] = mapped_column(nullable=True)
    publication_year: Mapped[Optional[int]] = mapped_column(nullable=True)
    publication_location: Mapped[Optional[str]] = mapped_column(nullable=True)  # City

    # Identifiers
    isbn: Mapped[Optional[str]] = mapped_column(nullable=True)
    issn: Mapped[Optional[str]] = mapped_column(nullable=True)
    doi: Mapped[Optional[str]] = mapped_column(nullable=True)

    # For articles/chapters
    journal_name: Mapped[Optional[str]] = mapped_column(nullable=True)
    volume: Mapped[Optional[str]] = mapped_column(nullable=True)
    issue: Mapped[Optional[str]] = mapped_column(nullable=True)
    pages: Mapped[Optional[str]] = mapped_column(nullable=True)  # "45-67"

    # For exhibition catalogs
    exhibition_id: Mapped[Optional[int]] = mapped_column(ForeignKey("exhibitions.id"), nullable=True)

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Link to publication

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    artwork_citations: Mapped[list["ArtworkCitation"]] = relationship(back_populates="publication")
    exhibition: Mapped[Optional["Exhibition"]] = relationship()
```

**NEW TABLE: `artwork_citations`**

```python
class ArtworkCitation(Base):
    """Links artworks to publications with citation details."""
    __tablename__ = "artwork_citations"

    id: Mapped[int] = mapped_column(primary_key=True)
    artwork_id: Mapped[int] = mapped_column(ForeignKey("artworks.id"))
    publication_id: Mapped[int] = mapped_column(ForeignKey("publications.id"))

    # Citation details
    page_numbers: Mapped[Optional[str]] = mapped_column(nullable=True)  # "45, 67, 89"
    plate_number: Mapped[Optional[str]] = mapped_column(nullable=True)  # "Plate XII"
    figure_number: Mapped[Optional[str]] = mapped_column(nullable=True)  # "Fig. 23"
    catalog_number: Mapped[Optional[str]] = mapped_column(nullable=True)  # In exhibition catalog

    # Type of citation
    citation_type: Mapped[str] = mapped_column(default=CitationType.MENTIONED.value)

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Relationships
    artwork: Mapped["Artwork"] = relationship(back_populates="citations")
    publication: Mapped["Publication"] = relationship(back_populates="artwork_citations")
```

### 2.3 Catalog Numbering

**NEW TABLE: `catalog_schemes`**

```python
class CatalogScheme(Base):
    """Defines catalog numbering schemes."""
    __tablename__ = "catalog_schemes"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column()  # "Dan Brown Catalogue Raisonné"
    prefix: Mapped[str] = mapped_column(default="")  # "DB-"

    # Numbering configuration
    number_format: Mapped[str] = mapped_column(default="{prefix}{number:04d}")  # Python format string
    next_number: Mapped[int] = mapped_column(default=1)

    # Options
    include_year: Mapped[bool] = mapped_column(default=False)
    include_medium_code: Mapped[bool] = mapped_column(default=False)

    # Medium codes (JSON mapping)
    medium_codes: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    # e.g., {"Painting": "P", "Drawing": "D", "Print": "PR"}

    is_default: Mapped[bool] = mapped_column(default=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
```

**Add to Artwork model:**

```python
# In Artwork class
catalog_number: Mapped[Optional[str]] = mapped_column(nullable=True, unique=True)
catalog_scheme_id: Mapped[Optional[int]] = mapped_column(ForeignKey("catalog_schemes.id"), nullable=True)
```

### 2.4 Related Works

**NEW TABLE: `related_artworks`**

```python
class RelatedArtwork(Base):
    """Relationships between artworks (study/finished, series, variants)."""
    __tablename__ = "related_artworks"

    id: Mapped[int] = mapped_column(primary_key=True)

    artwork_id_1: Mapped[int] = mapped_column(ForeignKey("artworks.id"))
    artwork_id_2: Mapped[int] = mapped_column(ForeignKey("artworks.id"))

    relationship_type: Mapped[str] = mapped_column()  # See RelationshipType enum

    # Direction matters for some relationships
    # artwork_1 is the "source" (e.g., the study)
    # artwork_2 is the "target" (e.g., the finished work)

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Relationships
    artwork_1: Mapped["Artwork"] = relationship(foreign_keys=[artwork_id_1])
    artwork_2: Mapped["Artwork"] = relationship(foreign_keys=[artwork_id_2])
```

---

## Phase 3: Collaboration

### 3.1 Multi-User Support

**NEW TABLE: `users`**

```python
class User(Base):
    """Application users."""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Identity
    email: Mapped[str] = mapped_column(unique=True)
    username: Mapped[str] = mapped_column(unique=True)
    display_name: Mapped[Optional[str]] = mapped_column(nullable=True)

    # Authentication
    password_hash: Mapped[str] = mapped_column()
    is_active: Mapped[bool] = mapped_column(default=True)

    # Role
    role: Mapped[str] = mapped_column(default=UserRole.VIEWER.value)

    # Profile
    avatar_url: Mapped[Optional[str]] = mapped_column(nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    last_login: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # Relationships
    activity_logs: Mapped[list["ActivityLog"]] = relationship(back_populates="user")
    comments: Mapped[list["ArtworkComment"]] = relationship(back_populates="user")
```

**NEW TABLE: `activity_log`**

```python
class ActivityLog(Base):
    """Audit trail of user actions."""
    __tablename__ = "activity_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)

    # What happened
    action: Mapped[str] = mapped_column()  # create, update, delete, verify, etc.
    entity_type: Mapped[str] = mapped_column()  # artwork, exhibition, etc.
    entity_id: Mapped[int] = mapped_column()

    # Details
    changes: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Before/after values
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Context
    ip_address: Mapped[Optional[str]] = mapped_column(nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(nullable=True)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Relationship
    user: Mapped[Optional["User"]] = relationship(back_populates="activity_logs")
```

**NEW TABLE: `artwork_comments`**

```python
class ArtworkComment(Base):
    """Comments/discussions on artworks."""
    __tablename__ = "artwork_comments"

    id: Mapped[int] = mapped_column(primary_key=True)
    artwork_id: Mapped[int] = mapped_column(ForeignKey("artworks.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    # Comment content
    content: Mapped[str] = mapped_column(Text)

    # Threading (for replies)
    parent_comment_id: Mapped[Optional[int]] = mapped_column(ForeignKey("artwork_comments.id"), nullable=True)

    # Status
    is_resolved: Mapped[bool] = mapped_column(default=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    artwork: Mapped["Artwork"] = relationship(back_populates="comments")
    user: Mapped["User"] = relationship(back_populates="comments")
    replies: Mapped[list["ArtworkComment"]] = relationship()
```

### 3.2 Authentication Workflow

**Modify `artworks` table** - Add columns:

```python
# Add to Artwork class
authentication_status: Mapped[str] = mapped_column(default=AuthenticationStatus.UNREVIEWED.value)
authentication_date: Mapped[Optional[datetime]] = mapped_column(nullable=True)
authenticated_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
```

**NEW TABLE: `expert_opinions`**

```python
class ExpertOpinion(Base):
    """Expert authentication opinions on artworks."""
    __tablename__ = "expert_opinions"

    id: Mapped[int] = mapped_column(primary_key=True)
    artwork_id: Mapped[int] = mapped_column(ForeignKey("artworks.id"))

    # Expert info
    expert_name: Mapped[str] = mapped_column()
    expert_title: Mapped[Optional[str]] = mapped_column(nullable=True)  # "Professor of Art History"
    expert_institution: Mapped[Optional[str]] = mapped_column(nullable=True)

    # Opinion
    opinion_date: Mapped[datetime] = mapped_column()
    opinion: Mapped[str] = mapped_column()  # authenticated, rejected, uncertain
    confidence_level: Mapped[Optional[str]] = mapped_column(nullable=True)  # high, medium, low

    # Details
    reasoning: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    conditions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # "Subject to cleaning"

    # Documentation
    document_url: Mapped[Optional[str]] = mapped_column(nullable=True)  # Scanned letter, etc.

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Relationship
    artwork: Mapped["Artwork"] = relationship(back_populates="expert_opinions")
```

### 3.3 Public Tip Submission

**NEW TABLE: `tip_submissions`**

```python
class TipSubmission(Base):
    """Public submissions of potential artworks."""
    __tablename__ = "tip_submissions"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Submitter info
    submitter_name: Mapped[str] = mapped_column()
    submitter_email: Mapped[str] = mapped_column()
    submitter_phone: Mapped[Optional[str]] = mapped_column(nullable=True)
    submitter_location: Mapped[Optional[str]] = mapped_column(nullable=True)

    # Artwork info provided
    artwork_title: Mapped[Optional[str]] = mapped_column(nullable=True)
    artwork_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    artwork_medium: Mapped[Optional[str]] = mapped_column(nullable=True)
    artwork_dimensions: Mapped[Optional[str]] = mapped_column(nullable=True)

    # Ownership/provenance claimed
    ownership_status: Mapped[Optional[str]] = mapped_column(nullable=True)  # "I own it", "I saw it for sale"
    provenance_info: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Images (JSON array of URLs or stored paths)
    images: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Additional info
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Status tracking
    status: Mapped[str] = mapped_column(default=TipStatus.NEW.value)
    priority: Mapped[str] = mapped_column(default=LeadPriority.MEDIUM.value)

    # If converted to research lead or artwork
    converted_to_lead_id: Mapped[Optional[int]] = mapped_column(ForeignKey("research_leads.id"), nullable=True)
    converted_to_artwork_id: Mapped[Optional[int]] = mapped_column(ForeignKey("artworks.id"), nullable=True)

    # Admin notes
    internal_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    submitted_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # Relationships
    converted_lead: Mapped[Optional["ResearchLead"]] = relationship()
    converted_artwork: Mapped[Optional["Artwork"]] = relationship()
```

---

## Phase 4: Discovery

### 4.1 Auction House Integration

**NEW TABLE: `auction_houses`**

```python
class AuctionHouse(Base):
    """Registry of auction houses for integration."""
    __tablename__ = "auction_houses"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column()  # "Christie's", "Sotheby's"
    code: Mapped[str] = mapped_column(unique=True)  # "christies", "sothebys"

    # Integration status
    is_active: Mapped[bool] = mapped_column(default=True)
    has_api: Mapped[bool] = mapped_column(default=False)
    scraper_class: Mapped[Optional[str]] = mapped_column(nullable=True)  # Python class name

    # Contact/Website
    website: Mapped[Optional[str]] = mapped_column(nullable=True)
    api_base_url: Mapped[Optional[str]] = mapped_column(nullable=True)

    # Rate limiting
    requests_per_minute: Mapped[int] = mapped_column(default=10)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
```

**NEW TABLE: `auction_results`**

```python
class AuctionResult(Base):
    """Historical auction results."""
    __tablename__ = "auction_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    artwork_id: Mapped[Optional[int]] = mapped_column(ForeignKey("artworks.id"), nullable=True)
    auction_house_id: Mapped[int] = mapped_column(ForeignKey("auction_houses.id"))

    # Sale info
    sale_name: Mapped[Optional[str]] = mapped_column(nullable=True)  # "American Art"
    sale_date: Mapped[datetime] = mapped_column()
    lot_number: Mapped[Optional[str]] = mapped_column(nullable=True)

    # Listing as appeared
    listing_title: Mapped[str] = mapped_column(Text)
    listing_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Estimates and result
    estimate_low: Mapped[Optional[float]] = mapped_column(nullable=True)
    estimate_high: Mapped[Optional[float]] = mapped_column(nullable=True)
    hammer_price: Mapped[Optional[float]] = mapped_column(nullable=True)
    premium_price: Mapped[Optional[float]] = mapped_column(nullable=True)  # Including buyer's premium
    currency: Mapped[str] = mapped_column(default="USD")

    # Status
    was_sold: Mapped[bool] = mapped_column(default=True)
    was_bought_in: Mapped[bool] = mapped_column(default=False)

    # Source
    source_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Relationships
    artwork: Mapped[Optional["Artwork"]] = relationship(back_populates="auction_results")
    auction_house: Mapped["AuctionHouse"] = relationship()
```

### 4.2 Museum Collections

**NEW TABLE: `institutions`**

```python
class Institution(Base):
    """Museums, libraries, and other institutions."""
    __tablename__ = "institutions"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column()
    institution_type: Mapped[str] = mapped_column()  # museum, library, archive, etc.

    # Location
    city: Mapped[Optional[str]] = mapped_column(nullable=True)
    state: Mapped[Optional[str]] = mapped_column(nullable=True)
    country: Mapped[str] = mapped_column(default="USA")

    # Contact
    website: Mapped[Optional[str]] = mapped_column(nullable=True)
    collections_url: Mapped[Optional[str]] = mapped_column(nullable=True)  # Online collection URL
    contact_email: Mapped[Optional[str]] = mapped_column(nullable=True)

    # API integration
    has_api: Mapped[bool] = mapped_column(default=False)
    api_base_url: Mapped[Optional[str]] = mapped_column(nullable=True)

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
```

**NEW TABLE: `institution_holdings`**

```python
class InstitutionHolding(Base):
    """Artworks held by institutions."""
    __tablename__ = "institution_holdings"

    id: Mapped[int] = mapped_column(primary_key=True)
    artwork_id: Mapped[int] = mapped_column(ForeignKey("artworks.id"))
    institution_id: Mapped[int] = mapped_column(ForeignKey("institutions.id"))

    # Accession info
    accession_number: Mapped[Optional[str]] = mapped_column(nullable=True)
    department: Mapped[Optional[str]] = mapped_column(nullable=True)

    # Acquisition
    date_acquired: Mapped[Optional[str]] = mapped_column(nullable=True)
    acquisition_method: Mapped[Optional[str]] = mapped_column(nullable=True)  # gift, purchase, bequest
    donor: Mapped[Optional[str]] = mapped_column(nullable=True)

    # Display status
    is_on_view: Mapped[bool] = mapped_column(default=False)
    gallery_location: Mapped[Optional[str]] = mapped_column(nullable=True)

    # Online collection link
    collection_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    artwork: Mapped["Artwork"] = relationship(back_populates="institution_holdings")
    institution: Mapped["Institution"] = relationship()
```

---

## Enum Definitions

Add these to `src/database/models.py`:

```python
# Phase 1 Enums
class ImageType(str, Enum):
    GENERAL = "general"
    FRONT = "front"           # Recto/main view
    BACK = "back"             # Verso
    SIGNATURE = "signature"   # Signature detail
    DETAIL = "detail"         # Other detail
    FRAME = "frame"           # Frame view
    UV = "uv"                 # UV photography
    IR = "ir"                 # Infrared
    XRAY = "xray"             # X-ray
    INSTALLATION = "installation"  # Installation view

class AnnotationType(str, Enum):
    SIGNATURE = "signature"
    INSCRIPTION = "inscription"
    DAMAGE = "damage"
    RESTORATION = "restoration"
    LABEL = "label"
    STAMP = "stamp"
    GENERAL = "general"

class ImportStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class DuplicateStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED_DUPLICATE = "confirmed_duplicate"
    NOT_DUPLICATE = "not_duplicate"
    MERGED = "merged"
    IGNORED = "ignored"

# Phase 2 Enums
class OwnerType(str, Enum):
    ARTIST = "artist"
    ESTATE = "estate"
    PRIVATE = "private"
    GALLERY = "gallery"
    AUCTION_HOUSE = "auction_house"
    MUSEUM = "museum"
    INSTITUTION = "institution"
    CORPORATE = "corporate"
    UNKNOWN = "unknown"

class DatePrecision(str, Enum):
    EXACT = "exact"           # Known exact date
    YEAR = "year"             # Known year only
    CIRCA = "circa"           # Approximate
    DECADE = "decade"         # "1980s"
    RANGE = "range"           # "1985-1990"
    UNKNOWN = "unknown"

class AcquisitionMethod(str, Enum):
    UNKNOWN = "unknown"
    CREATED = "created"       # Artist created it
    INHERITED = "inherited"
    GIFTED = "gifted"
    PURCHASED = "purchased"
    AUCTION = "auction"
    CONSIGNMENT = "consignment"
    COMMISSION = "commission"
    BEQUEST = "bequest"
    EXCHANGE = "exchange"

class PublicationType(str, Enum):
    BOOK = "book"
    ARTICLE = "article"
    EXHIBITION_CATALOG = "exhibition_catalog"
    AUCTION_CATALOG = "auction_catalog"
    MONOGRAPH = "monograph"
    MAGAZINE = "magazine"
    NEWSPAPER = "newspaper"
    WEBSITE = "website"
    THESIS = "thesis"
    OTHER = "other"

class CitationType(str, Enum):
    ILLUSTRATED = "illustrated"    # Image reproduced
    MENTIONED = "mentioned"        # Text reference only
    DISCUSSED = "discussed"        # Extended discussion
    CATALOGED = "cataloged"        # In catalog listing
    COVER = "cover"                # On publication cover

class RelationshipType(str, Enum):
    STUDY_FOR = "study_for"        # artwork_1 is study for artwork_2
    VARIANT_OF = "variant_of"      # Different version
    COPY_OF = "copy_of"            # Copy by same artist
    AFTER = "after"                # Copy by different artist
    PENDANT = "pendant"            # Companion piece
    SERIES = "series"              # Part of same series
    RELATED = "related"            # General relationship

# Phase 3 Enums
class UserRole(str, Enum):
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"

class AuthenticationStatus(str, Enum):
    UNREVIEWED = "unreviewed"
    UNDER_REVIEW = "under_review"
    AUTHENTICATED = "authenticated"
    REJECTED = "rejected"
    UNCERTAIN = "uncertain"
    CONDITIONAL = "conditional"    # "Authentic if cleaned"

class TipStatus(str, Enum):
    NEW = "new"
    UNDER_REVIEW = "under_review"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    DUPLICATE = "duplicate"
    NEEDS_INFO = "needs_info"
```

---

## Migration Guidelines

### Creating a Migration Script

For each schema change, create a script in `scripts/migrations/`:

```python
# scripts/migrations/add_image_type_field.py
"""
Migration: Add image_type field to artwork_images
Date: 2025-12-05
"""
import sqlite3
from pathlib import Path

def migrate():
    db_path = Path("data/artworks.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if column exists
    cursor.execute("PRAGMA table_info(artwork_images)")
    columns = [col[1] for col in cursor.fetchall()]

    if "image_type" not in columns:
        cursor.execute("""
            ALTER TABLE artwork_images
            ADD COLUMN image_type TEXT DEFAULT 'general'
        """)
        print("Added image_type column")
    else:
        print("image_type column already exists")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    migrate()
```

### Migration Checklist

Before running a migration:

1. [ ] Backup the database: `cp data/artworks.db data/artworks.db.backup`
2. [ ] Test on a copy first
3. [ ] Handle NULL values for existing rows
4. [ ] Update models.py after migration succeeds
5. [ ] Update any affected API routes
6. [ ] Update any affected templates
7. [ ] Test existing functionality still works

### Adding New Tables

1. Add model to `src/database/models.py`
2. Create migration script to create table
3. Run migration
4. Add API routes in new file under `src/api/routes/`
5. Register routes in `src/api/main.py`
6. Create templates as needed

---

*Last updated: December 5, 2025*
