import sys
import getopt
import feedparser
import requests
import time
import pytz

import config

from bs4 import BeautifulSoup
from datetime import datetime, timezone
from telegram.ext import Updater, CommandHandler
from telegraph import Telegraph

TZ_LOCAL = pytz.timezone("Europe/Rome")
TZ_UTC = pytz.timezone("Etc/UTC")

TELEGRAPH = "https://telegra.ph/"
NEWSSITES_SUPPORTED = ["RTM"]

E_BAD_INPUT = "Usage: python " + sys.argv[0] + " -s \"news site name\""
E_NOT_SUPPORTED = "News site not supported"

def main(news_site):
    telegraph = Telegraph(config.TELEGRAPH_KEY)
    
    last_article_date = TZ_UTC.localize(datetime.now())
    aux = None

    while True:
        feed = feedparser.parse(news_site[2])

        for entry in feed.entries:
            article_date = datetime.strptime(entry.published, '%a, %d %b %Y %H:%M:%S %z')
            
            if last_article_date < article_date:
                if entry == feed.entries[0]:
                    aux = article_date

                art_local_date = article_date.astimezone(TZ_LOCAL).strftime(config.TELEGRAPH_ARTICLE_DATE_FORMAT)

                print(entry.link) 
                request = requests.get(entry.link)
                
                html_content = request.content
                soup_for_image = BeautifulSoup(html_content, config.PARSER)
                soup_for_content = BeautifulSoup(entry.content[0].value, config.PARSER)
        
                article_content = article_generator(news_site, soup_for_image, soup_for_content, art_local_date, entry.link)
                
                author = news_site[0] + " " + entry.author
                telegraph_link = telegraph.create_page(entry.title, html_content = article_content, author_name = author, author_url = news_site[1])
                print(TELEGRAPH + '{}'.format(telegraph_link['path']))
            else:
                break
        
        if aux != None:
            last_article_date = aux

        time.sleep(config.TIMESPAN)

def article_generator(news_site, img_soup, content_soup, art_date, art_link):
    article_content = "<p>" + art_date + "</p>"

    image = img_soup.find('a', class_ = 'post_thumb')
    article_content += str(image)
                    
    for par in content_soup.find_all('p'):
        child = par.find("span")

        if (child != None):
            child.unwrap()

        article_content += str(par)
                
        article_content += "<p>Fonte: " + news_site[0] + " (<a href=\"" + art_link + "\">Leggi l'articolo e i commenti degli utenti sul sito di " + news_site[0] + "</a>)</p>"

    return article_content

def get_news_site(x):
    return {
        "RTM" : ["RTM", "https://www.radiortm.it/", "http://www.radiortm.it/feed/"]
    }

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print(E_BAD_INPUT)
        sys.exit(1)

    try:
        (opt, arg) = getopt.getopt(sys.argv[1:], "s:", "-newssite=")  
    except getopt.GetoptError:
        print(E_BAD_INPUT)
        sys.exit(1) 

    if arg not in NEWSSITES_SUPPORTED:
        print(E_NOT_SUPPORTED)
        sys.exit(1)

    news_site = get_news_site(arg)

    main(news_site)        
