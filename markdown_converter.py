from playwright.sync_api import sync_playwright
import os
import time
import platform # Added to check OS
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup


DATE_TIME_STAMP = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")



CHROME_DEBUGGING_PORT = 9222
WAIT_TIME = 1  # Seconds to wait for rendering to complete
DELAY_BETWEEN_FILES = 0.5  # Seconds to wait between processing files

CSS_PLACEHOLDER = "chrome-extension://ckkdlimhmcjmikdlpkmbgfkaikojcbjk"
PRISM_PLACEHOLDER = "prism.min.css"
PRISM = "prism-okaidia.min.css"

THEME_PLACEHOLDER = "github.css"
THEME = "github-dark.css"


# New configuration for refresh mechanism
MAX_RETRIES = 3
RETRY_TIMEOUT = 5_000  # 5 seconds in milliseconds

# Windows MAX_PATH warning threshold
WINDOWS_MAX_PATH_THRESHOLD = 250 # Warn if path exceeds this on Windows

# CSS for the copy button functionality
COPY_BUTTON_STYLES = """
.pre-container {
    position: relative;
}

.copy-btn {
    position: absolute;
    top: 5px;
    right: 5px;
    padding: 3px 8px;
    font-size: 12px;
    background-color: #800000; /* Maroon */
    color: white;
    border: 1px solid #5c0000; /* Darker maroon */
    border-radius: 3px;
    cursor: pointer;
    transition: background-color 0.2s ease;
}

.copy-btn:hover {
    background-color: #a00000; /* Lighter maroon on hover */
}

.copy-btn.copied {
    background-color: #006400; /* Dark Green */
    border-color: #004d00;
    color: white;
}

.copy-btn.failed {
    background-color: #dc3545; /* Red */
    border-color: #c82333;
    color: white;
}
"""

# JavaScript for the copy to clipboard functionality
COPY_TO_CLIPBOARD_SCRIPT = """
document.addEventListener('DOMContentLoaded', function() {
  const preTags = document.querySelectorAll('pre');
  
  preTags.forEach(function(pre) {
    const existingContainer = pre.closest('.pre-container');
    if (existingContainer) {
      // If pre is already in a container (e.g. script ran multiple times or manual structure)
      // Ensure button is there or add it. For simplicity, we assume if container exists, button might too.
      // A more robust check would be to see if a .copy-btn already exists for this pre.
      // For now, let's prevent adding duplicate buttons if script re-runs on dynamic content.
      if (existingContainer.querySelector('.copy-btn')) {
          return; // Skip if button already there
      }
    }

    const container = document.createElement('div');
    container.className = 'pre-container';
    
    const copyBtn = document.createElement('button');
    copyBtn.textContent = 'Copy';
    copyBtn.className = 'copy-btn';
    
    copyBtn.addEventListener('click', function() {
      const textToCopy = pre.innerText || pre.textContent; // .innerText is often better for user-visible text
      navigator.clipboard.writeText(textToCopy).then(
        function() {
          const originalText = copyBtn.textContent;
          copyBtn.textContent = 'Copied!';
          copyBtn.classList.add('copied');
          copyBtn.classList.remove('failed');
          
          setTimeout(function() {
            copyBtn.textContent = originalText;
            copyBtn.classList.remove('copied');
          }, 2000);
        },
        function() {
          const originalText = copyBtn.textContent;
          copyBtn.textContent = 'Failed!';
          copyBtn.classList.add('failed');
          copyBtn.classList.remove('copied');
          
          setTimeout(function() {
            copyBtn.textContent = originalText;
            copyBtn.classList.remove('failed');
          }, 2000);
        }
      );
    });
    
    // Structure: parent -> container -> pre & button
    if (pre.parentNode) {
        pre.parentNode.insertBefore(container, pre);
    }
    container.appendChild(pre); // Move pre into container
    container.appendChild(copyBtn); // Add button to container
  });
});
"""

correction_text = '''
./icons/default/16x16.png --> ./style/icons/default/16x16.png
./themes/github-dark.css --> ./style/themes/github-dark.css
./themes/github-light.css --> ./style/themes/github-light.css
./themes/github-dark-compact.css --> ./style/themes/github-dark-compact.css
'''

def correct_style_path(content):
    png_path = './icons/default/16x16.png'
    theme_dark = './themes/github-dark.css'
    theme_light = './themes/github-light.css'
    theme_dark_compact = './themes/github-dark-compact.css'
    result = content.replace(png_path, './style/icons/default/16x16.png')
    result = result.replace(theme_dark, './style/themes/github-dark.css')
    result = result.replace(theme_light, './style/themes/github-light.css')
    result = result.replace(theme_dark_compact, './style/themes/github-dark-compact.css')
    return result
    


