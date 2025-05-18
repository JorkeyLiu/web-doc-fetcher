import os
import shutil
import sys
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urlunparse # Import urlparse and urlunparse

# Add the project root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# import web_processor # No longer needed for this test

def run_basic_test(test_url, sidebar_spec):
    """
    Fetches the starting page, extracts links from the sidebar based on ID and class,
    filters them by the parent directory of the test_url, and prints the filtered URLs.

    Args:
        test_url (str): The URL of the starting page with the sidebar.
        sidebar_spec (str): Specifies the sidebar ID and optional link class in the format "id:class" or just "id".
    """
    print(f"Starting basic test for URL: {test_url} with sidebar specification: {sidebar_spec}")

    # Parse sidebar_spec
    parts = sidebar_spec.split(':', 1)
    sidebar_id = parts[0]

    try:
        response = requests.get(test_url, timeout=10) # Use a default timeout
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        html_content = response.content.decode(response.encoding or 'utf-8', errors='ignore')
    except requests.exceptions.RequestException as e:
        print(f"Error fetching starting page {test_url}: {e}")
        return # Exit if fetching fails

    soup = BeautifulSoup(html_content, 'lxml')

    # Try finding sidebar by ID first
    sidebar = soup.find(id=sidebar_spec)
    found_by = "ID"

    # If not found by ID, try finding by Class
    if not sidebar:
        sidebar = soup.find(class_=sidebar_spec)
        found_by = "Class"

    if not sidebar:
        print(f"Error: Sidebar element with ID or Class '{sidebar_spec}' not found on {test_url}")
        return

    print(f"Found sidebar element by {found_by}: '{sidebar_spec}'.")

    # Find links within the sidebar, optionally filtered by class
    links = sidebar.find_all('a', href=True)
    print(f"Searching for all links within the found sidebar element.")


    if not links:
        print(f"No links found in the sidebar with ID '{sidebar_id}'.")
        return

    # --- Filter links by parent directory, remove fragments, and deduplicate ---
    parsed_test_url = urlparse(test_url)
    # Get the parent directory path, ensuring it ends with a slash
    parent_path = os.path.dirname(parsed_test_url.path)
    if not parent_path.endswith('/'):
        parent_path += '/'
    # Reconstruct the parent URL (without fragment) for comparison
    parent_url_base = urlunparse((parsed_test_url.scheme, parsed_test_url.netloc, parent_path, '', '', ''))

    print(f"Filtering links to match parent directory: {parent_url_base}")
    
    # Step 1: Filter by parent directory
    parent_filtered_links = []
    for link in links:
        href = link['href']
        link_url = urljoin(test_url, href) # Handle relative URLs
        if link_url.startswith(parent_url_base):
            parent_filtered_links.append(link_url)

    if not parent_filtered_links:
        print(f"No links found matching the parent directory '{parent_url_base}'.")
        return

    # Step 2: Remove fragments
    links_without_fragments = []
    for link_url in parent_filtered_links:
        parsed_url = urlparse(link_url)
        url_without_fragment = urlunparse(parsed_url._replace(fragment=''))
        links_without_fragments.append(url_without_fragment)

    # Step 3: Deduplicate
    unique_links = list(set(links_without_fragments))

    # -------------------------------------------------------------------------

    if not unique_links:
        print(f"After removing fragments and deduplicating, no unique links remain matching the parent directory '{parent_url_base}'.")
        return

    print(f"Found {len(unique_links)} unique links matching the parent directory (fragments removed). Printing URLs:")

    for link_url in unique_links:
        print(link_url)

    # No return value needed for this modified test


if __name__ == "__main__":
    # --- User Configuration ---
    # IMPORTANT: Replace these with a real URL and sidebar specification for testing
    # Format: "sidebar_id:link_class" or just "sidebar_id"
    test_url = "https://docs.pytorch.org/docs/stable/index.html"
    test_spec = "pytorch-documentation"
    # test_url = "https://docs.python.org/3/installing/index.html"
    # test_spec = "sphinxsidebarwrapper"
    # --------------------------

    if test_url == "YOUR_TEST_URL_HERE" or test_spec == "YOUR_SIDEBAR_ID_HERE": # Update check for test_spec
        print("Please update 'test_url' and 'test_spec' in test_web_processor.py with actual values before running the test.")
    else:
        print("Running basic test...")
        run_basic_test(test_url, test_spec)