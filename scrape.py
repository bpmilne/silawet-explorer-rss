import requests
import redis
import config
import re
import json
from HTMLParser import HTMLParser
html = HTMLParser()

from bs4 import BeautifulSoup

r = redis.from_url(config.REDIS_URL)


def get_urls():
    authors = r.smembers('authors')
    return ['http://explorer.silawet.com/author/%s' % a for a in authors]

def update(url):
    # print 'updating %s' % url
    m = re.search(r'/author/(.*)', url)
    author = m.group(1)
    resp = requests.get(url)
    lines = resp.text.split('\n')
    msg_id, timestamp, content, url = '', '', '', ''
    for line in lines:
        m_id = re.search(r'ID:<a href="/message/(.*?)"', line)
        m_ts = re.search(r'Authored At:(\d+)', line)
        m_content = re.search(r'<p><span>(.*)</span></p>', line)
        if m_id:
            msg_id = m_id.group(1)
        elif m_ts:
            timestamp = m_ts.group(1)
        elif msg_id and timestamp and m_content:
            content = html.unescape(m_content.group(1)) \
                          .replace('\n', ' ') \
                          .replace('\\', '')
            url = 'http://explorer.silawet.com/message/%s' % msg_id
            item = {
                'id': msg_id,
                'url': url,
                'timestamp': timestamp,
                'content': content,
            }
            # score = timestamp
            r.hset('author:%s' % author, msg_id, json.dumps(item))
            # print 'FOUND', msg_id, url, timestamp, content[0:10]
            msg_id, timestamp, content, url = '', '', '', ''

def scrape():
    pass
    urls = get_urls()
    for url in urls:
        update(url)
    # check each for updates
    # store updates

if __name__ == '__main__':
    scrape()
