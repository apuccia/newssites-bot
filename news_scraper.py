import sys
import time
import json
from datetime import datetime
import pytz
import feedparser
import requests
from bs4 import BeautifulSoup
from telegraph import Telegraph

import config

TZ_LOCAL = pytz.timezone("Europe/Rome")

TELEGRAPH = "https://telegra.ph/"

E_BAD_INPUT = "Wrong option or no argument inserted"
E_CONNECTION = "Connection error, retrying in " + str(config.CONNECTION_TIMESPAN)
E_HTTP = "HTTP error, bad status code"
E_PERMANENT_REDIRECT = "Feed permanently redirected, modify config file"
E_FEED_NOT_AVAILABLE = "Feed not available"
E_MISS_LINK = "Missing article link"

D_NOT_CHANGED = "Feed not changed"
D_CHANGED = "Feed changed"

allowed_tags = ["p", "iframe", "a", "aside", "b", "blockquote", \
                "br", "code", "em", "figcaption", "figure", "h3", "h4", \
                "hr", "i", "img", "li", "ol", "pre", "s", "strong", \
                "u", "ul", "video"]
bad_tags_unw = ["center", "div", "span"]
bad_tags_ext = ["button", "style"]

last_article_dates = dict()
last_feed_etags = dict()
last_feed_mods = dict()

def main(news_sites):
    # access telegra.ph account
    telegraph = Telegraph(config.TELEGRAPH_KEY)
    
    for news_site in news_sites:
        last_article_dates[news_site["name"]] = None
        last_feed_etags[news_site["name"]] = None
        last_feed_mods[news_site["name"]] = None

    while True:
        for news_site in news_sites:
            # get RSS feeds
            feed = get_feed(news_site, news_sites)

            if feed == None or not feed:
                continue

            feed.entries.reverse()
            iterator = iter(feed.entries)
            entry = next(iterator, None)

            while entry != None:
                # format date
                article_date = datetime.strptime(entry.published, '%a, %d %b %Y %H:%M:%S %z')
                site_name = news_site["name"]

                if last_article_dates[site_name] == None:
                    last_article_dates[site_name] = datetime.strptime(feed.entries[-1].published, '%a, %d %b %Y %H:%M:%S %z')
                    break
                elif last_article_dates[site_name] < article_date:
                    request = get_page(entry.link)

                    # request exceptions
                    if request == None:
                        continue

                    print("-- A new article from " + site_name + " is out!")

                    # format from UTC date to local date
                    art_local_date = article_date.astimezone(TZ_LOCAL).strftime(config.TELEGRAPH_ARTICLE_DATE_FORMAT)
                    print("\tArticle UTC date: " + str(article_date))

                    if not entry.link:
                        print(E_MISS_LINK)
                        continue
                    else:
                        print("\tArticle link: " + entry.link) 

                    if not entry.content[0].value:
                        break

                    html_content = request.content
                    # retrieve intro image from html webpage
                    soup_for_image = BeautifulSoup(html_content, config.PARSER)
                    
                    # rss feed is well-formed, it contains html tags
                    if news_site.get("content_tag") == None:
                        soup_for_content = BeautifulSoup(entry.content[0].value, config.PARSER)
                    # rss feed is ill-formed, i need to get article paragraphs from html webpage 
                    else:
                        soup_for_content = soup_for_image

                    # create full article page
                    article_content = article_generator(news_site, soup_for_image, soup_for_content, art_local_date, entry.link)
                    
                    # define original article creator
                    author = site_name + " " + entry.author
                    
                    # create telegra.ph page
                    telegraph_link = telegraph.create_page(entry.title, html_content = article_content,
                                                                        author_name = author, 
                                                                        author_url = news_site.get("website"))
                    print("\tTelegra.ph link: " + TELEGRAPH + '{}'.format(telegraph_link['path']))

                    last_article_dates[site_name] = article_date

                entry = next(iterator, None)

        time.sleep(config.FEED_TIMESPAN)


