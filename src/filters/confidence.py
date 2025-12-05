"""Confidence scoring for artwork identification."""

import re
from dataclasses import dataclass, field

import structlog

from src.scrapers.base import ScrapedListing

logger = structlog.get_logger()


@dataclass
class FilterResult:
    """Result of filtering a listing through confidence scoring."""
    listing: ScrapedListing
    confidence_score: float
    positive_signals: dict[str, float] = field(default_factory=dict)
    negative_signals: dict[str, float] = field(default_factory=dict)
    is_rejected: bool = False
    rejection_reason: str | None = None


class ConfidenceScorer:
    """
    Scores listings to determine likelihood of being genuine Dan Brown artwork.

    Uses positive signals (increasing confidence) and negative signals
    (decreasing confidence or outright rejection) to filter results.
    """

    # Negative signals that auto-reject (the author Dan Brown)
    REJECT_PATTERNS = [
        r"da\s*vinci\s*code",
        r"robert\s*langdon",
        r"angels\s*(&|and)\s*demons",
        r"inferno",
        r"digital\s*fortress",
        r"deception\s*point",
        r"origin\s*novel",
        r"the\s*lost\s*symbol",
        r"\bauthor\b",
        r"\bnovelist\b",
        r"\bthriller\b",
        r"\bbestseller\b",
        r"\bbestselling\b",
        r"new\s*york\s*times\s*bestseller",
    ]

    # Strong positive signals (artist Dan Brown)
    STRONG_POSITIVE = {
        r"trompe\s*l['']?oeil": 3.0,
        r"paier\s*college": 3.0,
        r"ken\s*davies": 2.5,
        r"peter\s*poskas": 2.5,
        r"susan\s*powell\s*fine\s*art": 3.0,
        r"david\s*findlay\s*galler": 2.5,
        r"greenwich\s*workshop\s*galler": 2.5,
        r"robert\s*wilson\s*galler": 2.0,
        r"rack\s*painting": 2.5,
    }

    # Medium positive signals
    MEDIUM_POSITIVE = {
        r"madison\s*,?\s*(ct|connecticut)": 1.5,
        r"hamden\s*,?\s*(ct|connecticut)": 1.5,
        r"nantucket": 1.5,
        r"cape\s*cod": 1.0,
        r"vintage\s*postcards?": 1.5,
        r"currency\s*painting": 1.5,
        r"paper\s*currency": 1.0,
        r"hyperrealistic": 1.0,
        r"realist\s*paint": 1.0,
        r"still\s*life": 0.5,
        r"connecticut\s*artist": 1.5,
        r"1949\s*-?\s*2022": 2.0,  # His life dates
    }

    # Weak positive signals
    WEAK_POSITIVE = {
        r"harlequin\s*books?": 0.5,
        r"rolling\s*stone": 0.5,
        r"smithsonian": 0.5,
        r"national\s*geographic": 0.5,
        r"book\s*cover\s*illustrat": 0.5,
        r"commercial\s*illustrat": 0.5,
        r"syracuse\s*,?\s*(ny|new\s*york)": 0.5,
    }

    def __init__(self, rejection_threshold: float = -1.0, acceptance_threshold: float = 1.0):
        """
        Initialize the confidence scorer.

        Args:
            rejection_threshold: Score below which listings are auto-rejected
            acceptance_threshold: Score above which listings are high confidence
        """
        self.rejection_threshold = rejection_threshold
        self.acceptance_threshold = acceptance_threshold
        self.logger = logger.bind(component="confidence_scorer")

    def score(self, listing: ScrapedListing) -> FilterResult:
        """
        Score a listing for confidence that it's genuine Dan Brown artwork.

        Args:
            listing: The scraped listing to score

        Returns:
            FilterResult with confidence score and signal details
        """
        text = f"{listing.title} {listing.description or ''}".lower()

        result = FilterResult(listing=listing, confidence_score=0.0)

        # Check for auto-reject patterns first
        for pattern in self.REJECT_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                result.is_rejected = True
                result.rejection_reason = f"Matched rejection pattern: {pattern}"
                result.negative_signals[pattern] = -10.0
                result.confidence_score = -10.0
                self.logger.debug(
                    "Listing rejected",
                    url=listing.source_url,
                    pattern=pattern,
                )
                return result

        # Score positive signals
        for pattern, weight in self.STRONG_POSITIVE.items():
            if re.search(pattern, text, re.IGNORECASE):
                result.positive_signals[pattern] = weight
                result.confidence_score += weight

        for pattern, weight in self.MEDIUM_POSITIVE.items():
            if re.search(pattern, text, re.IGNORECASE):
                result.positive_signals[pattern] = weight
                result.confidence_score += weight

        for pattern, weight in self.WEAK_POSITIVE.items():
            if re.search(pattern, text, re.IGNORECASE):
                result.positive_signals[pattern] = weight
                result.confidence_score += weight

        # Check if below rejection threshold
        if result.confidence_score < self.rejection_threshold:
            result.is_rejected = True
            result.rejection_reason = f"Score {result.confidence_score} below threshold {self.rejection_threshold}"

        self.logger.debug(
            "Listing scored",
            url=listing.source_url,
            score=result.confidence_score,
            positive_signals=list(result.positive_signals.keys()),
        )

        return result

    def filter_listings(self, listings: list[ScrapedListing]) -> list[FilterResult]:
        """
        Score and filter a batch of listings.

        Args:
            listings: List of scraped listings

        Returns:
            List of FilterResults, sorted by confidence score (highest first)
        """
        results = [self.score(listing) for listing in listings]

        # Filter out rejected listings
        accepted = [r for r in results if not r.is_rejected]

        # Sort by confidence score
        accepted.sort(key=lambda r: r.confidence_score, reverse=True)

        self.logger.info(
            "Batch filtering complete",
            total=len(listings),
            accepted=len(accepted),
            rejected=len(listings) - len(accepted),
        )

        return accepted
