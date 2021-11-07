from bs4 import BeautifulSoup
import time
import pickle
import requests
from selenium import webdriver
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from selenium.webdriver.firefox.options import Options

profile = webdriver.FirefoxProfile()
profile.set_preference('browser.download.folderList', 2) # custom location
profile.set_preference('browser.download.manager.showWhenStarting', False)
profile.set_preference('browser.download.dir','/tmp')
profile.set_preference('browser.helperApps.neverAsk.saveToDisk', 'application/octet-stream')

result = requests.get("https://standardebooks.org/ebooks?page=1&per-page=48")

links=[]
src = result.content
soup = BeautifulSoup(src, 'lxml')

f = open("links.txt", "a")

t3 = soup.find_all('nav')[1]
t3 = t3.find_all('li')
no_of_pages = len(t3)
for i in range(1, no_of_pages+1):
    site = f"https://standardebooks.org/ebooks?page={i}&per-page=48"
    result = requests.get(site)
    src = result.content
    soup = BeautifulSoup(src, 'lxml')

    t1 = soup.find('ol')
    t2 = t1.find_all('a')
    t2 = [i for i in t2 if 'https' not in i['href']]
    print(i)


    for i in range(0,len(t2),2):
        f.write("https://standardebooks.org" + t2[i]['href'] + '\n')


browser = webdriver.Firefox(profile,executable_path = 'K:\geckodriver-v0.30.0-win64\geckodriver.exe')
with open('links.txt','r') as f:
    link=f.readlines()
    print(len(link))
    for i in link[461:]:
        browser.get(i)
        parent_handle = browser.current_window_handle
        linkElem = browser.find_element_by_link_text('Compatible epub')
        linkElem.click()       
        handles = browser.window_handles
        size = len(handles)
        for x in range(size):
            if handles[x] != parent_handle:
                    browser.switch_to.window(handles[x])
                    time.sleep(5.0)
                    browser.close()
                
        browser.switch_to.window(parent_handle)
        
