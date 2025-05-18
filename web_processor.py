# web_processor.py

import requests
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin, urlparse, urlunparse
import logging
import time
import random
import html2text

# Configure logging (basic configuration, can be moved to main.py for more control)
def process_document(start_url, link_source_selector, main_content_selector=None,
                     output_dir="output_markdowns", timeout=10,
                     min_delay=1.0, max_delay=5.0, max_retry_duration=15):
    """
    Fetches a web document, extracts links from a specified HTML element based on ID and class,
    filters them by the parent directory of the start_url,
    fetches each filtered linked page, removes irrelevant elements,
    converts its main content to Markdown, and saves it to a file structure
    mirroring the URL subpaths.

    Args:
        start_url (str): The URL of the starting page.
        link_source_selector (str): Specifies the ID or Class name of the HTML element that contains the navigation links (e.g., a sidebar, a navigation menu, or any other container). The script will first attempt to find an element with the provided string as an ID, and if not found, it will try to find an element with the provided string as a Class name.
        main_content_selector (str, optional): CSS selector for the main content area.
                                               Defaults to None, which extracts the body.
        output_dir (str): Directory to save the markdown files.
        timeout (int): Timeout for HTTP requests in seconds.
        min_delay (float): Minimum random delay between requests in seconds.
        max_delay (float): Maximum random delay between requests in seconds.
        max_retry_duration (int): Maximum duration for retries in seconds.
    """
    logging.info(f"Fetching starting page: {start_url}")

    # Add retry logic for fetching the starting page
    start_time = time.time()
    while True:
        elapsed_time = time.time() - start_time
        if elapsed_time > max_retry_duration:
            logging.error(f"Failed to fetch starting page {start_url} after {max_retry_duration} seconds.")
            return # Give up after max retry duration

        try:
            response = requests.get(start_url, timeout=timeout) # Use timeout parameter
            response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
            # Use detected encoding, fallback to utf-8
            html_content = response.content.decode(response.encoding or 'utf-8', errors='ignore')
            break # Success, exit retry loop
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to fetch starting page {start_url}: {e}. Retrying...")
            time.sleep(random.uniform(min_delay, max_delay)) # Use delay parameters

    soup = BeautifulSoup(html_content, 'lxml')

    # Try finding sidebar by ID first
    link_source_element = soup.find(id=link_source_selector)
    found_by = "ID"

    # If not found by ID, try finding by Class
    if not link_source_element:
        link_source_element = soup.find(class_=link_source_selector)
        found_by = "Class"

    if not link_source_element:
        logging.error(f"Error: Link source element with ID or Class '{link_source_selector}' not found on {start_url}")
        return

    logging.info(f"Found link source element by {found_by}: '{link_source_selector}'.")

    # Find links within the found link source element
    links = link_source_element.find_all('a', href=True)
    logging.info(f"Searching for all links within the found link source element.")


    if not links:
        logging.warning(f"No links found in the element with ID or Class '{link_source_selector}'.")
        return

    logging.info(f"Found {len(links)} potential links in the specified element.")

    # --- Filter links by parent directory, remove fragments, and deduplicate ---
    parsed_start_url = urlparse(start_url)
    # Get the parent directory path, ensuring it ends with a slash
    parent_path = os.path.dirname(parsed_start_url.path)
    if not parent_path.endswith('/'):
        parent_path += '/'
    # Reconstruct the parent URL (without fragment) for comparison
    parent_url_base = urlunparse((parsed_start_url.scheme, parsed_start_url.netloc, parent_path, '', '', ''))

    logging.info(f"Filtering links to match parent directory: {parent_url_base}")

    # Use a dictionary to store unique links (URL without fragment as key)
    # and their original link tag and full URL as value
    unique_links_map = {}
    for link in links:
        href = link.get('href') # Use .get() for safer access
        if not href:
            continue # Skip links without href

        link_url = urljoin(start_url, href) # Handle relative URLs

        # Remove fragment for comparison and deduplication
        parsed_link_url = urlparse(link_url)
        url_without_fragment = urlunparse(parsed_link_url._replace(fragment=''))

        # Filter by parent directory and check for uniqueness (based on URL without fragment)
        if url_without_fragment.startswith(parent_url_base) and url_without_fragment not in unique_links_map:
            unique_links_map[url_without_fragment] = (link, link_url) # Store original link tag and full URL

    # Convert the unique links map values back to a list of (link_tag, link_url) tuples
    filtered_links_info = list(unique_links_map.values())

    # -------------------------------------------------------------------------

    if not filtered_links_info:
        logging.warning(f"After filtering, removing fragments, and deduplicating, no unique links remain matching the parent directory '{parent_url_base}'. Skipping further processing.")
        return

    logging.info(f"Found {len(filtered_links_info)} unique filtered links matching the parent directory (fragments removed). Processing...")

    # Create the base output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True) # Use output_dir parameter

    # Determine the base path for relative directory calculation based on start_url
    parsed_start_url_path = urlparse(start_url).path
    # Get the directory containing the last component of the start_url path
    base_path_for_relative = os.path.dirname(parsed_start_url_path)
    # If the base path is empty (e.g., start_url is just domain/file.html), use the root '/'
    if not base_path_for_relative:
        base_path_for_relative = '/'
    # Ensure base_path_for_relative ends with a slash for consistent relative path calculation
    if not base_path_for_relative.endswith('/'):
        base_path_for_relative += '/'

    # Determine the root directory name for the output structure
    # This is the last component of the base_path_for_relative
    output_root_name = os.path.basename(os.path.normpath(base_path_for_relative))


    # Iterate over filtered links
    for link_tag, link_url in filtered_links_info: # Use link_tag and original link_url here
        logging.info(f"Fetching linked page: {link_url}")

        # Recalculate url_without_fragment for the current link
        parsed_link_url = urlparse(link_url)
        url_without_fragment = urlunparse(parsed_link_url._replace(fragment=''))
 
        # Add retry logic for fetching linked pages
        link_start_time = time.time()
        while True:
            link_elapsed_time = time.time() - link_start_time
            if link_elapsed_time > max_retry_duration:
                logging.error(f"Failed to fetch linked page {link_url} after {max_retry_duration} seconds.")
                linked_page_html = None # Indicate failure
                break # Give up after max retry duration

            try:
                link_response = requests.get(link_url, timeout=timeout) # Use timeout parameter
                link_response.raise_for_status()
                # Use detected encoding, fallback to utf-8
                linked_page_html = link_response.content.decode(link_response.encoding or 'utf-8', errors='ignore')
                break # Success, exit retry loop
            except requests.exceptions.RequestException as e:
                logging.error(f"Failed to fetch linked page {link_url}: {e}. Retrying...")
                time.sleep(random.uniform(min_delay, max_delay)) # Use delay parameters

        if linked_page_html is None:
            continue # Skip to the next link if fetching failed after retries
 
        link_soup = BeautifulSoup(linked_page_html, 'lxml')
 
        # --- Remove irrelevant elements ---
        irrelevant_selectors = [
            'nav', 'footer', 'script', 'style', 'header',
            '.header', '.footer', '.navigation', '.sidebar',
            '.menu', '.comments'
        ]
        # logging.info(f"Removing irrelevant elements from {url_without_fragment} using selectors: {irrelevant_selectors}") # Use url_without_fragment for logging
        for selector in irrelevant_selectors:
            for element in link_soup.select(selector):
                element.decompose()
        # ----------------------------------


        # --- Extract Main Content ---
        main_content_element = None
        if main_content_selector:
            main_content_element = link_soup.select_one(main_content_selector)
            if not main_content_element:
                logging.warning(f"Warning: Could not find element with selector '{main_content_selector}' for {url_without_fragment}. Falling back to body content.") # Use url_without_fragment for logging

        # If selector not provided or element not found, fallback to heuristic search
        if not main_content_element:
            # logging.info(f"Attempting heuristic main content extraction for {url_without_fragment}...") # Use url_without_fragment for logging
            # Find all potential content containers (e.g., div, article, main)
            potential_content_elements = link_soup.find_all(['div', 'article', 'main'])

            best_element = None
            max_text_length = 0

            for element in potential_content_elements:
                text_length = len(element.get_text(strip=True))
                # Consider elements with significant text content
                if text_length > 100: # Threshold for minimum text length
                    if text_length > max_text_length:
                        max_text_length = text_length
                        best_element = element

            if best_element:
                main_content_element = best_element
                logging.info(f"Heuristic extraction found a potential main content element with {max_text_length} characters for {url_without_fragment}.") # Use url_without_fragment for logging
            else:
                 # Final fallback to body if heuristic fails
                 logging.warning(f"Heuristic extraction failed for {url_without_fragment}. Falling back to body content.") # Use url_without_fragment for logging
                 main_content_element = link_soup.find('body')


        if not main_content_element:
              logging.warning(f"Warning: Could not find any main content (selector, heuristic, or body) for {url_without_fragment}. Skipping.") # Use url_without_fragment for logging
              continue

        main_content_html = str(main_content_element)
        # ----------------------------

        # Convert HTML to Markdown
        markdown_content = html2text.html2text(main_content_html)

        # Generate filename
        # Try to use page title, fallback to link text, then URL basename
        page_title = link_soup.title.string if link_soup.title else None
        # Use the original link tag from filtered_links_info to get link text
        link_text = link_tag.get_text(strip=True) # Use the link_tag passed in the loop


        if link_text:
            filename_base = link_text
        # elif page_title:
        #     filename_base = page_title
        else:
            # Use the URL without fragment for filename generation
            filename_base = os.path.basename(urlparse(url_without_fragment).path).replace('.', '_')


        # Sanitize filename: convert to lowercase, replace spaces with underscores,
        # remove invalid characters, and trim leading/trailing underscores/hyphens
        filename = filename_base.lower()
        filename = filename.replace(' ', '_')
        # Remove characters that are not alphanumeric, underscore, or hyphen
        filename = "".join([c for c in filename if c.isalnum() or c in ('_', '-')])
        # Remove leading/trailing underscores or hyphens
        filename = filename.strip('_-')


        if not filename:
            filename = "untitled_page"

        # --- Create subdirectories based on URL path and build full file path ---
        # Use the URL without fragment for directory structure
        parsed_link_url_without_fragment = urlparse(url_without_fragment)
        link_path = parsed_link_url_without_fragment.path

        # Calculate the relative path of the link URL's path to the base path
        try:
            relative_link_path = os.path.relpath(link_path, base_path_for_relative)
        except ValueError:
             # Handle cases where link_path is not under base_path_for_relative (should be filtered out, but as a safeguard)
             logging.warning(f"Link path {link_path} is not relative to base path {base_path_for_relative}. Skipping.")
             continue

        # Get the directory part of the relative path
        relative_output_subdir = os.path.dirname(relative_link_path)

        # Construct the final output directory path
        if output_root_name:
            file_output_dir = os.path.join(output_dir, output_root_name, relative_output_subdir)
        else:
            # If output_root_name is empty (e.g., start_url was domain/file.html or domain/),
            # the relative path is already correct relative to output_dir
            file_output_dir = os.path.join(output_dir, relative_output_subdir)

        # Remove leading './' if present in relative_output_subdir
        if file_output_dir.startswith('./') or file_output_dir.startswith('.\\'):
             file_output_dir = file_output_dir[2:]

        # Create the subdirectory if it doesn't exist
        os.makedirs(file_output_dir, exist_ok=True)

        # Combine the directory path and filename
        markdown_filename = os.path.join(file_output_dir, f"{filename}.md")
        # -----------------------------------------------------------------------


        # Ensure filename uniqueness (simple approach: append a counter if file exists)
        original_filename = filename
        counter = 1
        # Check for uniqueness in the specific subdirectory
        while os.path.exists(markdown_filename):
            filename = f"{original_filename}_{counter}"
            markdown_filename = os.path.join(file_output_dir, f"{filename}.md") # Check in the correct directory
            counter += 1

        # Save Markdown file
        try:
            with open(markdown_filename, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            logging.info(f"Successfully saved {markdown_filename}")
        except IOError as e:
                logging.error(f"Error saving file {markdown_filename}: {e}")
