import time
from decimal import Decimal
from re import sub
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
import csv
from sqlalchemy import create_engine, types

driver = webdriver.Chrome(ChromeDriverManager().install())

# enter your password and database names here
engine = create_engine('mysql://root:*Enter password here*@localhost/*Enter Databse name here*')



products = []  # List to store card name
prices = []  # List to store car price
rarities = []  # List to store card rarity
card_nums = []  # List to store card number
page_num = 1  # Start page


def record_data(page_num):

    driver.get(
        "https://www.tcgplayer.com/search/magic/kaldheim?productLineName=magic&setName=kaldheim&page={}&ProductTypeName=Cards".format(page_num))
    time.sleep(1.5)  # delay for page load
    content = driver.page_source
    soup = BeautifulSoup(content, features="html.parser")

    for a in soup.findAll('a', href=True, attrs={'class': 'search-result__product'}):

        # GET CARD DETAILS
        name = a.find('span', attrs={'class': 'search-result__title'})  # fetch card name
        price_area = a.find('section', attrs={'class': 'search-result__market-price'})  # fetch price area

        ## Get card price - If theres no market price available, catch and produce warning string
        try:
            price = price_area.find('span', attrs={'class': 'search-result__market-price--value'}).text
            price_val = Decimal(sub(r'[^\d.]', '', price))  # convert data into decimal
        except AttributeError:
            price = "No Market Value Available"

        ## Get card rarity - If card has no rarity (i.e. Token, Basic Land), catch and produce string
        rarity_area = a.find('section', attrs={'class': 'search-result__rarity'})
        rarity = rarity_area.find('span')

        card_num_span_space = rarity.find_next_siblings("span")

        try:
            card_num = card_num_span_space.pop().text
        except IndexError:
            card_num = "N/A"

        # Send items to lists
        products.append(name.text)
        prices.append(price_val)
        rarities.append(rarity.text)
        card_nums.append(card_num)

    # Increment page number by 1
    page_num += 1

    # Pagination recursion
    for b in soup.findAll('div', attrs={'class': 'search-layout__pagination'}):
        results_pos = b.find('div', attrs={'class': 'results'})

        if results_pos is None:
            break
        else:
            record_data(page_num)


record_data(page_num)
df = pd.DataFrame({'Card Name': products, 'Number': card_nums, 'Rarity': rarities, 'Market Price (USD)': prices})
df.sort_values(by='Market Price (USD)', ascending=False, inplace=True)
df.to_csv('kaldheim-tcgplayer-data.csv', index=False, encoding='utf-8')

df = pd.read_csv("kaldheim-tcgplayer-data.csv", sep=',', quotechar='\'', encoding='utf8')

# Replace first argument with your sql table name
df.to_sql('kaldheim_cardlist', con=engine, index=False, if_exists='replace')



