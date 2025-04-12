import requests
from bs4 import BeautifulSoup
import copy
import re
import os
import json
import signal
from contextlib import contextmanager

def scrape_moneycontrol_data(output_dir="../output", company_names=None, categories=None, scrape_all=False, tavily_api_key=None):
	"""
	Scrape financial data from MoneyControl website using Tavily API for enhanced search and parsing.
	
	Parameters:
	----------
	output_dir : str
		Directory to store the output files
	company_names : list
		List of specific company names to scrape. If None, uses other parameters.
	categories : list
		List of categories to scrape. If None, uses default category "Utilities".
	scrape_all : bool
		If True, scrapes data for all companies listed alphabetically.
	tavily_api_key : str
		API key for Tavily. If provided, uses Tavily for enhanced search and parsing.
	
	Returns:
	-------
	dict
		Dictionary containing the company sector information
	"""
	# Base URLs and directories
	baseurl = "http://www.moneycontrol.com"
	base_dir = output_dir
	company_dir = base_dir + '/Companies'
	category_Company_dir = base_dir + '/Category-Companies'
	company_sector = {"companies": {}}
	
	# Tavily API endpoints
	TAVILY_SEARCH_URL = "https://api.tavily.com/search"
	TAVILY_QNA_URL = "https://api.tavily.com/qna"
	
	# Create TimeoutException for handling request timeouts
	class TimeoutException(Exception): pass
	
	@contextmanager
	def time_limit(seconds):
		def signal_handler(signum, frame):
			raise TimeoutException
		signal.signal(signal.SIGALRM, signal_handler)
		signal.alarm(seconds)
		try:
			yield
		finally:
			signal.alarm(0)
	
	# Create directories if they don't exist
	def ckdir(dir):
		if not os.path.exists(dir):
			os.makedirs(dir)
		return
	
	# Get response from URL
	def get_response(aurl):
		hdr = {'User-Agent': 'Mozilla/5.0'}
		
		while True:
			try:
				with time_limit(30):
					content = requests.get(aurl, headers=hdr).content
				break
			except Exception as e:
				print(f"Error opening url {aurl}: {str(e)}")
				continue
				
		return content
	
	# Get BeautifulSoup object from URL
	def get_soup(aurl):
		response = get_response(aurl)
		soup = BeautifulSoup(response, 'html.parser')
		return soup
	
	# Search for a company using Tavily API with direct HTTP request
	def search_company_tavily(company_name):
		if not tavily_api_key:
			return None
			
		print(f"Searching for company '{company_name}' using Tavily API")
		try:
			# Search for the company on MoneyControl using Tavily
			search_query = f"{company_name} site:moneycontrol.com company profile"
			
			headers = {
				"Content-Type": "application/json",
				"X-Api-Key": tavily_api_key
			}
			
			payload = {
				"query": search_query,
				"search_depth": "advanced",
				"include_domains": ["moneycontrol.com"]
			}
			
			response = requests.post(TAVILY_SEARCH_URL, headers=headers, json=payload)
			
			if response.status_code != 200:
				print(f"Tavily API error: {response.status_code} - {response.text}")
				return None
				
			search_result = response.json()
			
			# Extract relevant results
			for result in search_result.get('results', []):
				url = result.get('url', '')
				title = result.get('title', '')
				
				# Check if it's a company profile page
				if 'moneycontrol.com' in url and '/stocks/company' in url and company_name.lower() in title.lower():
					print(f"Found company: {title}")
					return {'name': title, 'url': url}
			
			print(f"No results found for {company_name} using Tavily search")
			return None
			
		except Exception as e:
			print(f"Error searching for company using Tavily: {str(e)}")
			return None
	
	# Search for a company using traditional scraping
	def search_company(company_name):
		# If Tavily API key is available, try using it first
		if tavily_api_key:
			result = search_company_tavily(company_name)
			if result:
				return result
			print("Falling back to traditional search method")
		
		search_url = f"https://www.moneycontrol.com/stocks/cptmarket/compsearchnew.php?search_data={company_name}&cid=&mbsearch_str=&topsearch_type=1&search_str={company_name}"
		soup = get_soup(search_url)
		
		try:
			# Find search results table
			table = soup.find('table', {'class': 'srch_tbl'})
			if not table:
				print(f"No results found for {company_name}")
				return None
				
			# Get the first matched company
			rows = table.find_all('tr')
			if len(rows) <= 1:  # Only header row
				print(f"No results found for {company_name}")
				return None
				
			company_link = rows[1].find('a')
			if company_link:
				company_url = company_link['href']
				company_full_name = company_link.text.strip()
				print(f"Found company: {company_full_name}")
				return {'name': company_full_name, 'url': company_url}
			else:
				print(f"No link found for {company_name}")
				return None
				
		except Exception as e:
			print(f"Error searching for company {company_name}: {str(e)}")
			return None
	
	# Parse company financials using Tavily API with direct HTTP request
	def parse_financials_tavily(company_name, company_url):
		if not tavily_api_key:
			return False
			
		print(f"Parsing financials for {company_name} using Tavily API")
		try:
			# Use Tavily to extract structured data
			query = f"Extract the latest quarterly and annual financial data for {company_name} from their MoneyControl page. Include revenue, profit, EPS, and balance sheet highlights."
			
			headers = {
				"Content-Type": "application/json",
				"X-Api-Key": tavily_api_key
			}
			
			payload = {
				"query": query,
				"search_depth": "advanced",
				"include_urls": [company_url],
				"max_tokens": 4000
			}
			
			response = requests.post(TAVILY_QNA_URL, headers=headers, json=payload)
			
			if response.status_code != 200:
				print(f"Tavily API error: {response.status_code} - {response.text}")
				return False
				
			result = response.json()
			
			# Save the Tavily analysis
			with open(f"{company_dir}/{company_name}-tavily-analysis.json", 'w') as outfile:
				json.dump(result, outfile, indent=2)
			
			print(f"Saved Tavily analysis for {company_name}")
			return True
		except Exception as e:
			print(f"Error using Tavily to parse financials: {str(e)}")
			return False
	
	# Get categories from URL
	def get_categories(aurl):
		soup = get_soup(aurl)
		links = {}
		tables = soup.find('div', {'class': 'lftmenu'})
		categories = tables.find_all('li')
		for category in categories:
			category_name = category.get_text()
			if category.find('a', {'class': 'act'}):
				links[category_name] = aurl
			else:
				links[category_name] = baseurl + category.find('a')['href']
		return links
	
	# Extract and save table values
	def get_values(soup, fname):
		try:
			data = soup.find_all('table', {'class': 'table4'})
			if not data or len(data) < 2:
				print(f"Warning: Table data not found for {fname}")
				return
				
			rows = data[1].find_all('tr')
			final_rows = []
			flag = 1
			while flag == 1:
				flag = 0
				final_rows = []
				for row in rows:
					if row.find('tr'):
						flag = 1
						inner_rows = row.find_all('tr')
						for inner_row in inner_rows:
							final_rows.append(inner_row)
					else:
						final_rows.append(row)
				
				rows = copy.copy(final_rows)
			
			rows = []
			
			with open(company_dir + '/' + fname, 'w') as outfile:
				for i in range(0, len(final_rows)):
					if not final_rows[i].get('height'):
						continue
					if final_rows[i].get('height') == '1px':
						break
						
					fields = final_rows[i].find_all('td')
					if not fields:
						continue
						
					try:
						fields[0] = re.sub(',', '/', fields[0].get_text())
						for j in range(1, len(fields)):
							fields[j] = re.sub(',', '', fields[j].get_text())
						
						for field in fields[:-1]:
							outfile.write(field + ",")
						outfile.write(fields[-1] + "\n")
					except Exception as e:
						print(f"Error processing row in {fname}: {str(e)}")
						continue
		except Exception as e:
			print(f"Error in get_values for {fname}: {str(e)}")
		
		return
	
	# Get data from different formats
	def get_Data(aurl, fname):
		try:
			soup = get_soup(aurl)
			og_table = soup.find('div', {'class': 'boxBg1'})
			if not og_table:
				print(f"Warning: No data found at {aurl}")
				return
				
			links = og_table.find('ul', {'class': 'tabnsdn FL'})
			if not links:
				print(f"Warning: No tab links found at {aurl}")
				return
				
			for link in links.find_all('li'):
				format_type = link.get_text()
				new_fname = fname + format_type + ".csv"
				if link.find('a', {'class': 'active'}):
					table = og_table
				else:
					web_address = baseurl + link.find('a')['href']
					new_soup = get_soup(web_address)
					table = new_soup.find('div', {'class': 'boxBg1'})
					
				get_values(table, new_fname)
		except Exception as e:
			print(f"Error in get_Data for {aurl}: {str(e)}")
			
		return
	
	# Get Profit & Loss data
	def get_PL_Data(aurl, aname):
		get_Data(aurl, aname + "-PL-")
		return
	
	# Get Balance Sheet data
	def get_BS_Data(aurl, aname):
		get_Data(aurl, aname + "-BS-")
		return
	
	# Get sector information
	def get_sector(asoup):
		sector = None
		
		try:
			details = asoup.find('div', {'class': 'FL gry10'})
			headers = details.get_text().split('|')
		except AttributeError:
			return sector
			
		for header in headers:
			if "SECTOR" in header:
				sector = header.split(':')[1].strip()
				break
				
		return sector
	
	# Get company data
	def get_Company_Data(aurl, aname):
		try:
			soup = get_soup(aurl)
			
			# Try using Tavily for enhanced parsing if available
			if tavily_api_key:
				tavily_success = parse_financials_tavily(aname, aurl)
				if tavily_success:
					# Still get the sector info for consistency
					company_sector["companies"][aname] = get_sector(soup)
					with open(base_dir + "/company-sector.json", 'w') as outfile:
						json.dump(company_sector, outfile)
					return
			
			# Fall back to traditional parsing
			temp = soup.find('dl', {'id': 'slider'})
			if not temp:
				print(f"Warning: Company data structure not found for {aname}")
				# Save what we can
				company_sector["companies"][aname] = get_sector(soup)
				with open(base_dir + "/company-sector.json", 'w') as outfile:
					json.dump(company_sector, outfile)
				return
				
			try:
				links = temp.find_all(['dt', 'dd'])
				
			except AttributeError:
				print("Data on '" + aname + "' doesn't exist anymore.")
				return
				
			index = -1
			for i in range(0, len(links)):
				if links[i].get_text() == 'FINANCIALS':
					index = i
					break
					
			if index != -1:
				fields = links[i + 1].find_all('a')
				
				required_link = None
				for field in fields:
					if field.get_text() == "Profit & Loss":
						required_link = baseurl + field['href']
						get_PL_Data(required_link, aname)
						
					if field.get_text() == "Balance Sheet":
						required_link = baseurl + field['href']
						get_BS_Data(required_link, aname)
						
			company_sector["companies"][aname] = get_sector(soup)
			
			with open(base_dir + "/company-sector.json", 'w') as outfile:
				json.dump(company_sector, outfile)
		except Exception as e:
			print(f"Error processing company data for {aname}: {str(e)}")
			
		return
	
	# Get list of companies in a category
	def get_list(aurl, category):
		details = []
		try:
			soup = get_soup(aurl)
			filters = soup.find_all('div', {'class': 'MT10'})
			if not filters or len(filters) < 4:
				print(f"Warning: Category structure not found for {category}")
				return details
				
			table_containers = filters[3].find_all('div', {'class': 'FL'})
			if not table_containers or len(table_containers) < 3:
				print(f"Warning: Table structure not found for {category}")
				return details
				
			table = table_containers[2]
			rows = table.find_all('tr')
			if not rows:
				print(f"Warning: No companies found in category {category}")
				return details
				
			headers = rows[0].find_all('th')
			labels = {}
			for i in range(0, len(headers)):
				labels[i] = headers[i].get_text()
				
			for row in rows[1:]:
				company = {}
				fields = row.find_all('td')
				for i in range(0, len(headers)):
					if i < len(fields):
						company[labels[i]] = fields[i].get_text()
				if len(fields) > 0 and fields[0].find('a'):
					company['link'] = baseurl + fields[0].find('a')['href']
					get_Company_Data(company['link'], company.get('Company Name', 'Unknown'))
				details.append(company)
				
			with open(category_Company_dir + '/' + category + '.json', 'w') as outfile:
				json.dump({'Company_details': details}, outfile)
		except Exception as e:
			print(f"Error processing category list for {category}: {str(e)}")
			
		return details
	
	# Get sector data
	def get_sector_data(category="Utilities"):
		try:
			with open(base_dir + "/categories.json", 'r') as infile:
				categories_data = json.load(infile)
		except FileNotFoundError:
			try:
				sector_url = 'http://www.moneycontrol.com/india/stockmarket/sector-classification/marketstatistics/nse/automotive.html'
				categories_data = get_categories(sector_url)
				with open(base_dir + '/categories.json', 'w') as outfile:
					json.dump(categories_data, outfile)
			except Exception as e:
				print(f"Error getting categories: {str(e)}")
				return None
		
		if category not in categories_data:
			print(f"Warning: Category {category} not found")
			return None
			
		category_url = categories_data[category]
		
		print("Accessing companies. Category: " + category)
		
		company_list = get_list(category_url, category)
		return company_list
	
	# Get alphabetical quotes
	def get_alpha_quotes(aurl):
		try:
			soup = get_soup(aurl)
			
			print(aurl)
			
			list_table = soup.find('table', {'class': 'pcq_tbl MT10'})
			if not list_table:
				print(f"Warning: No company list found at {aurl}")
				return
				
			companies = list_table.find_all('a')
			
			for company in companies[:]:
				if company.get_text() != '':
					print(company.get_text() + " : " + company['href'])
					get_Company_Data(company['href'], company.get_text())
		except Exception as e:
			print(f"Error processing alphabetical quotes at {aurl}: {str(e)}")
	
	# Get all quotes data
	def get_all_quotes_data():
		try:
			quote_list_url = 'http://www.moneycontrol.com/india/stockpricequote'
			soup = get_soup(quote_list_url)
			list_div = soup.find('div', {'class': 'MT2 PA10 brdb4px alph_pagn'})
			if not list_div:
				print("Warning: Alphabetical pagination not found")
				return
				
			links = list_div.find_all('a')
			
			for link in links[8:]:
				print("Accessing list for : " + link.get_text())
				get_alpha_quotes(baseurl + link['href'])
		except Exception as e:
			print(f"Error getting all quotes data: {str(e)}")
	
	# Initialize directories
	print("Initializing directories")
	ckdir(base_dir)
	ckdir(company_dir)
	ckdir(category_Company_dir)
	
	# Load existing company sector data if available
	try:
		with open(base_dir + "/company-sector.json", 'r') as infile:
			company_sector = json.load(infile)
	except FileNotFoundError:
		company_sector = {"companies": {}}
	
	# Process based on input parameters
	if company_names:
		print(f"Scraping data for specific companies: {company_names}")
		for company in company_names:
			# Search for the company URL
			company_data = search_company(company)
			if company_data:
				print(f"Scraping data for: {company_data['name']}")
				get_Company_Data(company_data['url'], company_data['name'])
			else:
				print(f"Could not find company: {company}")
	
	elif categories:
		print(f"Scraping data for categories: {categories}")
		for category in categories:
			get_sector_data(category)
	
	elif scrape_all:
		print("Scraping data for all companies")
		get_all_quotes_data()
	
	else:
		# Default behavior - scrape a single category
		get_sector_data("Utilities")
	
	return company_sector

# Example usage
if __name__ == '__main__':
	# Get Tavily API key from environment variable or set directly
	# You should set your Tavily API key here or as an environment variable
	import os
	tavily_api_key = os.environ.get("TAVILY_API_KEY")
	
	# For testing, you can directly set your API key here
	# tavily_api_key = "your-api-key-here"
	
	# Scrape data for specific companies using direct HTTP requests to Tavily API
	scrape_moneycontrol_data(company_names=["ITC"], tavily_api_key=tavily_api_key)