def customize_css_and_add_scripts(html_content):
    soup = BeautifulSoup(html_content, "html.parser")

    if soup.body:
        css_links = soup.body.find_all(
            "link", attrs={"rel": "stylesheet", "type": "text/css"}
        )
        for link in css_links:
            link.extract()
            if soup.head:
                soup.head.append(link)
            else: # If no head, create one (shouldn't happen with valid HTML from playwright)
                head = soup.new_tag("head")
                soup.insert(0, head) # Insert head at the beginning of html element
                soup.head.append(link)


    if not soup.head: # Ensure head exists
        head_tag = soup.new_tag("head")
        if soup.html:
            soup.html.insert(0, head_tag)
        else: # If no html tag, wrap content in html and add head (very unlikely)
            current_contents = soup.contents
            html_tag = soup.new_tag("html")
            soup.append(html_tag)
            for item in current_contents:
                item.extract()
                html_tag.append(item)
            html_tag.insert(0, head_tag)

    custom_link = soup.new_tag("link")
    custom_link["rel"] = "stylesheet"
    custom_link["href"] = "./style/style.css" # Assuming style.css is in the same dir as output HTML
    custom_link["defer"] = "" 
    soup.head.append(custom_link)

    style_tag = soup.new_tag("style")
    style_tag.string = COPY_BUTTON_STYLES
    soup.head.append(style_tag)

    script_tag = soup.new_tag("script")
    script_tag.string = COPY_TO_CLIPBOARD_SCRIPT
    
    if soup.body:
        soup.body.append(script_tag)
    else: # If no body, append to html tag (fallback)
        soup.append(script_tag)

    return str(soup)


def wrap_html_children_in_container(html_string):
    soup = BeautifulSoup(html_string, "html.parser")
    parent_div = soup.find("div", id="_html")

    if parent_div:
        # Check if 'akbar_container' already exists to prevent re-wrapping
        if not parent_div.find("div", class_="akbar_container", recursive=False):
            container_div = soup.new_tag("div", attrs={"class": "akbar_container"})
            for child in list(parent_div.children):
                child.extract()
                container_div.append(child)
            parent_div.append(container_div)
    return str(soup)


md_files_path_input = input("Enter the path to the markdown files: ")
# Use abspath to handle cases like '.' or '..' robustly for basename
md_files_path_abs = os.path.abspath(md_files_path_input)
md_files_path_base_name = os.path.basename(md_files_path_abs)


OUTPUT_HTML_PATH = f"./{md_files_path_base_name}_HTML_{DATE_TIME_STAMP}"
Path(OUTPUT_HTML_PATH).mkdir(parents=True, exist_ok=True)


list_txt = []
for root, dirs, files in os.walk(md_files_path_input): # Use original input for walk
    for file in files:
        if file.endswith(".md"):
            list_txt.append(os.path.join(root, file).replace(os.sep, "/"))

print(f"Files Count: {len(list_txt)}")


