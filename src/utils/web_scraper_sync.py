"""
Synchronous wrapper for the web scraper utility
"""
import asyncio
from typing import Optional, Dict, Any
from src.utils.web_scraper import WebScraper


def scrape_url(url: str, wait_for_selector: Optional[str] = None, headless: bool = True) -> str:
    """
    Synchronous function to scrape a URL
    
    Args:
        url: The URL to scrape
        wait_for_selector: Optional CSS selector to wait for
        headless: Run browser in headless mode (default: True)
    
    Returns:
        The page content as HTML
    """
    async def _scrape():
        async with WebScraper() as scraper:
            await scraper.start(headless=headless)
            return await scraper.scrape_url(url, wait_for_selector)
    
    return asyncio.run(_scrape())


def extract_text(url: str, selector: str, headless: bool = True) -> str:
    """
    Synchronous function to extract text from a specific element
    
    Args:
        url: The URL to scrape
        selector: CSS selector for the element
        headless: Run browser in headless mode (default: True)
    
    Returns:
        Text content of the element
    """
    async def _extract():
        async with WebScraper() as scraper:
            await scraper.start(headless=headless)
            return await scraper.extract_text(url, selector)
    
    return asyncio.run(_extract())


def extract_table_data(url: str, table_selector: str = "table", headless: bool = True) -> list:
    """
    Synchronous function to extract data from an HTML table
    
    Args:
        url: The URL to scrape
        table_selector: CSS selector for the table (default: "table")
        headless: Run browser in headless mode (default: True)
    
    Returns:
        List of dictionaries representing table rows
    """
    async def _extract():
        async with WebScraper() as scraper:
            await scraper.start(headless=headless)
            return await scraper.extract_table_data(url, table_selector)
    
    return asyncio.run(_extract())


def screenshot(url: str, path: str, full_page: bool = False, headless: bool = True):
    """
    Synchronous function to take a screenshot of a webpage
    
    Args:
        url: The URL to screenshot
        path: Path to save the screenshot
        full_page: Capture full page or just viewport (default: False)
        headless: Run browser in headless mode (default: True)
    """
    async def _screenshot():
        async with WebScraper() as scraper:
            await scraper.start(headless=headless)
            await scraper.screenshot(url, path, full_page)
    
    asyncio.run(_screenshot())


def scrape_eia_weekly_petroleum(headless: bool = True) -> Dict[str, Any]:
    """
    Scrape the EIA Weekly Petroleum Status Report
    
    Args:
        headless: Run browser in headless mode (default: True)
    
    Returns:
        Dictionary containing scraped data
    """
    url = "https://www.eia.gov/petroleum/supply/weekly/"
    
    async def _scrape():
        async with WebScraper() as scraper:
            await scraper.start(headless=headless)
            
            # Navigate to the page
            await scraper.page.goto(url)
            
            # Wait for tables to load
            await scraper.page.wait_for_selector("table", timeout=10000)
            
            # Extract all tables
            tables = await scraper.page.evaluate('''
                () => {
                    const tables = document.querySelectorAll("table");
                    const result = [];
                    
                    tables.forEach((table, index) => {
                        const headers = Array.from(table.querySelectorAll("thead th"))
                            .map(th => th.innerText.trim());
                        
                        const rows = Array.from(table.querySelectorAll("tbody tr"));
                        const data = rows.map(row => {
                            const cells = Array.from(row.querySelectorAll("td"));
                            const rowData = {};
                            cells.forEach((cell, i) => {
                                if (headers[i]) {
                                    rowData[headers[i]] = cell.innerText.trim();
                                }
                            });
                            return rowData;
                        });
                        
                        result.push({
                            index: index,
                            headers: headers,
                            data: data
                        });
                    });
                    
                    return result;
                }
            ''')
            
            # Extract links to Excel files
            excel_links = await scraper.page.evaluate('''
                () => {
                    const links = document.querySelectorAll('a[href*=".xls"]');
                    return Array.from(links).map(link => ({
                        text: link.innerText.trim(),
                        href: link.href
                    }));
                }
            ''')
            
            return {
                "url": url,
                "tables": tables,
                "excel_links": excel_links
            }
    
    return asyncio.run(_scrape())


# Example usage
if __name__ == "__main__":
    # Example 1: Simple scraping
    content = scrape_url("https://www.eia.gov/petroleum/supply/weekly/")
    print(f"Scraped {len(content)} characters")
    
    # Example 2: Extract EIA data
    eia_data = scrape_eia_weekly_petroleum()
    print(f"Found {len(eia_data['tables'])} tables")
    print(f"Found {len(eia_data['excel_links'])} Excel download links")