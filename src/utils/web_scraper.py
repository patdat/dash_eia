"""
Web scraping utility using Playwright for dynamic content
"""
import asyncio
from playwright.async_api import async_playwright
from typing import Optional, Dict, Any
import json


class WebScraper:
    """
    A web scraper utility using Playwright for scraping dynamic content
    """
    
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
    
    async def __aenter__(self):
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def start(self, headless: bool = True):
        """
        Start the browser instance
        
        Args:
            headless: Run browser in headless mode (default: True)
        """
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=headless)
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()
    
    async def close(self):
        """Close the browser instance"""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def scrape_url(self, url: str, wait_for_selector: Optional[str] = None) -> str:
        """
        Scrape content from a URL
        
        Args:
            url: The URL to scrape
            wait_for_selector: Optional CSS selector to wait for before extracting content
        
        Returns:
            The page content as HTML
        """
        await self.page.goto(url)
        
        if wait_for_selector:
            await self.page.wait_for_selector(wait_for_selector)
        
        return await self.page.content()
    
    async def extract_text(self, url: str, selector: str) -> str:
        """
        Extract text content from a specific element
        
        Args:
            url: The URL to scrape
            selector: CSS selector for the element
        
        Returns:
            Text content of the element
        """
        await self.page.goto(url)
        await self.page.wait_for_selector(selector)
        element = await self.page.query_selector(selector)
        return await element.inner_text() if element else ""
    
    async def extract_table_data(self, url: str, table_selector: str = "table") -> list:
        """
        Extract data from an HTML table
        
        Args:
            url: The URL to scrape
            table_selector: CSS selector for the table (default: "table")
        
        Returns:
            List of dictionaries representing table rows
        """
        await self.page.goto(url)
        await self.page.wait_for_selector(table_selector)
        
        # Extract table data using JavaScript in the browser context
        data = await self.page.evaluate(f'''
            () => {{
                const table = document.querySelector("{table_selector}");
                if (!table) return [];
                
                const headers = Array.from(table.querySelectorAll("thead th"))
                    .map(th => th.innerText.trim());
                
                const rows = Array.from(table.querySelectorAll("tbody tr"));
                
                return rows.map(row => {{
                    const cells = Array.from(row.querySelectorAll("td"));
                    const rowData = {{}};
                    cells.forEach((cell, i) => {{
                        if (headers[i]) {{
                            rowData[headers[i]] = cell.innerText.trim();
                        }}
                    }});
                    return rowData;
                }});
            }}
        ''')
        
        return data
    
    async def screenshot(self, url: str, path: str, full_page: bool = False):
        """
        Take a screenshot of a webpage
        
        Args:
            url: The URL to screenshot
            path: Path to save the screenshot
            full_page: Capture full page or just viewport (default: False)
        """
        await self.page.goto(url)
        await self.page.screenshot(path=path, full_page=full_page)
    
    async def download_file(self, url: str, download_path: str):
        """
        Download a file from a URL
        
        Args:
            url: The URL of the file to download
            download_path: Path to save the downloaded file
        """
        async with self.page.expect_download() as download_info:
            await self.page.goto(url)
        download = await download_info.value
        await download.save_as(download_path)


# Convenience functions for simple use cases
async def scrape_simple(url: str, wait_for_selector: Optional[str] = None) -> str:
    """
    Simple function to scrape a URL without managing browser lifecycle
    
    Args:
        url: The URL to scrape
        wait_for_selector: Optional CSS selector to wait for
    
    Returns:
        The page content as HTML
    """
    async with WebScraper() as scraper:
        return await scraper.scrape_url(url, wait_for_selector)


async def extract_eia_data(url: str) -> Dict[str, Any]:
    """
    Extract data from EIA website
    
    Args:
        url: EIA webpage URL
    
    Returns:
        Dictionary containing extracted data
    """
    async with WebScraper() as scraper:
        # Wait for data tables to load
        content = await scraper.scrape_url(url, wait_for_selector=".data-table")
        
        # You can add specific extraction logic here based on EIA page structure
        # For now, returning the raw HTML
        return {"html": content, "url": url}


# Example usage
if __name__ == "__main__":
    async def main():
        # Example: Scrape EIA petroleum status report
        url = "https://www.eia.gov/petroleum/supply/weekly/"
        
        async with WebScraper() as scraper:
            # Get the page content
            content = await scraper.scrape_url(url)
            print(f"Scraped {len(content)} characters from {url}")
            
            # Take a screenshot
            await scraper.screenshot(url, "eia_screenshot.png", full_page=True)
            print("Screenshot saved")
    
    # Run the example
    asyncio.run(main())