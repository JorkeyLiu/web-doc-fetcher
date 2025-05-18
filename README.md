# web-doc-fetcher

A Python tool designed to fetch web documentation by extracting links from a specified HTML element, process its content, and convert it into clean Markdown format.

## Features

- **Navigation Link Extraction**: Locates an HTML element containing navigation links based on a provided ID or Class name and extracts the links.
- **Link Filtering and Deduplication**: Filters extracted links to ensure they are within the parent directory structure of the starting URL, removes URL fragments, and deduplicates links.
- **Content Fetching and Processing**: Fetches each linked page found. Supports configurable timeouts, random delays between requests, and retry logic for improved robustness.
- **HTML Cleaning**: Removes irrelevant elements such as navigation, footers, scripts, styles, and headers from the fetched pages.
- **Main Content Extraction**: Extracts the primary content area of a page using either a user-provided CSS selector or a heuristic method that identifies elements with rich text content.
- **HTML to Markdown Conversion**: Converts the extracted main HTML content into a clean and readable Markdown format.

## Installation

1.  **Clone or download this repository.**

2.  **Create a virtual environment:**

    ```bash
    # Create the conda environment with Python 3.11.12
    conda create -n web-doc-fetcher python=3.11.12

    # Activate the environment
    conda activate web-doc-fetcher
    ```

3.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

## Usage

To use the tool, navigate to the project directory in your terminal and run the main script with the required arguments:

```bash
python main.py <start_url> <link_source_selector> [optional_arguments]
```

*   `<start_url>`: The URL of the starting page. This page **must** contain all the documentation directory links.
*   `<link_source_selector>`: Specifies the ID or Class name of the HTML element that contains the navigation links, commonly it is a sidebar(e.g., `sidebar-nav`, `menu-list`, `main-navigation`). The script will first attempt to find an element with the provided string as an ID, and if not found, it will try to find an element with the provided string as a Class name. **Do not include CSS selector prefixes like `#` for IDs or `.` for Classes.**

**Optional Arguments:**

*   `--main-content-selector SELECTOR`: CSS selector for the main content area. If not provided, the tool will attempt to extract the body content or use a heuristic.
*   `--output-dir DIRECTORY`: Directory to save the markdown files (default: `output_markdowns`).
*   `--timeout SECONDS`: Timeout for HTTP requests in seconds (default: 10).
*   `--min-delay SECONDS`: Minimum random delay between requests in seconds (default: 1.0).
*   `--max-delay SECONDS`: Maximum random delay between requests in seconds (default: 5.0).
*   `--max-retry-duration SECONDS`: Maximum duration for retries in seconds (default: 15).

**Example:**

```bash
python main.py https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/installation.html pst-primary-sidebar
```

## Contributing

Contributions are welcome! If you find issues or have suggestions for improvements, please feel free to:

- Report issues on the issue tracker.
- Suggest improvements.
- Submit pull requests.

## License

This project is licensed under MIT License. Please see the LICENSE file for details.