def article_generator(news_site, img_soup, content_soup, art_date, art_link):
    article_content = "<p>" + art_date + "</p>"

    # get intro image from html webpage
    image = img_soup.find(news_site["image_tag"], {news_site["image_attribute"] : news_site["image_attrvalue"]})
    if image != None:
        article_content += str(image)

    # get paragraphs directly from rss feed
    if news_site["content_tag"] == None:
        article_content += get_paragraphs(content_soup)
    # need to get paragraphs from html webpage
    else:
        cont = content_soup.find(news_site.get("content_tag"), {news_site["content_attribute"] : news_site["content_attrvalue"]})        

        article_content += get_paragraphs(cont)

    article_content += "<p>Fonte: " + \
                            news_site["name"] + \
                            " (<a href=\"" + art_link + \
                            "\">Leggi l'articolo e i commenti degli utenti sul sito di " +  \
                            news_site["name"] + \
                            "</a>)</p>"
    #print("\n\n\nFINAL ARTICLE:")
    #print(article_content)
    return article_content

def get_feed(site, news_sites):
    name = site["name"]

    if last_feed_etags[name] == None and last_feed_mods[name] == None:
        feed = feedparser.parse(site["rss"])
    elif last_feed_etags[name] != None and last_feed_mods[name] == None:
        feed = feedparser.parse(site["rss"], etag = last_feed_etags[name])
    elif last_feed_etags[name] == None and last_feed_mods[name] != None:
        feed = feedparser.parse(site["rss"], modified = last_feed_mods[name])
    else:
        feed = feedparser.parse(site["rss"], modified = last_feed_mods[name], etag = last_feed_etags[name])

    if feed.status == 301:
        print(E_PERMANENT_REDIRECT)
        news_sites[site]["rss"] = feed.href

        with open(config.NEWS_SITES, 'w') as file:
            json.dump(news_sites, file)

        print("Feed URL changed, json file modified with the new URL: " + feed.href)
    elif feed.status == 304: #feed didn't change
        feed = None
    elif feed.status == 410:
        print(E_FEED_NOT_AVAILABLE)
        feed = None
    elif feed.status == 200:
        last_feed_etags[name] = feed.etag
        last_feed_mods[name] = feed.modified    

    return feed

def get_page(link):
    try:
        request = requests.get(link, timeout = config.REQUEST_TIMEOUT)
    except requests.exceptions.ConnectionError:
        print(E_CONNECTION)
        time.sleep(config.CONNECTION_TIMESPAN)
        request = None
    except requests.exceptions.HTTPError:
        request.raise_for_status()
        request = None

    return request

def get_paragraphs(content):
    #print("ORIGINAL ARTICLE")
    #print(content)
    for tag in content.find_all(list(set().union(allowed_tags, bad_tags_ext, bad_tags_unw))):
        if tag.name in bad_tags_ext:
            tag.extract()
        elif tag.name in bad_tags_unw:
            tag.unwrap()
        elif tag.name in allowed_tags:
            if tag.name == "iframe":
                # article yt video for ragusa news, need to check other websites
                parent = tag.parent

                # build supported yt embedded link for telegra.ph
                src = "/embed/youtube?url=" + tag["src"].replace("embed/", "watch?v=")
                src.replace("embed/", "watch?v=")

                # remove old iframe tag
                tag.extract()
                
                # put new iframe tag inside a figure tag
                fig_tag = content.new_tag("figure")
                fig_tag.append(content.new_tag("iframe", attrs={"src": src}))

                parent.append(fig_tag)
                
    paragraphs = ""
    for child in content.children:
        paragraphs += str(child)
   
    return paragraphs


if __name__ == '__main__':
    with open(config.NEWS_SITES, 'r') as jsonfile:
        news_sites = json.load(jsonfile)   

    main(news_sites)        
