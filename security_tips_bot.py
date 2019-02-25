from collections import namedtuple
from datetime import datetime, timedelta
import logging
import os
import sys
from time import mktime

import feedparser
from slackclient import SlackClient

# Security Tip of the Day RSS Feed
FEED_URL = 'https://feeds2.feedburner.com/security-awareness-tip-of-the-day/'

# Slack Bot config
SLACK_EMOJI = ':robot_face:'
SLACK_BOT_NAME = 'SecurityBot'
SLACK_FOOTER_ICON = 'https://platform.slack-edge.com/img/default_application_icon.png'

# Configuring logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')

# Configuring named tuples
Tip = namedtuple('Tip', ['link', 'title', 'summary', 'published_parsed'])

def get_slack_token():
    """Getting Slack Bot Token from env variable"""
    return os.environ['SLACK_BOT_TOKEN'].strip()


def get_slack_channel():
    """Getting Slack Channel Name from env variable"""
    return os.environ['SLACK_CHANNEL'].strip()


def parse(FEED_URL):
    """ Parsing Security Tips"""
    parsed = feedparser.parse(FEED_URL)
    status = parsed.status
    if status == 200:
        return parsed
    else:
        logging.fatal('HTTP Error (Code): %s Feed not found error (%s). Exiting...' % (status, FEED_URL))
        sys.exit(1)


def get_articles(parsed):
    """ Getting the most recent tip"""
    feed_date = datetime.today() - timedelta(days=1)
    entries = parsed['entries']
    tips = (
        Tip(link=entry['link'],
            title=entry['title'],
            summary=entry['summary'],
            published_parsed=datetime.fromtimestamp(mktime(entry['published_parsed'])))
        for entry in entries)
    return [tip for tip in tips if tip.published_parsed > feed_date]


def send_slack_tip(tips):
    """ Posting to a Slack channel """
    sc = SlackClient(get_slack_token())
    if len(tips) == 0:
        logging.error('No items in the feed. Parsed content: %s' % tips)
        return
    tip = tips[0]
    title = tip.title
    link = tip.link
    published = tip.published_parsed.timestamp()
    summary = tip.summary
    attachments = []
    markdownIn = ['text','pretext','fields','attachments']
    fields = []
    fields.append({
        'title': '',
        'value': summary,
        'short': False
    })
    attachments.append({
        'mrkdwn_in': markdownIn,
        'fallback': title,
        'color': '#2eb886',
        'title': title,
        'title_link': link,
        'pretext': "*Security tip of the day* ",
        'fields': fields,
        'footer': 'Security tips',
        'footer_icon': SLACK_FOOTER_ICON,
        'ts': published
    })
    if not sc.rtm_connect(with_team_state=False):
        logging.fatal('Connection to Slack failed!')
        sys.exit(1)
    sc.api_call(
        "chat.postMessage",
        icon_emoji=SLACK_EMOJI,
        username=SLACK_BOT_NAME,
        channel=get_slack_channel(),
        mrkdwn=True,
        attachments=attachments
    )
    logging.info('Security tip of the day has been posted to Slack')


def main():
    logging.info('Getting the tip of the day')
    parsed = parse(FEED_URL)
    tips = get_articles(parsed)
    send_slack_tip(tips)


if __name__ == '__main__':
    main()
