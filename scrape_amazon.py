from pathlib import Path
from playwright.async_api import async_playwright
import asyncio, time


query, pages = 'laptop', range(1, 11)
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'

def get_url(pg: int) -> str:
	"""Generate Amazon search URL for a given page number."""
	return f'https://www.amazon.in/s?k={query}&crid=3NW6BLF8383HH&qid=1770270843&sprefix=lapt%2Caps%2C463&xpid=vjzpPUSu4zLUM&ref=sr_pg_{pg}'


async def scrape_page_async(context, pg: int, results: dict):
	"""Scrape a single page asynchronously using Playwright selectors."""
	url = get_url(pg)
	print(f'Scraping page {pg}')
	
	page = await context.new_page()
	await page.goto(url, wait_until='domcontentloaded')
	
	cards = await page.locator('.puis-card-container').all()
	
	items = []
	for card in cards:
		# Check if card contains "Sponsored" text
		text_content = await card.text_content()
		if 'Sponsored' in text_content:
			continue
		
		# Extract only the HTML we need
		html = await card.inner_html()
		items.append(html)
	
	results[pg] = items
	print(f'Page {pg} done - found {len(items)} items')


async def start_async():
	"""Asynchronous scraping - all pages are scraped concurrently."""
	print('Starting asynchronous Playwright...')
	start_time = time.perf_counter()
	results = {}
	
	async with async_playwright() as p:
		browser = await p.chromium.launch()
		context = await browser.new_context(user_agent=USER_AGENT, java_script_enabled=False)
		
		# Create tasks for all pages to run concurrently
		tasks = [scrape_page_async(context, pg, results) for pg in pages]
		await asyncio.gather(*tasks)
		
		await browser.close()
	
	# Save all results to files
	item = 1
	for pg in sorted(results.keys()):
		for html in results[pg]:
			Path(f'data/Amazon/laptop_{item}.html').write_text(html, 'utf-8')
			item += 1
	
	end_time = time.perf_counter()
	print(f'Asynchronous Playwright took {end_time - start_time:.2f} seconds')
	print(f'Total items scraped: {item}')


if __name__ == '__main__':
	# Create output directory
	Path('data/Amazon').mkdir(parents=True, exist_ok=True)
	
	# Run async scraper
	asyncio.run(start_async())
