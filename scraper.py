import re
from collections import defaultdict
from copy import deepcopy

from urllib.parse import urlparse
from bs4 import BeautifulSoup
from bs4.element import NavigableString

visited_urls = set()
longest_page = ''
longest = 0
# words_cnt for statistic common 50 words
words_cnt = defaultdict(int)


def scraper(url, resp):
    global longest, longest_page
    with open('url.txt', 'a+') as f:
        f.write(f'{url}\n')

    try:
        if (not resp
            or not resp.raw_response
            or not resp.raw_response.content):
            return []
        length = get_html_text_words_cnt(resp.raw_response.content)
    except Exception as e:
        print(e)
        return []

    with open('words.txt', 'a+') as f:
        print(f'{url},{length}')
        f.write(f'{url},{length}\n')
        if length > longest:
            longest = length
            longest_page = url
            print(f'longest url {longest_page}, words: {longest}')

    save_top_50_words()

    links = extract_next_links(url, resp)
    invalid_links = list()
    for link in links:
        if not is_valid(link):
            print(f'invalid {link}')
        else:
            print(f'add {link}')
            invalid_links.append(link)
    return invalid_links


def extract_next_links(url, resp):
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content
    if resp.status != 200:
        return list()

    soup = BeautifulSoup(resp.raw_response.content, 'html.parser')
    links = list()
    parent_url_parsed = urlparse(url)
    for link in soup.find_all('a'):
        url = link.get('href')
        parsed = urlparse(url)
        if parsed.scheme:
            scheme = parsed.scheme
        else:
            scheme = parent_url_parsed.scheme

        if parsed.hostname:
            hostname = parsed.hostname
        else:
            hostname = parent_url_parsed.hostname
        try:
            url = scheme + "://" + hostname + parsed.path
        except Exception as e:
            continue

        if url not in visited_urls:
            visited_urls.add(url)
            links.append(url)

    return links


def is_valid(url):
    # Decide whether to crawl this url or not.
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False

        if re.match(
                r".*\.(css|js|bmp|gif|jpe?g|ico"
                + r"|png|tiff?|mid|mp2|mp3|mp4"
                + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
                + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
                + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
                + r"|epub|dll|cnf|tgz|sha1"
                + r"|thmx|mso|arff|rtf|jar|csv"
                + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower()):
            return False

        path = parsed.hostname + parsed.path.lower()
        if path.startswith('today.uci.edu/department/information_computer_sciences/'):
            return True

        if re.match(
                r".*\.(ics.uci.edu/"
                + r"|cs.uci.edu/"
                + r"|informatics.uci.edu/"
                + r"|stat.uci.edu/).*", path):
            return True

        return False


    except TypeError:
        print("TypeError for ", parsed)
        raise


def get_html_text_words_cnt(content):
    soup = BeautifulSoup(content, 'html.parser')
    # cur html words cnt
    words = 0
    stop_words = get_stop_words()

    def get_text(root):
        nonlocal words
        nonlocal stop_words

        if not root:
            return 0

        if isinstance(root, NavigableString):
            return 0

        if not hasattr(root, 'contents'):
            return 0

        for children in root.contents:
            if isinstance(children, NavigableString):
                continue

            if children.string is not None:
                cur_words = children.string.split()
                for word in cur_words:
                    if word and word not in stop_words:
                        words_cnt[word] += 1

                words += len(cur_words)

            get_text(children)

    get_text(soup.find('html'))
    return words


def get_stop_words():
    stop_words = set()
    with open('stopwords.txt') as f:
        for line in f:
            line = line.strip()
            if line:
                stop_words.add(line)
    return stop_words


def save_top_50_words():
    w_cnt = deepcopy(words_cnt)
    w_cnt_pair = list(w_cnt.items())
    w_cnt_pair.sort(key=lambda x: x[1], reverse=True)
    with open('top_50_words.txt', 'w') as f:
        for word, _ in w_cnt_pair[:50]:
            f.write(f'{word}\n')
