import feedparser
import requests
import time
import pytz

from bs4 import BeautifulSoup
from datetime import datetime, timezone
from telegram.ext import Updater, CommandHandler
from telegraph import Telegraph

LOCAL_TZ = pytz.timezone("Europe/Rome")
UTC_TZ = pytz.timezone("Etc/UTC")

def main():
    telegraph = Telegraph("your telegra.ph key")
    
    print(telegraph.get_account_info())
    last_article_date = UTC_TZ.localize(datetime.now())

    while True:
        feed = feedparser.parse("http://www.radiortm.it/feed/")

        for entry in feed.entries:
            article_date = datetime.strptime(entry.published, '%a, %d %b %Y %H:%M:%S %z')
            
            if last_article_date < article_date:
                last_article_date = article_date

                local_date = article_date.astimezone(LOCAL_TZ).strftime('%H:%M')
                
                print(entry.link)

                request = requests.get(entry.link)
                html_content = request.content
                
                soup = BeautifulSoup(html_content, 'html5lib')
                news = soup.find('div', class_='elementor-element elementor-element-6553dd6d contenuto_post elementor-widget elementor-widget-theme-post-content')

                if news != None:
                    content = "<p>" + local_date + "</p>"

                    for par in news.find_all(find_filter):
                        child = par.find("span")

                        if (child != None):
                            child.unwrap()

                        content += str(par)

                    content += "<p>Fonte: RTM (<a href=\"" + entry.link + "\">Leggi l'articolo e i commenti degli utenti sul sito di RTM</a>)</p>"

                    author = "RTM-" + entry.author
                    link = telegraph.create_page(entry.title, html_content = content, author_name = author)
                    print('https://telegra.ph/{}'.format(link['path']))
                else:
                    print("Class attribute changed!")
            else:
                break

        time.sleep(120)

def find_filter(tag):
    return tag.name == "p" or (tag.name == "a" and tag.has_attr("href") and tag.has_attr("class"))

if __name__ == '__main__':
    main()        
