"""Database models for artwork tracking."""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import ForeignKey, Text, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


class AcquisitionStatus(str, Enum):
    """Status of artwork acquisition."""
    NEW = "new"
    WATCHING = "watching"
    CONTACTED = "contacted"
    ACQUIRED = "acquired"
    PASSED = "passed"
    UNAVAILABLE = "unavailable"


class SourcePlatform(str, Enum):
    """Platforms we monitor for artwork."""
    EBAY = "ebay"
    ETSY = "etsy"
    LIVEAUCTIONEERS = "liveauctioneers"
    INVALUABLE = "invaluable"
    AUCTIONZIP = "auctionzip"
    FIRSTDIBS = "1stdibs"
    ARTNET = "artnet"
    FACEBOOK = "facebook"
    CRAIGSLIST = "craigslist"
    ESTATESALES_NET = "estatesales_net"
    ESTATESALES_ORG = "estatesales_org"
    GOOGLE_ALERT = "google_alert"
    MANUAL = "manual"


class Artwork(Base):
    """
    Represents a discovered artwork listing.

    Each record is a potential Dan Brown artwork found during scraping.
    """
    __tablename__ = "artworks"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Basic info
    title: Mapped[str] = mapped_column(Text)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Source information
    source_platform: Mapped[str] = mapped_column()
    source_url: Mapped[str] = mapped_column(Text, unique=True)
    source_id: Mapped[Optional[str]] = mapped_column(nullable=True)  # Platform-specific ID

    # Pricing
    price: Mapped[Optional[float]] = mapped_column(nullable=True)
    currency: Mapped[str] = mapped_column(default="USD")

    # Seller/Location
    seller_name: Mapped[Optional[str]] = mapped_column(nullable=True)
    seller_id: Mapped[Optional[str]] = mapped_column(nullable=True)
    location: Mapped[Optional[str]] = mapped_column(nullable=True)

    # Dates
    date_found: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    date_listing: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    date_ending: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # Verification
    confidence_score: Mapped[float] = mapped_column(default=0.0)
    positive_signals: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    negative_signals: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    is_verified: Mapped[bool] = mapped_column(default=False)
    is_false_positive: Mapped[bool] = mapped_column(default=False)

    # Status tracking
    acquisition_status: Mapped[str] = mapped_column(default=AcquisitionStatus.NEW.value)

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ===========================================
    # Artwork Catalog Metadata (new fields)
    # ===========================================

    # Physical characteristics
    medium: Mapped[Optional[str]] = mapped_column(nullable=True)  # e.g., "Oil on panel", "Oil on canvas"
    dimensions: Mapped[Optional[str]] = mapped_column(nullable=True)  # e.g., "12 x 16 in"
    dimensions_cm: Mapped[Optional[str]] = mapped_column(nullable=True)  # e.g., "30.5 x 40.6 cm"
    art_type: Mapped[Optional[str]] = mapped_column(nullable=True)  # e.g., "Painting", "Book Cover", "Lithograph"

    # Dating
    year_created: Mapped[Optional[int]] = mapped_column(nullable=True)  # e.g., 1985
    year_created_circa: Mapped[bool] = mapped_column(default=False)  # True if year is approximate

    # Signature & inscriptions
    signed: Mapped[Optional[str]] = mapped_column(nullable=True)  # e.g., "Signed lower right"
    inscription: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Any inscriptions on the work

    # Provenance & history
    provenance: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Ownership history
    exhibition_history: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Where exhibited
    literature: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Publications featuring the work

    # Condition & framing
    condition: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Condition notes
    framed: Mapped[Optional[bool]] = mapped_column(nullable=True)  # Whether framed
    frame_description: Mapped[Optional[str]] = mapped_column(nullable=True)  # Frame details

    # Subject matter
    subject_matter: Mapped[Optional[str]] = mapped_column(nullable=True)  # What's depicted
    category: Mapped[Optional[str]] = mapped_column(nullable=True)  # e.g., "Currency", "Still Life"

    # ===========================================
    # Acquisition & Sales Tracking
    # ===========================================

    # Last known sale information
    last_sale_price: Mapped[Optional[float]] = mapped_column(nullable=True)  # Price at last sale
    last_sale_date: Mapped[Optional[datetime]] = mapped_column(nullable=True)  # Date of last sale
    last_sale_venue: Mapped[Optional[str]] = mapped_column(nullable=True)  # Where sold (auction house, gallery)

    # Current ownership/location tracking
    last_known_owner: Mapped[Optional[str]] = mapped_column(nullable=True)  # Current/last known owner
    current_location: Mapped[Optional[str]] = mapped_column(nullable=True)  # Where piece is now (city, collection)

    # Acquisition planning
    acquisition_priority: Mapped[Optional[int]] = mapped_column(nullable=True)  # 1-5 priority (5 = must have)
    acquisition_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Notes on acquisition attempts
    estimated_value: Mapped[Optional[float]] = mapped_column(nullable=True)  # Our estimated current value

    # Source URLs for tracking and research
    source_listing_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Current/active listing URL
    last_sale_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # URL of auction/sale record
    research_source_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Where we found metadata
    research_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Notes on info sources

    # ===========================================
    # Research & Collection Status (new fields)
    # ===========================================

    # Research completeness
    research_status: Mapped[Optional[str]] = mapped_column(nullable=True)  # 'complete', 'needs_image', 'needs_dimensions', 'unverified'

    # Personal collection tracking
    is_personal_collection: Mapped[bool] = mapped_column(default=False)  # In family possession
    location_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # e.g., "Living room above snake plants"

    # Special tagging
    is_personal_artifact: Mapped[bool] = mapped_column(default=False)  # Artist's personal items (hands drawings)
    emotional_significance: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Why it matters to family

    # Relationships
    images: Mapped[list["ArtworkImage"]] = relationship(back_populates="artwork", cascade="all, delete-orphan")
    notifications: Mapped[list["Notification"]] = relationship(back_populates="artwork", cascade="all, delete-orphan")
    exhibition_appearances: Mapped[list["ArtworkExhibition"]] = relationship(back_populates="artwork", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Artwork(id={self.id}, title='{self.title[:30]}...', platform={self.source_platform})>"


class ArtworkImage(Base):
    """Images associated with an artwork listing."""
    __tablename__ = "artwork_images"

    id: Mapped[int] = mapped_column(primary_key=True)
    artwork_id: Mapped[int] = mapped_column(ForeignKey("artworks.id"))

    url: Mapped[str] = mapped_column(Text)
    local_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_primary: Mapped[bool] = mapped_column(default=False)

    # Image metadata
    width: Mapped[Optional[int]] = mapped_column(nullable=True)
    height: Mapped[Optional[int]] = mapped_column(nullable=True)

    date_downloaded: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    artwork: Mapped["Artwork"] = relationship(back_populates="images")

    def __repr__(self) -> str:
        return f"<ArtworkImage(id={self.id}, artwork_id={self.artwork_id}, primary={self.is_primary})>"


class Notification(Base):
    """Record of notifications sent about artwork discoveries."""
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    artwork_id: Mapped[int] = mapped_column(ForeignKey("artworks.id"))

    channel: Mapped[str] = mapped_column()  # email, sms, push
    recipient: Mapped[str] = mapped_column()

    sent_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    status: Mapped[str] = mapped_column(default="sent")  # sent, failed, pending
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    artwork: Mapped["Artwork"] = relationship(back_populates="notifications")

    def __repr__(self) -> str:
        return f"<Notification(id={self.id}, artwork_id={self.artwork_id}, channel={self.channel})>"


class SearchFilter(Base):
    """
    Configurable search filters for identifying Dan Brown artwork.

    Allows adding/modifying positive and negative signals without code changes.
    """
    __tablename__ = "search_filters"

    id: Mapped[int] = mapped_column(primary_key=True)

    filter_type: Mapped[str] = mapped_column()  # positive, negative
    category: Mapped[str] = mapped_column()  # artist, style, gallery, location, etc.
    pattern: Mapped[str] = mapped_column(Text)  # The actual search term or regex
    weight: Mapped[float] = mapped_column(default=1.0)  # How much this affects confidence
    is_active: Mapped[bool] = mapped_column(default=True)

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<SearchFilter(id={self.id}, type={self.filter_type}, pattern='{self.pattern}')>"


class Artist(Base):
    """
    Artist biographical information.

    Primary record for Dan Brown (1949-2022), but designed to support
    tracking other artists if needed.
    """
    __tablename__ = "artists"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Basic identity
    name: Mapped[str] = mapped_column()
    birth_year: Mapped[Optional[int]] = mapped_column(nullable=True)
    death_year: Mapped[Optional[int]] = mapped_column(nullable=True)
    birth_place: Mapped[Optional[str]] = mapped_column(nullable=True)

    # Biography
    biography: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    education: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    teachers: Mapped[Optional[str]] = mapped_column(nullable=True)  # e.g., "Ken Davies, Peter Poskas"
    influences: Mapped[Optional[str]] = mapped_column(nullable=True)  # e.g., "Winslow Homer, Edward Hopper"

    # Artistic focus
    specialty: Mapped[Optional[str]] = mapped_column(nullable=True)  # e.g., "Trompe l'oeil"
    subjects: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # What they paint

    # Career highlights
    notable_collections: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    commercial_clients: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Source of information
    source_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    exhibitions: Mapped[list["Exhibition"]] = relationship(back_populates="artist", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Artist(id={self.id}, name='{self.name}', {self.birth_year}-{self.death_year})>"


class Exhibition(Base):
    """
    Exhibition history for an artist.

    Tracks gallery shows, museum exhibitions, and art fairs.
    """
    __tablename__ = "exhibitions"

    id: Mapped[int] = mapped_column(primary_key=True)
    artist_id: Mapped[Optional[int]] = mapped_column(ForeignKey("artists.id"), nullable=True)

    # Exhibition details
    year: Mapped[int] = mapped_column()
    venue_name: Mapped[str] = mapped_column()
    venue_city: Mapped[Optional[str]] = mapped_column(nullable=True)
    venue_state: Mapped[Optional[str]] = mapped_column(nullable=True)
    venue_country: Mapped[str] = mapped_column(default="USA")

    # Precise dates (optional)
    start_date: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    end_date: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # Exhibition type
    is_solo: Mapped[bool] = mapped_column(default=False)
    exhibition_type: Mapped[Optional[str]] = mapped_column(nullable=True)  # gallery, museum, art fair, etc.

    # Additional info
    title: Mapped[Optional[str]] = mapped_column(nullable=True)  # Exhibition title if named
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    curator: Mapped[Optional[str]] = mapped_column(nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Source/Research
    source_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    catalog_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    artist: Mapped[Optional["Artist"]] = relationship(back_populates="exhibitions")
    artworks_shown: Mapped[list["ArtworkExhibition"]] = relationship(back_populates="exhibition", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        solo = " (solo)" if self.is_solo else ""
        return f"<Exhibition(id={self.id}, {self.year} - {self.venue_name}{solo})>"


class ArtworkExhibition(Base):
    """
    Many-to-many relationship between artworks and exhibitions.

    Tracks which artworks were displayed at which exhibitions,
    along with optional details about each showing.
    """
    __tablename__ = "artwork_exhibitions"

    id: Mapped[int] = mapped_column(primary_key=True)
    artwork_id: Mapped[int] = mapped_column(ForeignKey("artworks.id"))
    exhibition_id: Mapped[int] = mapped_column(ForeignKey("exhibitions.id"))

    # Optional details about this specific showing
    catalog_number: Mapped[Optional[str]] = mapped_column(nullable=True)  # Exhibition catalog number
    was_sold: Mapped[bool] = mapped_column(default=False)
    sale_price: Mapped[Optional[float]] = mapped_column(nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Relationships
    artwork: Mapped["Artwork"] = relationship(back_populates="exhibition_appearances")
    exhibition: Mapped["Exhibition"] = relationship(back_populates="artworks_shown")

    def __repr__(self) -> str:
        return f"<ArtworkExhibition(artwork_id={self.artwork_id}, exhibition_id={self.exhibition_id})>"


# =============================================================================
# Outreach & Research Tracking
# =============================================================================

class OutreachStatus(str, Enum):
    """Status of an outreach attempt."""
    DRAFT = "draft"
    SENT = "sent"
    AWAITING_RESPONSE = "awaiting_response"
    RESPONDED = "responded"
    FOLLOW_UP_NEEDED = "follow_up_needed"
    CLOSED = "closed"
    NO_RESPONSE = "no_response"


class ContactType(str, Enum):
    """Type of contact/organization."""
    GALLERY = "gallery"
    AUCTION_HOUSE = "auction_house"
    MUSEUM = "museum"
    PUBLISHER = "publisher"
    EDUCATIONAL = "educational"
    GOVERNMENT = "government"
    AGENCY = "agency"
    INDIVIDUAL = "individual"
    OTHER = "other"


class OutreachType(str, Enum):
    """Type of outreach communication."""
    EMAIL = "email"
    PHONE = "phone"
    LETTER = "letter"
    IN_PERSON = "in_person"
    SOCIAL_MEDIA = "social_media"
    OTHER = "other"


class LeadStatus(str, Enum):
    """Status of a research lead."""
    NEW = "new"
    INVESTIGATING = "investigating"
    CONTACTED = "contacted"
    RESOLVED = "resolved"
    DEAD_END = "dead_end"


class LeadPriority(str, Enum):
    """Priority level for research leads."""
    HIGH = "high"          # High emotional value / confirmed connection
    MEDIUM = "medium"      # Good lead, worth pursuing
    LOW = "low"            # Speculative / low confidence


class LeadCategory(str, Enum):
    """Category of research lead."""
    PERSONAL_ARTIFACT = "personal_artifact"    # Hands drawings, family pieces
    COMMERCIAL_WORK = "commercial_work"        # Magazine, book covers, cards
    FINE_ART = "fine_art"                      # Paintings, original artwork
    PROVENANCE = "provenance"                  # Trade/barter stories, lost works
    PUBLICATION = "publication"                # Magazine, book mentions
    EXHIBITION = "exhibition"                  # Show/gallery appearances
    OTHER = "other"


class Contact(Base):
    """
    External contacts for research outreach.

    Represents organizations or individuals we contact for information,
    images, or metadata about Dan Brown's artwork.
    """
    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Basic info
    name: Mapped[str] = mapped_column()  # Person or organization name
    organization: Mapped[Optional[str]] = mapped_column(nullable=True)  # If person, their org
    contact_type: Mapped[str] = mapped_column(default=ContactType.OTHER.value)
    role: Mapped[Optional[str]] = mapped_column(nullable=True)  # e.g., "Archivist", "Gallery Owner"

    # Contact details
    email: Mapped[Optional[str]] = mapped_column(nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    website: Mapped[Optional[str]] = mapped_column(nullable=True)

    # Location
    city: Mapped[Optional[str]] = mapped_column(nullable=True)
    state: Mapped[Optional[str]] = mapped_column(nullable=True)
    country: Mapped[str] = mapped_column(default="USA")

    # Relationship to Dan Brown's work
    connection_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # How they're connected
    target_artworks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Which artworks they may have info on

    # Status
    priority: Mapped[int] = mapped_column(default=3)  # 1-5 (5 = highest priority)
    is_active: Mapped[bool] = mapped_column(default=True)

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    outreach_records: Mapped[list["Outreach"]] = relationship(back_populates="contact", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Contact(id={self.id}, name='{self.name}', type={self.contact_type})>"


class Outreach(Base):
    """
    Individual outreach communications.

    Tracks each email, call, or letter sent to contacts for research purposes.
    """
    __tablename__ = "outreach"

    id: Mapped[int] = mapped_column(primary_key=True)
    contact_id: Mapped[int] = mapped_column(ForeignKey("contacts.id"))

    # Communication type
    outreach_type: Mapped[str] = mapped_column(default=OutreachType.EMAIL.value)
    status: Mapped[str] = mapped_column(default=OutreachStatus.DRAFT.value)

    # Content
    subject: Mapped[Optional[str]] = mapped_column(nullable=True)  # Email subject or call topic
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Email body or call notes
    template_used: Mapped[Optional[str]] = mapped_column(nullable=True)  # Which template was used

    # Dates
    date_sent: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    follow_up_date: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # Response tracking
    response_received: Mapped[bool] = mapped_column(default=False)
    response_date: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    response_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    response_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Outcome
    outcome: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # What we got from this
    images_received: Mapped[bool] = mapped_column(default=False)
    metadata_received: Mapped[bool] = mapped_column(default=False)
    leads_received: Mapped[bool] = mapped_column(default=False)

    # What we're requesting
    requesting_images: Mapped[bool] = mapped_column(default=False)
    requesting_metadata: Mapped[bool] = mapped_column(default=False)
    requesting_provenance: Mapped[bool] = mapped_column(default=False)
    requesting_attribution: Mapped[bool] = mapped_column(default=False)
    request_details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Gmail tracking - for emails sent via the app
    gmail_message_id: Mapped[Optional[str]] = mapped_column(nullable=True)  # Gmail message ID
    gmail_thread_id: Mapped[Optional[str]] = mapped_column(nullable=True)   # Gmail thread ID for tracking replies

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    contact: Mapped["Contact"] = relationship(back_populates="outreach_records")

    def __repr__(self) -> str:
        return f"<Outreach(id={self.id}, contact_id={self.contact_id}, type={self.outreach_type}, status={self.status})>"


class AlertStatus(str, Enum):
    """Status of an alert result."""
    NEW = "new"                    # Just found, unreviewed
    REVIEWING = "reviewing"        # User is looking at it
    CONFIRMED = "confirmed"        # Confirmed as Dan Brown
    REJECTED = "rejected"          # Not Dan Brown / false positive
    WATCHING = "watching"          # Monitoring for price changes


class SavedSearch(Base):
    """
    Saved search configurations for recurring alert monitoring.

    Allows users to define search queries that run periodically
    to find new listings on eBay and other platforms.
    """
    __tablename__ = "saved_searches"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Search definition
    name: Mapped[str] = mapped_column()  # User-friendly name
    query: Mapped[str] = mapped_column(Text)  # The search query
    platform: Mapped[str] = mapped_column(default=SourcePlatform.EBAY.value)  # Which platform to search

    # Search options
    category: Mapped[Optional[str]] = mapped_column(nullable=True)  # eBay category (art, paintings, etc.)
    min_price: Mapped[Optional[float]] = mapped_column(nullable=True)
    max_price: Mapped[Optional[float]] = mapped_column(nullable=True)

    # Scheduling
    is_active: Mapped[bool] = mapped_column(default=True)
    run_interval_hours: Mapped[int] = mapped_column(default=24)  # How often to run
    last_run: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    next_run: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # Stats
    total_results: Mapped[int] = mapped_column(default=0)
    new_since_last_view: Mapped[int] = mapped_column(default=0)

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    results: Mapped[list["AlertResult"]] = relationship(back_populates="search", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<SavedSearch(id={self.id}, name='{self.name}', platform={self.platform})>"


class AlertResult(Base):
    """
    Results from saved search alerts.

    Each record represents a listing found by a saved search.
    Separate from Artwork to keep unverified finds in their own space.
    """
    __tablename__ = "alert_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    search_id: Mapped[int] = mapped_column(ForeignKey("saved_searches.id"))

    # Listing info
    title: Mapped[str] = mapped_column(Text)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_url: Mapped[str] = mapped_column(Text)
    source_id: Mapped[Optional[str]] = mapped_column(nullable=True)  # Platform listing ID

    # Pricing
    price: Mapped[Optional[float]] = mapped_column(nullable=True)
    currency: Mapped[str] = mapped_column(default="USD")

    # Seller/Location
    seller_name: Mapped[Optional[str]] = mapped_column(nullable=True)
    location: Mapped[Optional[str]] = mapped_column(nullable=True)

    # Image
    image_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Dates
    date_found: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    date_listing: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    date_ending: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # Status & Review
    status: Mapped[str] = mapped_column(default=AlertStatus.NEW.value)
    confidence_score: Mapped[Optional[float]] = mapped_column(nullable=True)

    # If promoted to Artwork
    promoted_to_artwork_id: Mapped[Optional[int]] = mapped_column(ForeignKey("artworks.id"), nullable=True)

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    search: Mapped["SavedSearch"] = relationship(back_populates="results")
    promoted_artwork: Mapped[Optional["Artwork"]] = relationship(foreign_keys=[promoted_to_artwork_id])

    def __repr__(self) -> str:
        return f"<AlertResult(id={self.id}, title='{self.title[:30]}', status={self.status})>"


class ResearchLead(Base):
    """
    Research leads for tracking down Dan Brown's work.

    Represents clues, rumors, and leads about potential artworks before
    they become verified entries in the Artwork table.
    """
    __tablename__ = "research_leads"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Lead description
    title: Mapped[str] = mapped_column()  # Short descriptive title
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Full details

    # Categorization
    category: Mapped[str] = mapped_column(default=LeadCategory.OTHER.value)
    priority: Mapped[str] = mapped_column(default=LeadPriority.MEDIUM.value)
    status: Mapped[str] = mapped_column(default=LeadStatus.NEW.value)

    # Source of the lead
    source: Mapped[Optional[str]] = mapped_column(nullable=True)  # e.g., "Daughter conversation Dec 1"
    source_date: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # Action tracking
    next_action: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # What to do next
    search_terms: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Keywords to search

    # If this lead results in finding an artwork
    found_artwork_id: Mapped[Optional[int]] = mapped_column(ForeignKey("artworks.id"), nullable=True)
    resolved_date: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to artwork (if found)
    found_artwork: Mapped[Optional["Artwork"]] = relationship(foreign_keys=[found_artwork_id])

    def __repr__(self) -> str:
        return f"<ResearchLead(id={self.id}, title='{self.title[:30]}', status={self.status})>"
