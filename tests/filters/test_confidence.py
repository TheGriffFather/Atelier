"""Tests for the confidence scoring system."""

import pytest

from src.filters.confidence import ConfidenceScorer
from src.scrapers.base import ScrapedListing
from src.database import SourcePlatform


@pytest.fixture
def scorer():
    return ConfidenceScorer()


def make_listing(title: str, description: str = "") -> ScrapedListing:
    """Helper to create test listings."""
    return ScrapedListing(
        title=title,
        description=description,
        source_platform=SourcePlatform.EBAY,
        source_url="https://example.com/listing/123",
    )


class TestConfidenceScorer:
    """Tests for ConfidenceScorer."""

    def test_rejects_da_vinci_code_author(self, scorer):
        """Should reject listings about the author Dan Brown."""
        listing = make_listing(
            "Dan Brown - The Da Vinci Code - First Edition",
            "Bestselling thriller by the famous author"
        )
        result = scorer.score(listing)

        assert result.is_rejected
        assert "da vinci code" in result.rejection_reason.lower() or len(result.negative_signals) > 0

    def test_rejects_novelist_references(self, scorer):
        """Should reject listings mentioning novelist/author."""
        listing = make_listing(
            "Dan Brown Collection",
            "Complete set of novels by this bestselling author"
        )
        result = scorer.score(listing)

        assert result.is_rejected

    def test_high_confidence_trompe_loeil(self, scorer):
        """Should give high confidence to trompe l'oeil references."""
        listing = make_listing(
            "Dan Brown Trompe L'oeil Painting",
            "Beautiful vintage postcard painting by Connecticut artist"
        )
        result = scorer.score(listing)

        assert not result.is_rejected
        assert result.confidence_score >= 3.0
        assert "trompe" in str(result.positive_signals).lower()

    def test_high_confidence_susan_powell(self, scorer):
        """Should give high confidence to Susan Powell gallery references."""
        listing = make_listing(
            "Dan Brown - Madison Postcards",
            "From Susan Powell Fine Art gallery"
        )
        result = scorer.score(listing)

        assert not result.is_rejected
        assert result.confidence_score >= 2.5

    def test_medium_confidence_connecticut(self, scorer):
        """Should give medium confidence to Connecticut references."""
        listing = make_listing(
            "Dan Brown Painting",
            "Artist from Madison, CT"
        )
        result = scorer.score(listing)

        assert not result.is_rejected
        assert result.confidence_score >= 1.0

    def test_low_score_ambiguous_listing(self, scorer):
        """Ambiguous listings should have low confidence."""
        listing = make_listing(
            "Dan Brown Art Print",
            "Decorative print"
        )
        result = scorer.score(listing)

        # Should not be rejected, but low confidence
        assert not result.is_rejected
        assert result.confidence_score < 1.0

    def test_filter_batch_removes_rejected(self, scorer):
        """Batch filtering should remove rejected listings."""
        listings = [
            make_listing("Da Vinci Code Book", "Bestselling novel"),
            make_listing("Dan Brown Trompe L'oeil", "Beautiful painting"),
            make_listing("Angels and Demons", "Thriller book"),
        ]

        results = scorer.filter_listings(listings)

        assert len(results) == 1
        assert "trompe" in results[0].listing.title.lower()

    def test_filter_batch_sorts_by_confidence(self, scorer):
        """Batch filtering should sort by confidence score."""
        listings = [
            make_listing("Dan Brown Art", "Generic painting"),
            make_listing("Dan Brown Trompe L'oeil Susan Powell", "High confidence"),
            make_listing("Dan Brown Connecticut Artist", "Medium confidence"),
        ]

        results = scorer.filter_listings(listings)

        # Should be sorted highest to lowest
        scores = [r.confidence_score for r in results]
        assert scores == sorted(scores, reverse=True)
