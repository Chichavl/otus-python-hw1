import requests
import logging
import argparse
import pprint
import re
from bs4 import BeautifulSoup

logging.basicConfig(format='%(asctime)s %(levelname)s : %(message)s [in %(funcName)s %(pathname)s:%(lineno)d]', level=logging.INFO)
logger = logging.getLogger(__name__)
pp = pprint.PrettyPrinter(indent=2)

def get_external_links(url):
  response = requests.get(url)
  if response.status_code == 200:
    logger.debug(f"""Recieved {url} content""")
    html = response.text
    logger.debug(f"""Response content first 50 chars""")
    logger.debug(html[:50])
  else:
    logger.error(f"""Failed to recieve {url}. HTTP code {response.status_code}. Response {response.text}""")
    raise RuntimeError(f"""Failed to recieve {url}. HTTP code {response.status_code}. Response {response.text}""")
  
  soup = BeautifulSoup(html, 'html.parser')
  links = soup.find_all('a')
  # https://regex101.com/library/jN6kU2
  site_name_regexp = re.compile(r'^(?:https?:\/\/)?(?:[^@\/\n]+@)?(?:www\.)?([^:\/\n]+)')
  site_name_match = site_name_regexp.search(url)
  logger.debug(f"""Match our site name as {site_name_match[1]}""")
  external_links = []
  for link in links:
    logger.debug(f"""Got link object {link}""")
    # Default for no href or data-href, we should exit from iteration
    link_url = link.get('href', '/')
    logger.debug(f"""Found link with "{link_url}" """)
    if link_url.startswith("/") or \
      link_url.startswith("#") or \
      link_url.startswith("..") or \
      link_url.startswith("mailto:") or \
      len(link_url) == 0:
      continue
    url_site_name_match = site_name_regexp.search(link_url)
    logger.debug(f"""Match link site name as {url_site_name_match[1]}""")
    if site_name_match[1] != url_site_name_match[1]:
      external_links.append(link_url)
  return list(dict.fromkeys(external_links)) # remove duplicates


def get_parser():
  parser = argparse.ArgumentParser("Parser")
  parser.add_argument(
      "--url", "-u", action="store", default="https://www.farpost.ru/", help="Provide site url (default: https://www.farpost.ru/)"
  )
  parser.add_argument(
      "--verbose", "-v", action="store_true", help="Turn on debug mode"
  )
  parser.add_argument(
      "--depth", "-d", action="store", type=int, default=1, help="How deep should we go (default: 1)"
  )
  return parser

def check_protocol(url):
    """Check URL for a protocol."""
    return url and (url.startswith("http://") or url.startswith("https://"))

def add_protocol(url):
    """Add protocol to URL."""
    if not check_protocol(url):
        return f"""http://{url}"""
    return url

def iter(url, depth):
  if depth == 0:
    return
  for link in get_external_links(url):
    print(link)
    iter(link, depth - 1)

if __name__ == "__main__":
  parser = get_parser()
  args = parser.parse_args()
  if args.verbose:
    logger.setLevel(logging.DEBUG)
  # Add protocol, to prevent:
  # requests.exceptions.MissingSchema: Invalid URL 'ya.ru': No scheme supplied. Perhaps you meant http://ya.ru?
  iter(add_protocol(args.url), args.depth)