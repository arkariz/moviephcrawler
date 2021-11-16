import os
import requests
import time

from tzlocal import get_localzone
from apscheduler.schedulers.background import BackgroundScheduler
from bs4 import BeautifulSoup
from selenium import webdriver

def setDriver():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
    return webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), chrome_options=chrome_options)
    # return webdriver.Chrome(executable_path="utils/chromedriver.exe", options=chrome_options)


def getNewestMovie():
    r = requests.get('http://moviephrestfullapi.herokuapp.com/newest_movie/', headers={'accept': 'application/json'})
    print("checking newest movie")
    if r.status_code == 204:
        return 'empty'
    else:
        return r.json()['url']


def startSpider():
    driver = setDriver()
    driver.get('https://pahe.ph/')  # Accessing Web
    html = driver.page_source  # Get HTML
    soup = BeautifulSoup(html, 'html.parser')
    cat_box = soup.find("div", {"class": "cat-box-content"})

    movie_container = []
    for movie in reversed(cat_box.find_all('div', {'class': 'post-thumbnail'})):
        movie_container.append(movie)

    if movie_container[-1].a['href'] == getNewestMovie():
        print("list already up to date")
    else:
        items = []
        for movie in movie_container:
            original_title = movie.a['original-title'].split(")", 1)
            title = original_title[0]
            item = {
                'title': title,
                'url': movie.a['href'],
                'image': movie.img['src']
            }
            print('added: ', item['title'])

            requests.post('http://moviephrestfullapi.herokuapp.com/refresh_movie/', data=item)
            items.append(item)


if __name__ == "__main__":
    scheduler = BackgroundScheduler()
    scheduler.configure(timezone=get_localzone())
    scheduler.add_job(startSpider, 'interval', minutes=1)
    scheduler.start()
    print('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))

    try:
        # This is here to simulate application activity (which keeps the main thread alive).
        while True:
            time.sleep(2)
    except (KeyboardInterrupt, SystemExit):
        # Not strictly necessary if daemonic mode is enabled but should be done if possible
        scheduler.shutdown()