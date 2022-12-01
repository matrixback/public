import re
from collections import defaultdict
from copy import deepcopy

from urllib.parse import urlparse
from bs4 import BeautifulSoup
from bs4.element import NavigableString

# 控制一个url只请求一次
visited_urls = set()
# 包含单词最多的页面
longest_page = ''
longest = 0
# words_cnt for statistic common 50 words
# 统计出现次数最多的50个单词
words_cnt = defaultdict(int)


def scraper(url, resp):
    """
    此函数从当前爬取的页面 resp 中提取有效的 url，供爬虫再次爬取
    url: 当前爬取页面的 url
    resp: 当前爬取页面的 response，一个 html 文件
    return: 有效的 url list
    """
    # 在函数中使用函数外定义的变量
    global longest, longest_page
    # 先将已爬到数据的 URL 保存到文件中，后面统计数据时使用
    with open('url.txt', 'a+') as f:
        f.write(f'{url}\n')

    try:
        # 如果返回的数据内容为空，则直接返回空list
        if (not resp
            or not resp.raw_response
            or not resp.raw_response.content):
            return []
        
        # 获取当前页面包含的单词长度
        length = get_html_text_words_cnt(resp.raw_response.content)
    except Exception as e:
        print(e)
        return []
   
    # 将 url 以及页面单词的长度 length 保存起来，后面统计用
    with open('words.txt', 'a+') as f:
        print(f'{url},{length}')
        f.write(f'{url},{length}\n')
        # 更新当前的最大长度页面
        if length > longest:
            longest = length
            longest_page = url
            print(f'longest url {longest_page}, words: {longest}')

    save_top_50_words()
    
    # 从当前页面提取所有的 url
    links = extract_next_links(url, resp)
    # 对于提取的url，将有效的 url 添加到 invalid_links 返回
    invalid_links = list()
    for link in links:
        if not is_valid(link):
            print(f'invalid {link}')
        else:
            print(f'add {link}')
            invalid_links.append(link)
    return invalid_links


def extract_next_links(url, resp):
    """
    此函数解析 resp html 页面，获取所有未爬取的 url
    返回 url list
    """
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content
    
    
    # 如果 resp 的状态码不为200，则页面无效，直接返回空list
    if resp.status != 200:
        return list()

    # 通过 beautifulsoup 解析当前的 html 页面
    soup = BeautifulSoup(resp.raw_response.content, 'html.parser')
    links = list()
    # parse 当前url的信息
    parent_url_parsed = urlparse(url)
    # 从html 页面提取所有的 a tag
    for link in soup.find_all('a'):
        # 获取 a tag 的href 属性，即 url
        url = link.get('href')
        # 解析当前的 url，如果缺少必要信息，则从父 url 中获取
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
        # 如果未爬取，则添加到 links 中，返回
        if url not in visited_urls:
            visited_urls.add(url)
            links.append(url)

    return links


def is_valid(url):
    """
    此函数判断一个 url 是否有效，返回 bool 类型
    """
    # Decide whether to crawl this url or not.
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        # 解析 url ，获取 url 信息
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
        
        # 如果 url.path 以下面这些结尾，则为无效 url
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
        
        # 判断特殊的url
        path = parsed.hostname + parsed.path.lower()
        if path.startswith('today.uci.edu/department/information_computer_sciences/'):
            return True
        
        # 如果 path 符合的正则表达式，为为有效的 url
        # .*\.(ics.uci.edu/|cs.uci.edu/|informatics.uci.edu/|stat.uci.edu/).*
        # .* 表示0个或多个字符
        # | 表示或
        # xxx.(ics.uci.edu/ 或者 cs.uci.edu 等).xxx 就是合格的
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
