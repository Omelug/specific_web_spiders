from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import re
import sys
import os

fireFoxOptions = webdriver.FirefoxOptions()
options = Options()
options.headless = True
options.add_argument('-headless')
driver = webdriver.Firefox(options=options)

def wait_for_number_of_elements(locator, number, timeout=10):
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: len(d.find_elements(*locator)) == number
        )
    except:
        print(f"Smula {len(d.find_elements(*locator))}")

def click_load_more_button():
    #Zobrazit dalsi reakce button
    button_selector = (By.CSS_SELECTOR, 'button.d_J.d_M.d_O.g_d0[data-dot="nacist_nove_podkomentare"]')
    print(f"        {len(driver.find_elements(*button_selector))} Zobrazit buttons")
    try:
        i = 0
        for _ in driver.find_elements(*button_selector):
            load_more_button = WebDriverWait(driver, 60).until(
                EC.element_to_be_clickable(button_selector)
            )
            load_more_button.click()
            print(f"        Zobrazit dalsi reakce button {i}")
            i += 1
        #wait_for_number_of_elements(button_selector, 0, 5)
    except:
        print("     No more buttons", file=sys.stderr)

    # Zobrazit dalsich x odpovedi span
    span_locator = (By.CSS_SELECTOR, 'span.g_dZ')
    try:
        i = 0
        for _ in driver.find_elements(*span_locator):
            span = WebDriverWait(driver, 60).until(
                EC.element_to_be_clickable(span_locator)
            )
            span.click()
            driver.implicitly_wait(0.2)
            print(f"        Clicked on {i}/{len(driver.find_elements(*span_locator))} span")
            i += 1
        #wait_for_number_of_elements(button_selector, 0, 5)
    except Exception as e:
        print(f"        EEE Now driver see {len(driver.find_elements(*span_locator))} spans")
        print(f" exeption {e}" )
        print("     No more Zobrazit dalsich x reakci span", file=sys.stderr)

if __name__ == "__main__":
    tree = ET.parse("novinky_cz/sitemap_articles_0.xml")
    root = tree.getroot()
    print(root)
    namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
    loc_elements = root.findall(".//ns:loc", namespaces=namespace)
    for loc in loc_elements:
        match = re.search(r'(\d+)(?=\D*$)', loc.text)
        if match:
            last_number = match.group(1)
        else:
            print(f"No number found in the URL {loc.text}", file=sys.stderr)
            exit(1)
        url = f"https://diskuze.seznam.cz/v3/novinky/discussion/www.novinky.cz%2Fclanek%2F{last_number}?sentinel=ahoj"
        print(f"Started {url}")
        page_number = 1
        while True:
            path = f"./out/{last_number}-{page_number}.html"
            path_end = f"./out/{last_number}-{page_number}-end.html"

            if os.path.isfile(path):
                print(f"    {path} already exists")
                page_number += 1
                continue
            if os.path.isfile(path_end):
                print(f"    {path_end} already exists")
                print(f"    {page_number} end")
                break
            driver.get(f"{url}&discussion--page={page_number}")
            click_load_more_button()
            content = driver.page_source
            soup = BeautifulSoup(content, "html.parser")
            data = soup.find('div', {'class', 'ogm-discussion-timeline'})
            if data is None:
                print("Error data is None")
                break
            pattern = "Zobrazit dal"
            while re.search(pattern, str(data)):
                print(f"\033[91m            Zobrazit in {path}\033[0m")
                click_load_more_button()
                content = driver.page_source
                soup = BeautifulSoup(content, "html.parser")
                data = soup.find('div', {'class', 'ogm-discussion-timeline'})

            #delete useless elements
            for div in data.find_all('div', {'class': 'g_dG'}):
                div.decompose()
            for div in data.find_all('button', {'class': 'd_Y'}):
                div.decompose()
            for div in data.find_all('div', {'class': 'mol-native-advert'}):
                div.decompose()
            last = soup.find('svg', {'class': 'd_D atm-icon__arrow-right'})
            if not last:
                path=path_end

            # delete useless elements
            with open(path, 'w+') as file:
                file.write(f"<a href=\"{loc.text}\"><h2>Clanek</h2></a>")
                file.write(f"<a href=\"{url}\"><h2>Diskuze</h2></a>")
                file.write(str(data))
                print(f"    {path} saved")

            if not last:
                break
            page_number += 1
    driver.quit()
