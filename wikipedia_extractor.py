#!/usr/bin/env python3
"""
Wikipedia Article Text Extractor

A self-contained script that searches Wikipedia for a given keyword,
downloads the most relevant article, extracts clean text content,
and saves it to a UTF-8 text file.

Usage: python wikipedia_extractor.py <keyword>
"""

import sys
import re
import urllib.parse
import urllib.request
from bs4 import BeautifulSoup


def search_wikipedia(keyword):
    """Search Wikipedia for the given keyword and return the most relevant article URL."""
    search_url = f"https://en.wikipedia.org/w/index.php?search={urllib.parse.quote(keyword)}&title=Special:Search&fulltext=1"
    
    try:
        with urllib.request.urlopen(search_url) as response:
            search_html = response.read().decode('utf-8')
        
        soup = BeautifulSoup(search_html, 'html.parser')
        
        # Look for the first search result
        result_links = soup.select('.mw-search-result-heading a')
        if result_links:
            first_result = result_links[0]
            article_title = first_result.get('title', '')
            article_url = f"https://en.wikipedia.org{first_result.get('href', '')}"
            return article_url, article_title
        
        # If no search results, try direct page access
        direct_url = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(keyword.replace(' ', '_'))}"
        return direct_url, keyword
        
    except Exception as e:
        print(f"Error searching Wikipedia: {e}", file=sys.stderr)
        sys.exit(1)


def download_article(url):
    """Download the full HTML content of a Wikipedia article."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        print(f"Error downloading article: {e}", file=sys.stderr)
        sys.exit(1)


def extract_clean_text(html_content):
    """Extract clean text content from Wikipedia article HTML."""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove unwanted elements
    for element in soup(['script', 'style', 'nav', 'aside', 'footer', 'header']):
        element.decompose()
    
    # Find the main content
    main_content = soup.find('div', {'id': 'mw-content-text'})
    if not main_content:
        print("Could not find main content in Wikipedia article", file=sys.stderr)
        sys.exit(1)
    
    # Find all paragraphs under the main heading
    paragraphs = []
    
    # Get the main heading (usually h1 or h2)
    main_heading = soup.find('h1', {'id': 'firstHeading'})
    if not main_heading:
        main_heading = soup.find('h1')
    
    # Start collecting paragraphs from after the main heading
    current = main_heading.find_next() if main_heading else main_content
    
    while current:
        if current.name == 'p':
            text = current.get_text(strip=True)
            if text:  # Only add non-empty paragraphs
                # Clean reference numbers and citation brackets
                text = re.sub(r'\[\d+\]', '', text)  # Remove [1], [2], etc.
                text = re.sub(r'\[citation needed\]', '', text, flags=re.IGNORECASE)
                text = re.sub(r'\[edit\]', '', text)
                text = re.sub(r'\s+', ' ', text).strip()  # Normalize whitespace
                if text:
                    paragraphs.append(text)
        elif current.name in ['h2', 'h3', 'h4', 'h5', 'h6']:
            # Stop at next major heading to avoid navigation/footer content
            break
        elif current.name == 'div' and 'reflist' in str(current.get('class', [])):
            # Skip reference sections
            break
        
        current = current.find_next()
    
    # Also collect paragraphs from the main content area
    all_paragraphs = main_content.find_all('p')
    for p in all_paragraphs:
        text = p.get_text(strip=True)
        if text and not any(parent.get('class') and 'reflist' in str(parent.get('class', [])) 
                           for parent in p.parents):
            text = re.sub(r'\[\d+\]', '', text)
            text = re.sub(r'\[citation needed\]', '', text, flags=re.IGNORECASE)
            text = re.sub(r'\[edit\]', '', text)
            text = re.sub(r'\s+', ' ', text).strip()
            if text and text not in paragraphs:
                paragraphs.append(text)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_paragraphs = []
    for para in paragraphs:
        if para not in seen:
            seen.add(para)
            unique_paragraphs.append(para)
    
    return unique_paragraphs


def save_text_to_file(keyword, paragraphs):
    """Save the extracted text to a UTF-8 file named <keyword>.txt."""
    filename = f"{keyword.replace(' ', '_').lower()}.txt"
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            for paragraph in paragraphs:
                f.write(paragraph + '\n\n')
        
        total_chars = sum(len(p) for p in paragraphs)
        print(f"Saved {len(paragraphs)} paragraphs ({total_chars} characters) to {filename}")
        return filename
        
    except Exception as e:
        print(f"Error saving file: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main function to orchestrate the Wikipedia extraction process."""
    if len(sys.argv) != 2:
        print("Usage: python wikipedia_extractor.py <keyword>", file=sys.stderr)
        sys.exit(1)
    
    keyword = sys.argv[1].strip()
    if not keyword:
        print("Please provide a non-empty keyword", file=sys.stderr)
        sys.exit(1)
    
    print(f"Searching Wikipedia for: {keyword}")
    
    # Search for the article
    article_url, article_title = search_wikipedia(keyword)
    print(f"Found article: {article_title}")
    
    # Download the article
    print("Downloading article...")
    html_content = download_article(article_url)
    
    # Extract clean text
    print("Extracting text content...")
    paragraphs = extract_clean_text(html_content)
    
    if not paragraphs:
        print("No text content found in the article", file=sys.stderr)
        sys.exit(1)
    
    # Save to file
    filename = save_text_to_file(keyword, paragraphs)
    
    return filename


if __name__ == "__main__":
    main()