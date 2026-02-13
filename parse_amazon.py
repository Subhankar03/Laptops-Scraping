"""
Extract product details from scraped Amazon HTML files.
"""
from pathlib import Path
from bs4 import BeautifulSoup
import pandas as pd
import re


def extract_product_details(html: str) -> dict:
	"""
	Extract product details from Amazon product card HTML.
	
	Returns dict with: title, mrp, current_price, rating, link
	"""
	soup = BeautifulSoup(html, 'html.parser')
	
	# Extract title from h2 > span
	title = None
	h2 = soup.find('h2')
	if h2:
		span = h2.find('span')
		title = span.get_text(strip=True) if span else h2.get_text(strip=True)
	
	# Extract current price (the main displayed price)
	current_price = None
	price_tag = soup.find('span', class_='a-price', attrs={'data-a-size': 'xl'})
	if price_tag:
		offscreen = price_tag.find('span', class_='a-offscreen')
		if offscreen:
			price_text = offscreen.get_text(strip=True)
			# Extract numeric value (e.g., "₹12,990" -> 12990)
			current_price = re.sub(r'[^\d.]', '', price_text)
			current_price = float(current_price) if current_price else None
	
	# Extract MRP (struck-through price)
	mrp = None
	mrp_tag = soup.find('span', class_='a-price', attrs={'data-a-strike': 'true'})
	if mrp_tag:
		offscreen = mrp_tag.find('span', class_='a-offscreen')
		if offscreen:
			mrp_text = offscreen.get_text(strip=True)
			mrp = re.sub(r'[^\d.]', '', mrp_text)
			mrp = float(mrp) if mrp else None
	
	# Extract rating (e.g., "3.0")
	rating = None
	# Method 1: Direct rating text
	reviews_block = soup.find('div', attrs={'data-cy': 'reviews-block'})
	if reviews_block:
		rating_span = reviews_block.find('span', class_='a-size-small a-color-base')
		if rating_span:
			rating_text = rating_span.get_text(strip=True)
			try:
				rating = float(rating_text)
			except ValueError:
				pass
	
	# Method 2: From alt text if method 1 fails
	if rating is None:
		icon_alt = soup.find('span', class_='a-icon-alt')
		if icon_alt:
			alt_text = icon_alt.get_text(strip=True)
			match = re.search(r'([\d.]+)\s*out of\s*5', alt_text)
			if match:
				rating = float(match.group(1))
	
	# Extract product link
	link = None
	title_recipe = soup.find('div', attrs={'data-cy': 'title-recipe'})
	if title_recipe:
		a_tag = title_recipe.find('a', href=True)
		if a_tag:
			link = 'https://www.amazon.in' + a_tag['href'].replace('&amp;', '&')
	
	return {
		'title': title,
		'mrp': mrp,
		'current_price': current_price,
		'rating': rating,
		'link': link
	}


def process_all_html_files(data_dir: str = 'data/Amazon', output_csv: str = 'data/amazon_laptops.csv') -> pd.DataFrame:
	"""
	Process all HTML files in the directory and save to CSV.
	
	Args:
		data_dir: Directory containing scraped HTML files
		output_csv: Output CSV file path
	
	Returns:
		DataFrame with all extracted products
	"""
	data_path = Path(data_dir)
	html_files = sorted(data_path.glob('*.html'), key=lambda x: int(re.search(r'(\d+)', x.stem).group(1)))
	
	products = []
	for idx, html_file in enumerate(html_files, start=1):
		html = html_file.read_text(encoding='utf-8')
		product = extract_product_details(html)
		product['sl_no'] = idx
		products.append(product)
	
	# Create DataFrame with sl_no as first column
	df = pd.DataFrame(products)
	columns_order = ['sl_no', 'title', 'current_price', 'mrp', 'rating', 'link']
	df = df[columns_order]
	df.columns = ['SL No', 'Title', 'Current Price', 'MRP', 'Rating', 'Link']
	
	# Save to CSV
	output_path = Path(output_csv)
	output_path.parent.mkdir(parents=True, exist_ok=True)
	df.to_csv(output_path, index=False, encoding='utf-8')
	
	print(f'Saved {len(df)} products to {output_csv}')
	return df


if __name__ == '__main__':
	df = process_all_html_files()
	print(df.head(10))
