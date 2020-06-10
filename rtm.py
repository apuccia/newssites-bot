import feedparser
import webbrowser
import requests
from bs4 import BeautifulSoup
from datetime import datetime

last_time = 0
while True:
    feed = feedparser.parse("http://www.radiortm.it/feed/")
    last_time = datetime.now()
    print(last_time)
    feed_entries = feed.entries

    for entry in feed.entries:
        article_time = entry.published

        print(last_time.text + "\n")
        print(article_time.text + "\n")
        article_title = entry.title
        article_link = entry.link

        req = requests.get(article_link)
        coverpage = req.content
        soup = BeautifulSoup(coverpage, 'html5lib')
        coverpage_news = soup.find('div', class_='td-post-content')

        print (article_time)
        for par in coverpage_news.find_all('p', recursive = False):
            print(par.text)

        print("\n")
