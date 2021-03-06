import os
import re
import email.utils
import pytz
from flask import Flask
from flask_oauthlib.client import OAuth

app = Flask(__name__)

app.config.from_pyfile('config.py')

oauth = OAuth()
twitter = oauth.remote_app(
    'twitter',
    base_url='https://api.twitter.com/1.1/',
    request_token_url='https://api.twitter.com/oauth/request_token',
    access_token_url='https://api.twitter.com/oauth/access_token',
    authorize_url='https://api.twitter.com/oauth/authorize',
    consumer_key=app.config['TWITTER_CONSUMER_KEY'],
    consumer_secret=app.config['TWITTER_CONSUMER_SECRET']
)


def datetimeformat(value, format='%Y-%m-%d %H:%M'):
    return value.strftime(format)


def pretty_date(time=False, now=None):
    """
    Get a datetime object or a int() Epoch timestamp and return a
    pretty string like 'an hour ago', 'Yesterday', '3 months ago',
    'just now', etc
    """
    from datetime import datetime
    if now is None:
        now = datetime.utcnow()
    if type(time) is int:
        diff = now - datetime.fromtimestamp(time)
    elif isinstance(time, datetime):
        diff = now - time
    elif not time:
        diff = now - now
    else:
        time = datetime.\
            fromtimestamp(
                email.utils.mktime_tz(email.utils.parsedate_tz(time)),
                tz=pytz.utc
            ).replace(tzinfo=None)
        diff = now - time
    second_diff = diff.seconds
    day_diff = diff.days

    if day_diff < 0:
        return 'From The Future'

    if day_diff == 0:
        if second_diff < 10:
            return "just now"
        if second_diff < 60:
            return str(second_diff) + " seconds ago"
        if second_diff < 120:
            return "a minute ago"
        if second_diff < 3600:
            return str(second_diff / 60) + " minutes ago"
        if second_diff < 7200:
            return "an hour ago"
        if second_diff < 86400:
            return str(second_diff / 3600) + " hours ago"
    if day_diff == 1:
        return "Yesterday"
    if day_diff < 7:
        return str(day_diff) + " days ago"
    if day_diff < 31:
        return str(day_diff / 7) + " weeks ago"
    if day_diff < 365:
        return str(day_diff / 30) + " months ago"
    return str(day_diff / 365) + " years ago"


def linkify(tweet):
    if 'text' in tweet:
        text = tweet['text']
        urls = tweet['entities']['urls']
    elif 'description' in tweet:
        text = tweet['description']
        urls = tweet['entities']['description']['urls']
    else:
        return ''
    offset = 0
    for url in urls:
        text = (text[:url['indices'][0] + offset]
                + '<a href="' + url['expanded_url'] + '">'
                + url['display_url'] + '</a>'
                + text[url['indices'][1] + offset:])
        offset += (15 + len(url['expanded_url']) + len(url['display_url'])
                   - len(url['url']))
    name_replacement = re.compile(r'@(\w+)')
    text = name_replacement.sub('<a href="\g<1>">@\g<1></a>', text)
    return text


def is_mention(screen_name, tweet):
    return re.search('@%s' % screen_name, tweet['text']) is not None

app.jinja_env.filters['datetime'] = datetimeformat
app.jinja_env.filters['pretty_date'] = pretty_date
app.jinja_env.filters['linkify'] = linkify
app.jinja_env.globals.update(is_mention=is_mention)

from views import *

if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
