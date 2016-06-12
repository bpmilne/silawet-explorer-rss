import redis
import config
import os
import re
import json

from flask import (
    Flask,
    make_response,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_wtf import Form
from wtforms.fields.html5 import URLField
from wtforms import validators
from feedgen.feed import FeedGenerator

r = redis.from_url(config.REDIS_URL)

app = Flask(__name__)
app.secret_key = 'keyboard cat'

author_re = r'https?:\/\/explorer.silawet.com\/author\/(.*)'

class UrlForm(Form):
    url = URLField(validators=[
        validators.url(),
        validators.Regexp(
            author_re,
            message='Must be like: http://explorer.silawet.com/author/...')
    ])

def valid_xml_char_ordinal(c):
    codepoint = ord(c)
    # conditions ordered by presumed frequency
    return (
        0x20 <= codepoint <= 0xD7FF or
        codepoint in (0x9, 0xA, 0xD) or
        0xE000 <= codepoint <= 0xFFFD or
        0x10000 <= codepoint <= 0x10FFFF)

def clean(str):
    cleaned = ''.join(c for c in str if valid_xml_char_ordinal(c))
    return cleaned

@app.route('/feed/<author>.rss', methods=['GET'])
def feed(author):
    m = re.search(r'(https?:\/\/.*?)\/feed/', request.url)
    origin = m.group(1)

    fg = FeedGenerator()
    fg.id('%s/author/%s' % (origin, author))
    fg.title('Silawet Feed')
    fg.description('Silawet Feed')
    fg.author({'name': author})
    fg.link(href=request.url)

    key = 'author:%s' % author
    items = r.hgetall(key).values()
    items = [json.loads(s) for s in items]
    items.sort(key=lambda(i): i['timestamp'])
    for item in items:
        print item['url']
        fe = fg.add_entry()
        fe.id(item['id'])
        fe.content(clean(item['content']))
        fe.link(href=item['url'])

    rssfeed = fg.rss_str(pretty=True)
    return rssfeed

@app.route('/', methods=['GET', 'POST'])
def index():
    form = UrlForm()
    if form.validate_on_submit():
        m = re.match(author_re, form.url.data)
        author = m.group(1)
        r.sadd('authors', author)
        return redirect('/')
    authors = r.smembers('authors')
    return render_template('index.html', form=form, authors=authors)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
