"""
HTML parsing logic for extracting book data.
"""
from typing import Optional, List
from bs4 import BeautifulSoup
from loguru import logger

from .models.book import Book
from .models.bookparseresult import BookParseResult
from .utils import (
    extract_price,
    extract_rating,
    clean_text,
    build_absolute_url,
    extract_number_from_text
)
from config import settings


class BookParser:
    """Parser for extracting book information from HTML."""
    
    def __init__(self, base_url: str = None):
        """
        Initialize parser.
        
        Args:
            base_url: Base URL for building absolute URLs
        """
        self.base_url = base_url or settings.target_url
    
    def parse_book_page(self, html: str, url: str) -> BookParseResult:
        """
        Parse a single book page and extract all information.
        
        Args:
            html: HTML content of the book page
            url: URL of the book page
            
        Returns:
            BookParseResult with parsed data or error
        """
        try:
            soup = BeautifulSoup(html, 'lxml')
            
            # Extract all fields
            title = self._extract_title(soup)
            description = self._extract_description(soup)
            category = self._extract_category(soup)
            price_excl_tax = self._extract_price_excl_tax(soup)
            price_incl_tax = self._extract_price_incl_tax(soup)
            availability = self._extract_availability(soup)
            num_reviews = self._extract_num_reviews(soup)
            image_url = self._extract_image_url(soup)
            rating = self._extract_rating(soup)
            
            # Validate required fields
            if not all([title, category, price_incl_tax > 0, rating > 0]):
                missing_fields = []
                if not title:
                    missing_fields.append("title")
                if not category:
                    missing_fields.append("category")
                if price_incl_tax <= 0:
                    missing_fields.append("price")
                if rating <= 0:
                    missing_fields.append("rating")
                
                error_msg = f"Missing required fields: {', '.join(missing_fields)}"
                logger.warning(f"Incomplete book data for {url}: {error_msg}")
                return BookParseResult(success=False, book=None, error=error_msg, url=url)
            
            # Create Book model
            book = Book(
                url=url,
                title=title,
                description=description,
                category=category,
                price_excl_tax=price_excl_tax,
                price_incl_tax=price_incl_tax,
                availability=availability,
                num_reviews=num_reviews,
                image_url=image_url,
                rating=rating,
                raw_html=html  # Store raw HTML as backup
            )
            
            return BookParseResult(success=True, book=book, error=None, url=url)
            
        except Exception as e:
            logger.error(f"Error parsing book page {url}: {e}")
            return BookParseResult(success=False, book=None, error=str(e), url=url)
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract book title."""
        title_elem = soup.find('h1')
        if title_elem:
            return clean_text(title_elem.get_text())
        
        # Fallback: try product title
        title_elem = soup.find('div', class_='product_main').find('h1')
        if title_elem:
            return clean_text(title_elem.get_text())
        
        return ""
    
    def _extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract book description."""
        # Description is in the product_description section
        desc_header = soup.find('div', id='product_description')
        if desc_header:
            # Description is in the next <p> tag
            desc_elem = desc_header.find_next('p')
            if desc_elem:
                return clean_text(desc_elem.get_text())
        
        return None
    
    def _extract_category(self, soup: BeautifulSoup) -> str:
        """Extract book category from breadcrumb."""
        breadcrumb = soup.find('ul', class_='breadcrumb')
        if breadcrumb:
            # Category is the second-to-last item (last is book title)
            links = breadcrumb.find_all('a')
            if len(links) >= 3:
                # links[0] = Home, links[1] = Books, links[2] = Category
                return clean_text(links[2].get_text())
        
        return "Unknown"
    
    def _extract_price_excl_tax(self, soup: BeautifulSoup) -> float:
        """Extract price excluding tax."""
        table = soup.find('table', class_='table-striped')
        if table:
            rows = table.find_all('tr')
            for row in rows:
                th = row.find('th')
                if th and 'Price (excl. tax)' in th.get_text():
                    td = row.find('td')
                    if td:
                        return extract_price(td.get_text())
        
        return 0.0
    
    def _extract_price_incl_tax(self, soup: BeautifulSoup) -> float:
        """Extract price including tax."""
        # Try product info table
        table = soup.find('table', class_='table-striped')
        if table:
            rows = table.find_all('tr')
            for row in rows:
                th = row.find('th')
                if th and 'Price (incl. tax)' in th.get_text():
                    td = row.find('td')
                    if td:
                        return extract_price(td.get_text())
        
        # Fallback: try main price
        price_elem = soup.find('p', class_='price_color')
        if price_elem:
            return extract_price(price_elem.get_text())
        
        return 0.0
    
    def _extract_availability(self, soup: BeautifulSoup) -> str:
        """Extract availability status."""
        # Availability is in product info table
        table = soup.find('table', class_='table-striped')
        if table:
            rows = table.find_all('tr')
            for row in rows:
                th = row.find('th')
                if th and 'Availability' in th.get_text():
                    td = row.find('td')
                    if td:
                        return clean_text(td.get_text())
        
        # Fallback: look for instock availability class
        avail_elem = soup.find('p', class_='instock availability')
        if avail_elem:
            return clean_text(avail_elem.get_text())
        
        return "Unknown"
    
    def _extract_num_reviews(self, soup: BeautifulSoup) -> int:
        """Extract number of reviews."""
        table = soup.find('table', class_='table-striped')
        if table:
            rows = table.find_all('tr')
            for row in rows:
                th = row.find('th')
                if th and 'Number of reviews' in th.get_text():
                    td = row.find('td')
                    if td:
                        return extract_number_from_text(td.get_text())
        
        return 0
    
    def _extract_image_url(self, soup: BeautifulSoup) -> str:
        """Extract book cover image URL."""
        # Image is in the product gallery
        img_container = soup.find('div', id='product_gallery')
        if img_container:
            img = img_container.find('img')
            if img and img.get('src'):
                relative_url = img.get('src')
                # Build absolute URL
                return build_absolute_url(self.base_url, relative_url)
        
        # Fallback: try any image in main product area
        img = soup.find('div', class_='item active').find('img')
        if img and img.get('src'):
            relative_url = img.get('src')
            return build_absolute_url(self.base_url, relative_url)
        
        return ""
    
    def _extract_rating(self, soup: BeautifulSoup) -> int:
        """Extract star rating."""
        # Rating is in a <p> tag with class "star-rating"
        rating_elem = soup.find('p', class_='star-rating')
        if rating_elem:
            # Rating is in the class name: "star-rating Three"
            classes = rating_elem.get('class', [])
            for cls in classes:
                if cls != 'star-rating':
                    return extract_rating(cls)
        
        return 0
    
    def parse_category_page(self, html: str) -> List[str]:
        """
        Parse a category page and extract all book URLs.
        
        Args:
            html: HTML content of category page
            
        Returns:
            List of book URLs
        """
        soup = BeautifulSoup(html, 'lxml')
        book_urls = []
        
        # Books are in article elements with class "product_pod"
        articles = soup.find_all('article', class_='product_pod')
        
        for article in articles:
            # Find the link to the book
            h3 = article.find('h3')
            if h3:
                link = h3.find('a')
                if link and link.get('href'):
                    relative_url = link.get('href')
                    absolute_url = build_absolute_url(self.base_url, relative_url)
                    book_urls.append(absolute_url)
        
        logger.info(f"Found {len(book_urls)} books on page")
        return book_urls
    
    def has_next_page(self, html: str) -> Optional[str]:
        """
        Check if there's a next page and return its URL.
        
        Args:
            html: HTML content of current page
            
        Returns:
            URL of next page or None
        """
        soup = BeautifulSoup(html, 'lxml')
        
        # Look for "next" button in pagination
        next_elem = soup.find('li', class_='next')
        if next_elem:
            link = next_elem.find('a')
            if link and link.get('href'):
                return link.get('href')
        
        return None
    
    def extract_categories(self, html: str) -> List[tuple]:
        """
        Extract all category links from homepage.
        
        Args:
            html: HTML content of homepage
            
        Returns:
            List of tuples (category_name, category_url)
        """
        soup = BeautifulSoup(html, 'lxml')
        categories = []
        
        # Categories are in the sidebar navigation
        nav = soup.find('ul', class_='nav-list')
        if nav:
            # Find all category links (skip "Books" which is the parent)
            links = nav.find_all('a')
            for link in links[1:]:  # Skip first link (Books)
                category_name = clean_text(link.get_text())
                category_url = build_absolute_url(self.base_url, link.get('href'))
                categories.append((category_name, category_url))
        
        logger.info(f"Found {len(categories)} categories")
        return categories