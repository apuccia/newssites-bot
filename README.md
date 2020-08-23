# newssites-bot
This program let you track articles published by some websites (actually only the ones that are popular in my hometown) using RSS feeds. For each article, using the original image and paragraphs, it will create a clean and minimal Telegra.ph page. 

Obviously each Telegra.ph page is going to contain the appropriate acknowledgment to the original article and website. Each article is created as is, I'm not responsible about the original content published by the newspaper office.

## What do you need to use this program (at this moment)
The program is written in Python 3+ and uses these external APIs:
* [**requests**](https://requests.readthedocs.io/en/master/) : used to retrieve the original article webpage.
* [**pytz**](http://pytz.sourceforge.net/) : used to deal with timezones of the RSS feeds in order to show exactly the article creation datetime.
* [**feedparser**](https://pythonhosted.org/feedparser/) : used to parse the rss feed of the news website.
* [**beautifulsoup**](https://www.crummy.com/software/BeautifulSoup/bs4/doc/) : used in order to parse HTML of the article web page and obtain the introductory image. In the case of an illformed RSS feed (like the ragusaoggi.it one) it is used to obtain also the paragraphs.
* [**telegraph**](https://python-telegraph.readthedocs.io/en/latest/) : used to create the telegra.ph page. Not all HTML tags can be used (like \<span\> tag).

## Websites supported
Currently only 3 websites are supported:
* [**RTM**](https://www.radiortm.it/)
* [**Ragusa oggi**](https://www.ragusaoggi.it/)
* [**Ragusa news**](https://www.ragusanews.com/)

If you want to have support for other websites just contact me.

## Next updates
The next things that I'm going to add:
* Support to [**Telegram bot API**](https://python-telegram-bot.readthedocs.io/en/stable/), in order to receive the newly created Telegra.ph pages to your account/group/channel.
* Other websites, primarily news websites that are located in my hometown and its surroundings. 