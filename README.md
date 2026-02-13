# 💻 Laptops Scraping

A 3-stage data pipeline that scrapes laptop listings from **Amazon India**, extracts product details, and uses **Google Gemini AI** to parse unstructured titles into clean, structured hardware specifications.

## Pipeline

```
Amazon India (10 pages)
        │
        ▼  scrape_amazon.py
  data/Amazon/laptop_*.html
        │
        ▼  parse_amazon.py
  data/amazon_laptops.csv
        │
        ▼  extract_laptop_specs.py + Gemini AI
  data/amazon_laptops_structured.csv
```

| Stage | Script | Description |
|-------|--------|-------------|
| 1 | `scrape_amazon.py` | Scrapes search results concurrently using **Playwright** (10 pages in parallel) |
| 2 | `parse_amazon.py` | Parses saved HTML with **BeautifulSoup** → extracts title, price, MRP, rating, link |
| 3 | `extract_laptop_specs.py` | Sends all titles to **Gemini** in a single API call → extracts processor, RAM, storage, display, GPU, OS, weight, color |

## Setup

```bash
# Install dependencies
uv sync

# Install Playwright browsers
playwright install chromium

# Set your Gemini API key (https://aistudio.google.com/apikey)
# Create a .env file:
echo GOOGLE_API_KEY=your_key_here > .env
```

## Usage

```bash
# Run the full pipeline
python main.py

# Skip scraping (reuse existing HTML files)
python main.py --skip-scrape

# Skip scraping + parsing (only re-run AI extraction)
python main.py --skip-scrape --skip-parse
```

Each stage can also be run independently:

```bash
python scrape_amazon.py
python parse_amazon.py
python extract_laptop_specs.py
```

## Output

The final CSV (`data/amazon_laptops_structured.csv`) contains:

| Column | Example |
|--------|---------|
| `product_name` | HP 15, ASUS Vivobook Go 14 |
| `processor` | Intel Core i3-1315U |
| `ram` | 8GB DDR4 |
| `storage` | 512GB SSD |
| `display` | 15.6" FHD IPS |
| `gpu` | NVIDIA RTX 3050 |
| `os` | Windows 11 |
| `weight` | 1.5kg |
| `color` | Silver |
| `current_price` | 32990 |
| `mrp` | 47990 |
| `rating` | 4.1 |
| `link` | https://amazon.in/... |

## Dependencies

- [Playwright](https://playwright.dev/python/) — headless browser automation
- [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/) — HTML parsing
- [LangChain + Google GenAI](https://python.langchain.com/) — structured AI extraction with Gemini
- [Pandas](https://pandas.pydata.org/) — data manipulation
- [Colorama](https://pypi.org/project/colorama/) — colored console output
