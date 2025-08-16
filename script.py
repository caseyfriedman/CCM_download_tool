import requests
import pdfkit
import os
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE_URL = "https://coloradocommunitymedia.com/author/"

AUTHORS = ["mckenna-harford", "mharford"]

OUTPUT_FOLDER = "downloaded_articles"

# Optional: configure path for wkhtmltopdf if not in PATH
# pdfkit_config = pdfkit.configuration(wkhtmltopdf=r"C:/Program Files/wkhtmltopdf/bin/wkhtmltopdf.exe")
path_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)

options = {'encoding': 'UTF-8'}

def extract_and_clean_html(html):
    """Extracts <main> content, removes <aside> tags and everything after jp-relatedposts."""
    soup = BeautifulSoup(html, "html.parser")

    # Get the <main> tag
    main_tag = soup.find("main")
    if not main_tag:
        return ""  # If no <main> found, return empty string

    # Remove all <aside> tags
    for aside in main_tag.find_all("aside"):
        aside.decompose()

    comments = main_tag.find("div", id="comments")
    if comments:
        comments.decompose()


    # Find the "jp-relatedposts" div and remove it + everything after
    related_div = main_tag.find("div", id="jp-relatedposts")
    if related_div:
        # Remove the related posts div itself
        related_div.decompose()

        # Remove all siblings after this point
        for sibling in list(main_tag.contents):
            if sibling == related_div:
                break
 

    # Return prettified HTML (BeautifulSoup closes tags automatically)
    return BeautifulSoup(str(main_tag), "html.parser").prettify()

def download_webpage_to_pdf(url, output_filename, faillist: list[str]):
    """Downloads an article, trims to </article>, cleans HTML, and saves as PDF."""
    try:
        response = requests.get(url, headers = {'User-agent': 'authorbot'}, timeout=10)
        response.raise_for_status()

        cleaned_html = extract_and_clean_html(response.text)

        temp_html = output_filename.replace(".pdf", ".html")
        with open(temp_html, "w", encoding="utf-8") as file:
            file.write(cleaned_html)

        pdfkit.from_file(temp_html, output_filename, configuration=config, options={'encoding': 'UTF-8' })

        os.remove(temp_html)
        print(f"✅ Saved {url} -> {output_filename}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to download {url}: {e}")
        faillist.append(url)

def get_article_links_from_page(page_url):
    """Fetches article links from a paginated author page."""
    response = requests.get(page_url, headers = {'User-agent': 'authorbot'}, timeout=10)
    if response.status_code == 404:
        return None  # Signal no more pages
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    main_tag = soup.find("main", id="main")
    if not main_tag:
        return []

    links = []
    
    for article in main_tag.find_all("article"):
        link_tag = article.find("figure", class_="post-thumbnail")
        if link_tag and link_tag.a and link_tag.a.get("href"):
            links.append(link_tag.a["href"])

    return links

def crawl_and_download():
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    article_counter = 1
    link_counter = 0

    fail_list = []
    for author in AUTHORS:
        page_number = 1
        while True:
            if page_number == 1:
                page_url = urljoin(BASE_URL, author)
            else:
                page_url = urljoin(BASE_URL, f"{author}/page/{page_number}")

            print(f"\n📄 Fetching {page_url} ...")
            links = get_article_links_from_page(page_url)

            if links is None:  # 404 found → stop
                print("🚪 No more pages. Exiting.")
                break

            for link in links:
                link_counter += 1
                print(f"The link is: {link}")
                folder = os.path.join(OUTPUT_FOLDER, get_date_folder(link))
                os.makedirs(folder, exist_ok=True)
                short_name = get_filename_from_url(link)
                pdf_filename = os.path.join(folder, f"{short_name}.pdf")
                if os.path.isfile(pdf_filename):  #if it already exists, skip
                    continue
                download_webpage_to_pdf(link, pdf_filename, fail_list)
                article_counter += 1
            page_number += 1

    print(f"Finished crawling.")
    print(f"Found {link_counter} links")
    print(f"Downloaded {article_counter} articles")
    print(f"Errored on {len(fail_list)} articles: {fail_list}")

def get_date_folder(url: str):
    match = re.search(r"/(\d{4})/(\d{2})/(\d{2})/", url)
    if match:
        year, month, day = match.groups()
        return os.path.join(year, month, day)
    print(f"Date unknown for link {url}")
    return "unknown_date"

def get_filename_from_url(url: str) -> str:
    short_title = url.split("/")[-2]
    return short_title.replace("-", "_")


if __name__ == "__main__":
    crawl_and_download()
