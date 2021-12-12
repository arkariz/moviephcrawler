import os
import requests

from apscheduler.schedulers.background import BackgroundScheduler
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By

def setDriver():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
    return webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), chrome_options=chrome_options)
    # return webdriver.Chrome(executable_path="D:\GitHub\moviephRestfullApi\movieph\moviephApi\chromedriver.exe",
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
    driver.get('https://103.194.171.205/')  # Accessing Web
    driver.implicitly_wait(3)

    add = driver.find_element(by=By.XPATH, value='//*[@id="baner_close"]')
    add.click()

    html = driver.page_source  # Get HTML
    soup = BeautifulSoup(html, 'html.parser')
    cat_box = soup.find("div", {"class": "row grid-container gmr-module-posts"})

    movie_container = []
    for movie in reversed(cat_box.find_all('div', {'class': 'gmr-item-modulepost'})):
        movie_container.append(movie)

    if movie_container[-1].a['href'] == getNewestMovie():
        print("list already up to date")
    else:
        items = []
        for movie in movie_container:
            original_title = movie.a['title'].split(":", 1)
            title = original_title[1]
            star = movie.find("div", {'class': 'gmr-rating-item'}).text
            item = {
                'title': title,
                'url': movie.a['href'],
                'image': movie.img['src'],
                'star': star
            }
            print('added: ', item['title'])

            # requests.post('http://127.0.0.1:8000/refresh_movie/', data=item
            requests.post('http://moviephrestfullapi.herokuapp.com/refresh_movie/', data=item)

            items.append(item)


if __name__ == "__main__":
    scheduler = BackgroundScheduler()
    scheduler.add_job(startSpider, 'interval', minutes=1)
    scheduler.start()