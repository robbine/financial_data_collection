import pytest
import asyncio
from typing import Dict, Any
from unittest.mock import Mock, patch

from financial_data_collector.core.data_classifier import DataClassifier
from financial_data_collector.models.crawled_data import CrawledData


class TestDataClassifier:
    """Test suite for DataClassifier functionality."""

    def setup_method(self):
        """Setup test environment."""
        self.classifier = DataClassifier()
        self.financial_test_content = ""
        """
        Apple Inc. (AAPL) reported Q3 earnings of $1.29 per share, beating analyst expectations of $1.19.
        The company's revenue increased 5% year-over-year to $81.8 billion. Gross margin expanded to 45.3%,
        up from 43.3% in the prior year quarter. Cash and investments stood at $202.6 billion as of quarter end.
        The board of directors approved a $90 billion share repurchase program and increased the quarterly dividend
        by 4% to $0.24 per share.
        """

        self.news_test_content = ""
        """
        Breaking News: Federal Reserve Announces Interest Rate Decision
        The Federal Reserve today announced it will maintain the target federal funds rate at 5.25-5.50%.
        In a statement released after the two-day policy meeting, Fed officials cited ongoing inflation concerns
        while acknowledging signs of moderating economic growth. Chairman Jerome Powell noted that "inflation has
        declined but remains above our 2% longer-run goal."
        Markets reacted positively to the news, with the S&P 500 rising 0.8% in afternoon trading.
        """

        self.mixed_test_content = ""
        """
        Tesla (TSLA) shares fell 3% in pre-market trading following reports of production cuts at its Shanghai plant.
        Meanwhile, Amazon (AMZN) announced plans to hire 150,000 seasonal workers for the upcoming holiday season.
        Economic data released this morning showed retail sales increased 0.3% in September, beating expectations.
        """

        self.irrelevant_test_content = ""
        """
        The Eiffel Tower is a wrought-iron lattice tower on the Champ de Mars in Paris, France. 
        It is named after the engineer Gustave Eiffel, whose company designed and built the tower.
        Constructed from 1887 to 1889, it was originally criticized by some of France's leading artists and intellectuals
        for its design, but it has become a global cultural icon of France and one of the most recognizable structures in the world.
        """

    def test_data_classifier_initialization(self):
        """Test DataClassifier initialization."""
        assert self.classifier is not None
        assert hasattr(self.classifier, 'financial_extractor')
        assert hasattr(self.classifier, 'news_extractor')
        assert hasattr(self.classifier, 'type_identifier')

    @pytest.mark.asyncio
    async def test_identify_financial_data_type(self):
        """Test identification of financial data type."""
        crawled_data = CrawledData(
            url="https://finance.example.com/earnings-report",
            content=self.financial_test_content
        )

        data_type = await self.classifier.identify_data_type(crawled_data)
        assert data_type == 'financial'

    @pytest.mark.asyncio
    async def test_identify_news_data_type(self):
        """Test identification of news data type."""
        crawled_data = CrawledData(
            url="https://news.example.com/federal-reserve",
            content=self.news_test_content
        )

        data_type = await self.classifier.identify_data_type(crawled_data)
        assert data_type == 'news'

    @pytest.mark.asyncio
    async def test_identify_mixed_data_type(self):
        """Test identification of mixed financial news data type."""
        crawled_data = CrawledData(
            url="https://finance.example.com/market-update",
            content=self.mixed_test_content
        )

        data_type = await self.classifier.identify_data_type(crawled_data)
        assert data_type in ['financial', 'news']  # Should classify as one of them

    @pytest.mark.asyncio
    async def test_identify_irrelevant_data_type(self):
        """Test identification of irrelevant data type."""
        crawled_data = CrawledData(
            url="https://example.com/travel/eiffel-tower",
            content=self.irrelevant_test_content
        )

        data_type = await self.classifier.identify_data_type(crawled_data)
        assert data_type == 'other'

    @pytest.mark.asyncio
    async def test_extract_financial_data(self):
        """Test extraction of financial data."""
        crawled_data = CrawledData(
            url="https://finance.example.com/earnings-report",
            content=self.financial_test_content
        )

        with patch.object(self.classifier.financial_extractor, 'extract') as mock_extract:
            mock_extract.return_value = {
                "company_name": "Apple Inc.",
                "ticker": "AAPL",
                "earnings_per_share": 1.29,
                "revenue": 81800000000,
                "gross_margin": 45.3,
                "cash_position": 202600000000
            }

            financial_data = await self.classifier.extract_financial_data(crawled_data)
            assert financial_data is not None
            assert financial_data["company_name"] == "Apple Inc."
            assert financial_data["ticker"] == "AAPL"
            assert financial_data["earnings_per_share"] == 1.29

    @pytest.mark.asyncio
    async def test_extract_news_data(self):
        """Test extraction of news data."""
        crawled_data = CrawledData(
            url="https://news.example.com/federal-reserve",
            content=self.news_test_content
        )

        with patch.object(self.classifier.news_extractor, 'extract') as mock_extract:
            mock_extract.return_value = {
                "title": "Federal Reserve Announces Interest Rate Decision",
                "topic": "monetary_policy",
                "entities": ["Federal Reserve", "Jerome Powell"],
                "market_impact": "positive"
            }

            news_data = await self.classifier.extract_news_data(crawled_data)
            assert news_data is not None
            assert news_data["title"] == "Federal Reserve Announces Interest Rate Decision"
            assert "Federal Reserve" in news_data["entities"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])