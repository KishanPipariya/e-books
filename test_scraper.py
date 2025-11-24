import unittest
from unittest.mock import MagicMock, patch
import requests
from e_books import get_total_pages, scrape_book_links

class TestEbookScraper(unittest.TestCase):

    @patch('e_books.requests.Session')
    def test_get_total_pages(self, mock_session_cls):
        mock_session = mock_session_cls.return_value
        mock_response = MagicMock()
        mock_response.content = b"""
        <html>
            <body>
                <nav>Main Nav</nav>
                <nav>
                    <li>Page 1</li>
                    <li>Page 2</li>
                    <li>Page 3</li>
                </nav>
            </body>
        </html>
        """
        mock_session.get.return_value = mock_response
        
        total_pages = get_total_pages(mock_session)
        self.assertEqual(total_pages, 3)

    @patch('e_books.requests.Session')
    def test_scrape_book_links(self, mock_session_cls):
        mock_session = mock_session_cls.return_value
        mock_response = MagicMock()
        # Mocking a page with 2 books (4 links: 2 images + 2 titles)
        mock_response.content = b"""
        <html>
            <body>
                <ol>
                    <a href="/ebooks/book1">Book 1 Image</a>
                    <a href="/ebooks/book1">Book 1 Title</a>
                    <a href="/ebooks/book2">Book 2 Image</a>
                    <a href="/ebooks/book2">Book 2 Title</a>
                    <a href="https://external.com">External Link</a>
                </ol>
            </body>
        </html>
        """
        mock_session.get.return_value = mock_response
        
        links = scrape_book_links(mock_session, 1)
        # Should pick every 2nd link from valid ones
        # Valid anchors: book1 (img), book1 (title), book2 (img), book2 (title)
        # Result should be: book1 (img), book2 (img) -> wait, the loop is range(0, len, 2)
        # So it picks index 0 and 2.
        expected_links = [
            "https://standardebooks.org/ebooks/book1",
            "https://standardebooks.org/ebooks/book2"
        ]
        self.assertEqual(links, expected_links)

if __name__ == '__main__':
    unittest.main()
