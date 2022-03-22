import os
import time

import requests

from apscheduler.schedulers.background import BackgroundScheduler
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By


def setDriver():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
    return webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), chrome_options=chrome_options)
    # return webdriver.Chrome(executable_path="utils/chromedriver99.exe",
    #                         options=chrome_options)


def getNewestMovie():
    r = requests.get('http://moviephrestfullapi.herokuapp.com/newest_movie/', headers={'accept': 'application/json'})
    print("checking newest movie")
    if r.status_code == 204:
        return 'empty'
    else:
        return r.json()['url']


def startSpider():
    driver = setDriver()
    driver.get('http://95.168.173.89/')  # Accessing Web
    WebDriverWait(driver, 4)
    # driver.find_element(By.CLASS_NAME, "sgpb-popup-close-button-6").click()

    html = driver.page_source  # Get HTML
    soup = BeautifulSoup(html, 'html.parser')
    cat_box = soup.find("div", {"class": "row grid-container gmr-module-posts"})

    movie_container = []
    for movie in reversed(cat_box.find_all('div', {'class': 'gmr-item-modulepost'})):
        movie_container.append(movie)

    if movie_container[-1].a['href'] == getNewestMovie():
        print("list already up to date")
    else:
        for movie in movie_container:
            original_title = movie.a['title'].split("(", 1)
            title = original_title[0].split(":", 1)[1][1:-1]
            year = original_title[1].replace(")", "")
            star = movie.find("div", {'class': 'gmr-rating-item'}).text

            r = requests.get('https://api.gdriveplayer.us/v1/movie/search?title={}&year={}'.format(title, year),
                             headers={'accept': 'application/json'})

            if r.json() is None:
                pass
            else:
                gdplayer = r.json()[0]
                url = "http://database.gdriveplayer.us/player.php?imdb={}".format(gdplayer['imdb'])

                item = {
                    'title': gdplayer["title"],
                    'year': gdplayer["year"],
                    'url': movie.a['href'],
                    'image': gdplayer["poster"],
                    'star': star,
                    'imdb': gdplayer["imdb"],
                    'genre': gdplayer["genre"].split(",", 1)[0] if gdplayer["genre"] else "empty",
                    'duration': gdplayer["runtime"] if gdplayer["runtime"] else "empty",
                    'video_url': url
                }

                # requests.post('http://127.0.0.1:8000/refresh_movie/', data=item)
                print('added: ',
                      item['title'],
                      item['year'],
                      item['image'],
                      item['star'],
                      item['imdb'],
                      item['genre'],
                      item['duration'],
                      item['video_url']
                      )
                requests.post('http://moviephrestfullapi.herokuapp.com/refresh_movie/', data=item)


if __name__ == "__main__":
    scheduler = BackgroundScheduler()
    scheduler.add_job(startSpider, 'interval', hours=12)
    scheduler.start()

    print('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))

    try:
        # This is here to simulate application activity (which keeps the main thread alive).
        while True:
            time.sleep(10000)
    except (KeyboardInterrupt, SystemExit):
        # Not strictly necessary if daemonic mode is enabled but should be done if possible
        scheduler.shutdown()