def render_markdown_to_html(markdown_file_path, input_folder_basename):
    markdown_abs_path = os.path.abspath(markdown_file_path)

    # --- BEGIN LONG PATH CHECK ---
    if platform.system() == "Windows" and len(markdown_abs_path) > WINDOWS_MAX_PATH_THRESHOLD:
        error_message = (
            f"\n--------------------------------------------------------------------\n"
            f"WARNING: SKIPPING FILE DUE TO LONG PATH ON WINDOWS.\n"
            f"File: {markdown_file_path}\n"
            f"Absolute Path: {markdown_abs_path}\n"
            f"Path Length: {len(markdown_abs_path)} characters (Threshold: {WINDOWS_MAX_PATH_THRESHOLD})\n\n"
            f"On Windows, file paths longer than ~260 characters can lead to 'File Not Found' errors \n"
            f"by browsers and other applications, even if the file exists.\n\n"
            f"To resolve this, you can:\n"
            f"1. Move your project folder ('{input_folder_basename}') to a location with a shorter base path \n"
            f"   (e.g., directly under C:\\, like C:\\my_project\\{input_folder_basename}).\n"
            f"2. Enable Win32 long path support in Windows. This requires administrator rights and typically a system reboot.\n"
            f"   (Search online for 'Enable Win32 long paths' for instructions for your Windows version).\n"
            f"--------------------------------------------------------------------\n"
        )
        print(error_message)
        # Raise a specific exception that the main loop can catch.
        raise FileNotFoundError(f"Path too long for Windows (>{WINDOWS_MAX_PATH_THRESHOLD} chars): {markdown_abs_path}")
    # --- END LONG PATH CHECK ---

    file_url = f"file:///{markdown_abs_path.replace(os.sep, '/')}"
    print(f"Processing: {file_url}")

    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp(
                f"http://localhost:{CHROME_DEBUGGING_PORT}"
            )
            context = browser.contexts[0] if browser.contexts else browser.new_context()
            page = context.new_page()

            retries = 0
            selector_found = False

            while retries < MAX_RETRIES and not selector_found:
                print(
                    f"Navigating to markdown file (attempt {retries + 1}/{MAX_RETRIES})"
                )
                try:
                    # Added timeout to goto itself to prevent indefinite hang on file not found
                    page.goto(file_url, timeout=RETRY_TIMEOUT * 2, wait_until="domcontentloaded") # wait_until might be 'load' or 'networkidle'
                except Exception as nav_error:
                    # If navigation itself fails (e.g. ERR_FILE_NOT_FOUND not caught by path length check)
                    print(f"Error during page.goto(): {nav_error}")
                    if "net::ERR_FILE_NOT_FOUND" in str(nav_error):
                         print(f"Hint: This could still be a path length issue if not caught by the pre-check, or the file truly doesn't exist at {markdown_abs_path}")
                    # We will re-raise after finally block to ensure page is closed
                    raise 

                try:
                    selectors = ["#_html", ".markdown-body", ".markdown-theme", "body[data-vscode-theme-name]"] # Added VSCode specific one
                    for selector in selectors:
                        try:
                            page.wait_for_selector(
                                selector, state="visible", timeout=RETRY_TIMEOUT
                            )
                            print(f"Found rendered content with selector: {selector}")
                            selector_found = True
                            break
                        except:
                            continue
                    
                    if selector_found:
                        break

                    print(
                        f"No expected content selector found after {RETRY_TIMEOUT/1000} seconds, refreshing page..."
                    )
                    retries += 1
                    if retries < MAX_RETRIES:
                        page.reload(wait_until="domcontentloaded") # Try reloading
                    else:
                        print("Max retries reached for finding selector.")

                except Exception as e: # Catch timeout from wait_for_selector
                    print(f"Warning: Could not detect rendered content via selectors: {e}")
                    retries += 1
                    if retries < MAX_RETRIES:
                        print(f"Refreshing page (attempt {retries}/{MAX_RETRIES})...")
                        page.reload(wait_until="domcontentloaded")
                    else:
                        print("Max retries reached after selector timeout.")


            if not selector_found:
                print(
                    "Warning: Could not find any expected content selectors after all retries. Will attempt to get content anyway."
                )

            print(f"Waiting {WAIT_TIME} seconds for complete rendering...")
            time.sleep(WAIT_TIME)

            html_content = page.content()

            # Check for minimal content, sometimes even if selectors fail, basic HTML is there
            if not html_content or len(html_content) < 200: # Arbitrary small number
                print("Warning: Retrieved HTML content is very short. The page might not have rendered correctly.")
                # Potentially raise an error here if empty HTML is a critical failure
                # raise Exception("Retrieved HTML content is too short or empty.")


            html_content = html_content.replace(CSS_PLACEHOLDER, ".")
            html_content = html_content.replace(PRISM_PLACEHOLDER, PRISM)
            html_content = html_content.replace(THEME_PLACEHOLDER, THEME)
            html_content = wrap_html_children_in_container(html_content)
            html_content = customize_css_and_add_scripts(html_content)

            file_name = os.path.basename(markdown_file_path)
            html_file_name = file_name.replace(".md", ".html")
            file_path = os.path.join(OUTPUT_HTML_PATH, html_file_name).replace(
                os.sep, "/"
            )

            print(f'Writing HTML to "{file_path}"')
            with open(file_path, "w", encoding="utf-8") as f:
                # Correct the style paths in the HTML content
                html_content = correct_style_path(html_content)
                f.write(html_content)
            print(f"Successfully saved HTML to: {file_path}")

        except Exception as e:
            # This will catch the FileNotFoundError from long path, or any other error
            print(f"Error during rendering for {markdown_file_path}: {e}")
            raise 
        finally:
            if "page" in locals() and page and not page.is_closed():
                page.close()
            # Don't close browser or context if connected to existing one


if __name__ == "__main__":
    successful = 0
    failed = 0

    if not list_txt:
        print(f"No markdown files found in the specified path: {md_files_path_input}")
    else:
        for idx, markdown_file_path in enumerate(list_txt):
            print(
                f"\n--- Converting {idx+1}/{len(list_txt)}: {os.path.basename(markdown_file_path)} ---"
            )
            try:
                render_markdown_to_html(markdown_file_path, md_files_path_base_name) # Pass base name for error message
                successful += 1
                print(f"--- Finished converting {idx+1}/{len(list_txt)}: {os.path.basename(markdown_file_path)} ---")
            except FileNotFoundError as e: # Specifically catch the long path error
                # The detailed message is already printed in render_markdown_to_html
                print(f"Failed to convert {markdown_file_path} due to: {e}")
                failed += 1
            except Exception as e:
                print(f"Failed to convert {markdown_file_path}")
                print(f"General Error: {e}")
                # You might want to print traceback here for other errors:
                # import traceback
                # traceback.print_exc()
                failed += 1

            if idx < len(list_txt) - 1:
                print(
                    f"Waiting {DELAY_BETWEEN_FILES} seconds before processing next file..."
                )
                time.sleep(DELAY_BETWEEN_FILES)

    print(f"\n--- Conversion Summary ---")
    print(f"Total files processed: {len(list_txt)}")
    print(f"Successfully converted: {successful}")
    print(f"Failed: {failed}")
    if failed > 0:
        print("\nFor files that failed due to 'Path too long for Windows':")
        print("Please move your input markdown folder to a location with a shorter path (e.g., C:\\my_docs\\)")
        print("or enable Win32 long path support in your Windows settings (requires admin rights & reboot).")