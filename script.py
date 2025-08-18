import requests
import os
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from tqdm import tqdm
from weasyprint import HTML, default_url_fetcher

BASE_URL = "https://coloradocommunitymedia.com/author/"

AUTHORS = ["mckenna-harford", "mharford"]

OUTPUT_FOLDER = "downloaded_articles"

def extract_and_clean_html(html, url):
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

    # Build a new soup with DOCTYPE + html
    new_soup = BeautifulSoup("<!DOCTYPE html><html></html>", "html.parser")

    # Copy over the <head> from the original
    if soup.head:
        new_soup.html.append(soup.head)

    # Create a new <body> and insert the cleaned <main>
    body = new_soup.new_tag("body")
    body.append(main_tag)
    new_soup.html.append(body)

    return new_soup.prettify()
 

def download_webpage_to_pdf(url, output_filename, faillist: list[str]):
    """Downloads an article, trims to </article>, cleans HTML, and saves as PDF."""
    try:
        response = requests.get(url, headers = {'User-agent': 'authorbot'}, timeout=10)
        response.raise_for_status()

        cleaned_html = extract_and_clean_html(response.text, url)
        HTML(string=cleaned_html, base_url=url, url_fetcher =custom_url_fetcher2).write_pdf(output_filename)
  
        tqdm.write(f"✅ Saved {url} -> {output_filename}")
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

def calculate_total_articles() -> list[str]:
    total = set()
    print(f"Searching for articles... {len(total)} found",  end='\r')
    for author in AUTHORS:
        page_number = 1
        while True:
            if page_number == 1:
                page_url = urljoin(BASE_URL, author)
            else:
                page_url = urljoin(BASE_URL, f"{author}/page/{page_number}")

            links = get_article_links_from_page(page_url)

            if links is None:  # 404 found → stop
                #print("🚪 No more pages. Exiting.")
                break

            total.update(links)

            print(f"Searching for articles... {len(total)} found",  end='\r')
            page_number += 1

    print(f"Total Articles = {len(total)}.")
    return list(total)

            
def crawl_and_download(links: list[str]):
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    article_counter = 0
    link_counter = 0

    fail_list = []
   
    for link in tqdm(links):
        link_counter += 1
        folder = os.path.join(OUTPUT_FOLDER, get_date_folder(link))
        os.makedirs(folder, exist_ok=True)
        short_name = get_filename_from_url(link)
        pdf_filename = os.path.join(folder, f"{short_name}.pdf")
        if os.path.isfile(pdf_filename):  #if it already exists, skip
            tqdm.write(f"Skipping {link}. Already exists.")
            continue
        download_webpage_to_pdf(link, pdf_filename, fail_list)
        article_counter += 1


    print(f"Finished crawling.")
    print(f"Found {link_counter} links")
    print(f"Downloaded {article_counter} articles")
    print(f"Errored on {len(fail_list)} articles.")
    if fail_list:
        print(fail_list)

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


def custom_url_fetcher(url):
    if url.startswith("https://"):
        resp = requests.get(url)
        resp.raise_for_status()
        return {
            "string": resp.content,
            "mime_type": resp.headers.get("Content-Type")
        }
    return default_url_fetcher(url)


def custom_url_fetcher2(url):
    if url.startswith("https://i0.wp.com"):
        url = url.replace("https:", "http:")
    return default_url_fetcher(url)


def print_intro():
    print(f"Executing script")
    print(f"Searching for authors: {AUTHORS}")
    

if __name__ == "__main__":
    print_intro()
    articles = calculate_total_articles()
    if articles:
        crawl_and_download(articles)
    else:
        print("No articles found. Executing script.")
