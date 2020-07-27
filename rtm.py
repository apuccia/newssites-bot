import sys
import getopt
import feedparser
import requests
import time
import pytz
import json

import config

from bs4 import BeautifulSoup
from datetime import datetime, timezone
from telegram.ext import Updater, CommandHandler
from telegraph import Telegraph

TZ_LOCAL = pytz.timezone("Europe/Rome")

TELEGRAPH = "https://telegra.ph/"

USAGE = "Usage: python " + sys.argv[0] + " -s \"news site name\""

E_BAD_INPUT = "Wrong option or no argument inserted"
E_CONNECTION = "Connection error, retrying in " + str(config.CONNECTION_TIMESPAN)
E_PERMANENT_REDIRECT = "Feed permanently redirected, modify config file"
E_FEED_NOT_AVAILABLE = "Feed not available"

def main(news_sites):
    telegraph = Telegraph(config.TELEGRAPH_KEY)
    
    last_article_date = None
    aux = None

    while True:
        for news_site in news_sites:
            feed = feedparser.parse(news_site.get("rss"))
            if feed.status == None:
                print(E_CONNECTION)
                time.sleep(config.CONNECTION_TIMESPAN)
                continue
            elif feed.status == 301:
                print(E_PERMANENT_REDIRECT)
                news_sites.get(news_site)["rss"] = feed.href
                print("Feed URL changed, json file modified with the new URL: " + feed.href)
            elif feed.status == 410:
                print(E_FEED_NOT_AVAILABLE)

            iterator = iter(feed.entries)
            entry = next(iterator, None)
            while entry != None:
                article_date = datetime.strptime(entry.published, '%a, %d %b %Y %H:%M:%S %z')
                print(article_date)
                if last_article_date == None:
                    last_article_date = article_date

                if last_article_date < article_date:
                    try:
                        request = requests.get(entry.link)
                    except requests.exceptions.ConnectionError:
                        print(E_CONNECTION)
                        time.sleep(config.CONNECTION_TIMESPAN)
                        continue

                    print("--A new article is out!")

                    if entry == feed.entries[0]:
                        aux = article_date

                    art_local_date = article_date.astimezone(TZ_LOCAL).strftime(config.TELEGRAPH_ARTICLE_DATE_FORMAT)
                    print("\tArticle local date: " + art_local_date)

                    print("\tArticle link: " + entry.link) 

                    html_content = request.content
                    soup_for_image = BeautifulSoup(html_content, config.PARSER)
                    soup_for_content = BeautifulSoup(entry.content[0].value, config.PARSER)
            
                    article_content = article_generator(news_site, soup_for_image, soup_for_content, art_local_date, entry.link)
                    
                    author = news_site.get("name") + " " + entry.author
                    telegraph_link = telegraph.create_page(entry.title, html_content = article_content, author_name = author, author_url = news_site.get("website"))
                    print("\tTelegra.ph link: " + TELEGRAPH + '{}'.format(telegraph_link['path']))
                else:
                    break

                entry = next(iterator, None)
            
            if aux != None:
                last_article_date = aux

        time.sleep(config.FEED_TIMESPAN)


def article_generator(news_site, img_soup, content_soup, art_date, art_link):
    article_content = "<p>" + art_date + "</p>"

    image = img_soup.find('a', class_ = 'post_thumb')
    article_content += str(image)
                    
    for par in content_soup.find_all('p'):
        child = par.find("span")

        if (child != None):
            child.unwrap()

        article_content += str(par)
                
    article_content += "<p>Fonte: " + news_site.get("name") + " (<a href=\"" + art_link + "\">Leggi l'articolo e i commenti degli utenti sul sito di " + news_site.get("name") + "</a>)</p>"

    return article_content


if __name__ == '__main__':
    try:
        (opts, args) = getopt.getopt(sys.argv[1:], "hs:", ["help", "newssite="])  
    except getopt.GetoptError:
        print(E_BAD_INPUT)
        sys.exit(1) 

    for opt, arg in opts:
        if opt in ('-h', '--help'):
            print(USAGE)
            sys.exit(1)
    
    with open(config.NEWS_SITES, 'r') as jsonfile:
        news_sites = json.load(jsonfile)   

    main(news_sites)        
