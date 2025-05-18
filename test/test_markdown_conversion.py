import requests
from bs4 import BeautifulSoup
import sys
import os
import html2text
from urllib.parse import urlparse # Import urlparse for filename generation

# Add the project root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_conversion_from_url(url, output_dir="output_markdowns"):
    """
    Fetches HTML content from a URL, removes irrelevant elements,
    converts its body to Markdown, and saves it to a file.

    Args:
        url (str): The URL to fetch and convert.
        output_dir (str): Directory to save the markdown file.
    """
    print(f"Testing HTML to Markdown conversion from URL: {url}")

    try:
        response = requests.get(url, timeout=10) # Use a default timeout
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        html_content = response.content.decode(response.encoding or 'utf-8', errors='ignore')
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL {url}: {e}")
        return # Exit if fetching fails

    soup = BeautifulSoup(html_content, 'lxml')

    # --- Remove irrelevant elements ---
    irrelevant_selectors = [
        'nav', 'footer', 'script', 'style', 'header',
        '.header', '.footer', '.navigation', '.sidebar',
        '.menu', '.comments'
    ]
    print(f"Removing irrelevant elements using selectors: {irrelevant_selectors}")
    for selector in irrelevant_selectors:
        for element in soup.select(selector):
            element.decompose()
    # ----------------------------------

    # Extract the body content for conversion (after removing irrelevant elements)
    body_content = soup.find('body')

    if not body_content:
        print(f"Error: Could not find body content on {url}")
        return

    # Convert HTML to Markdown
    # Convert HTML to Markdown using html2text
    markdown_content = html2text.html2text(str(body_content))

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Generate filename based on URL basename
    parsed_url = urlparse(url)
    filename_base = os.path.basename(parsed_url.path).replace('.', '_')
    if not filename_base:
        filename_base = "converted_page"

    # Sanitize filename (basic sanitization)
    filename = "".join([c for c in filename_base if c.isalnum() or c in ('_', '-')])
    filename = filename.strip('_-')
    if not filename:
         filename = "converted_page"

    markdown_filename = os.path.join(output_dir, f"{filename}.md")

    # Ensure filename uniqueness (simple approach: append a counter if file exists)
    original_filename = filename
    counter = 1
    while os.path.exists(markdown_filename):
        filename = f"{original_filename}_{counter}"
        markdown_filename = os.path.join(output_dir, f"{filename}.md")
        counter += 1

    # Save Markdown file
    try:
        with open(markdown_filename, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        print(f"Successfully saved converted markdown to {markdown_filename}")
    except IOError as e:
        print(f"Error saving file {markdown_filename}: {e}")


if __name__ == "__main__":
    # --- User Configuration ---
    # IMPORTANT: Replace this with a real URL for testing
    test_url = "https://go.dev/doc/modules/developing"
    test_output_dir = "output_markdowns" # Directory to save the output
    # --------------------------

    if test_url == "YOUR_TEST_URL_HERE":
        print("Please update 'test_url' in test_live_markdown_conversion.py with an actual URL before running the test.")
    else:
        test_conversion_from_url(test_url, test_output_dir)