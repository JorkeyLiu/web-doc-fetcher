# main.py

import argparse
import logging
from web_processor import process_document

if __name__ == "__main__":
    # Configure basic logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # Set up argument parser
    parser = argparse.ArgumentParser(description="Fetch web documentation by extracting links from a specified HTML element and convert to Markdown.")
    parser.add_argument("start_url", help="The URL of the starting page.")
    parser.add_argument("link_source_selector", help="Specifies the ID or Class name of the HTML element that contains the navigation links.")
    parser.add_argument("--main-content-selector", help="CSS selector for the main content area (optional). If not provided, the body content will be extracted.", default=None)
    parser.add_argument("--output-dir", help="Directory to save the markdown files.", default="output_markdowns")
    parser.add_argument("--timeout", type=int, help="Timeout for HTTP requests in seconds.", default=10)
    parser.add_argument("--min-delay", type=float, help="Minimum random delay between requests in seconds.", default=1.0)
    parser.add_argument("--max-delay", type=float, help="Maximum random delay between requests in seconds.", default=5.0)
    parser.add_argument("--max-retry-duration", type=int, help="Maximum duration for retries in seconds.", default=15)


    args = parser.parse_args()

    # Call the main processing function with the new sidebar_spec argument
    process_document(args.start_url, args.link_source_selector, args.main_content_selector,
                     output_dir=args.output_dir,
                     timeout=args.timeout,
                     min_delay=args.min_delay,
                     max_delay=args.max_delay,
                     max_retry_duration=args.max_retry_duration)