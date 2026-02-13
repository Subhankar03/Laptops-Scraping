"""Run the full laptop scraping pipeline."""
import warnings
warnings.filterwarnings('ignore', message='.*Pydantic V1.*')

import asyncio
import os
from pathlib import Path

from colorama import init, Fore, Style
from scrape_amazon import start_async
from parse_amazon import process_all_html_files
from extract_laptop_specs import extract_specs_from_titles
from dotenv import load_dotenv

init(autoreset=True)
load_dotenv()


def banner(text: str, color: str = Fore.BLUE):
	"""Print a colored stage banner."""
	line = '=' * 60
	print(f'\n{color}{line}')
	print(f'{color}{text}')
	print(f'{color}{line}{Style.RESET_ALL}')


def info(text: str):
	print(f'{Fore.GREEN}✔ {text}{Style.RESET_ALL}')


def warn(text: str):
	print(f'{Fore.YELLOW}⚠ {text}{Style.RESET_ALL}')


def error(text: str):
	print(f'{Fore.RED}✖ {text}{Style.RESET_ALL}')


def run_pipeline(skip_scrape=False, skip_parse=False):
	"""
	Run the laptop scraping pipeline.
	
	Stages:
		1. Scrape Amazon search results (Playwright)
		2. Parse HTML files into CSV (BeautifulSoup)
		3. Extract structured specs using AI (Gemini)
	"""
	# Stage 1: Scrape
	if not skip_scrape:
		banner('STAGE 1: Scraping Amazon...')
		Path('data/Amazon').mkdir(parents=True, exist_ok=True)
		asyncio.run(start_async())
		info('Scraping complete')
	else:
		warn('Skipping Stage 1 (scraping)')

	# Stage 2: Parse HTML → CSV
	if not skip_parse:
		banner('STAGE 2: Parsing HTML files...')
		process_all_html_files()
		info('Parsing complete')
	else:
		warn('Skipping Stage 2 (parsing)')

	# Stage 3: AI spec extraction
	if not os.environ.get('GOOGLE_API_KEY'):
		error('GOOGLE_API_KEY not set. Skipping Stage 3.')
		warn('Get an API key from https://aistudio.google.com/apikey')
		return

	banner('STAGE 3: Extracting specs with Gemini...')
	df = extract_specs_from_titles()
	info('Spec extraction complete')

	banner('PIPELINE COMPLETE', Fore.GREEN)
	info(f'Total laptops processed: {len(df)}')
	info(f'Output: data/amazon_laptops_structured.csv')


if __name__ == '__main__':
	import argparse

	parser = argparse.ArgumentParser(description='Amazon laptop scraping pipeline')
	parser.add_argument('--skip-scrape', action='store_true', help='Skip scraping, use existing HTML files')
	parser.add_argument('--skip-parse', action='store_true', help='Skip parsing, use existing CSV')
	args = parser.parse_args()

	run_pipeline(skip_scrape=args.skip_scrape, skip_parse=args.skip_parse)
