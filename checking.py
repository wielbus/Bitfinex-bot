from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support import expected_conditions as EC
import asyncio
import bitfinex
import pandas as pd
from dotenv import load_dotenv
import os
from telethon import TelegramClient

url_cTrader =  'XXX'
refresh_cTrader = 5 # seconds

load_dotenv()
my_id = int(os.environ.get('TELEGRAM_MY_ID'))
tg_api_id = os.environ.get('TELEGRAM_API_ID')
tg_api_hash = os.environ.get('TELEGRAM_API_HASH')
bot_api = os.environ.get('TELEGRAM_BOT_API')

bot = TelegramClient('bot_anon', tg_api_id, tg_api_hash).start(bot_token=bot_api)

chrome_path = 'XXX'
chromedriver_path = 'XXX'
user_dir_path = 'XXX'

browser_options = webdriver.ChromeOptions()
# browser_options.add_argument(f'--user-data-dir={user_dir_path}')
# browser_options.add_argument(r'--profile-directory=Default')
# browser_options.add_argument('--headless')
browser_options.add_argument('--start-maximized')
browser_options.add_argument('--window-size=1920,1080')

browser_options.binary_location = chrome_path
browser = webdriver.Chrome(service = Service(chromedriver_path), options = browser_options)

def cTrader_positions_fun():
    cTrader_pairs = ['EURUSD','GBPUSD','XAGUSD','XAUUSD']
    while(True):
        try:
            browser.refresh()
            browser.execute_script("document.body.style.zoom='25%'")
            WebDriverWait(browser, 5).until(EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div/div/div[2]/div[7]/div/div/div[2]/div/div/div[1]/div[2]/div/div/div/div/div[2]/div/div/div/div[1]")))
            browser.execute_script("document.body.style.zoom='100%'")
            positions = browser.find_elements(By.XPATH, "/html/body/div[1]/div/div/div[2]/div[7]/div/div/div[2]/div/div/div[1]/div[2]/div/div/div/div/div[2]/div/div/div/div[1]/*")
            temp = []
            indexes = [1,3,5,6,7,8,9,10,11,12,13]
            for i in positions:
                temp.append(i.text.split('\n'))

            for i in temp:
                for j in sorted(indexes, reverse=True):
                    i.pop(j)
            
            positions = pd.DataFrame(temp, columns=['ID','Symbol','Direction'])
            positions['Amount'] = None
            positions = positions[positions['Symbol'].isin(cTrader_pairs)]
            positions = positions.reset_index(drop=True)

            return positions
        except:
            pass

async def check():
    while(True):
        try:
            global existing_positions
            
            cTrader_positions = cTrader_positions_fun()

            temp_positions = pd.DataFrame(columns=['ID','Symbol','Direction','Amount'])
            print(cTrader_positions)
            print(existing_positions)

            cTrader_IDs = set(cTrader_positions['ID'])
            existing_IDs = set(existing_positions['ID'])
            to_Open_IDs = cTrader_IDs - existing_IDs
            to_Close_IDs = existing_IDs - cTrader_IDs
            same_IDs = cTrader_IDs & existing_IDs

            if len(to_Close_IDs) > 0:
                for i in to_Close_IDs:
                    response = bitfinex.Close_position(existing_positions[existing_positions['ID']==i]['Symbol'].values[0], existing_positions[existing_positions['ID']==i]['Direction'].values[0], existing_positions[existing_positions['ID']==i]['Amount'].values[0])
                    if response == 200:
                        await bot.send_message(my_id, f"Close: {i}")
                    else:
                        await bot.send_message(my_id, f"Couldn't close: {i}")
                        temp_positions.loc[len(temp_positions)] = existing_positions[existing_positions['ID']==i].values[0]

            if len(to_Open_IDs) > 0:
                for i in to_Open_IDs:
                    if bitfinex.Spread(cTrader_positions[cTrader_positions['ID']==i]['Symbol'].values[0]) <= bitfinex.acceptable_spread:
                        amount = (bitfinex.collateral / bitfinex.Current_price(cTrader_positions[cTrader_positions['ID']==i]['Symbol'].values[0])) * bitfinex.leverage
                        response = bitfinex.Open_position(cTrader_positions[cTrader_positions['ID']==i]['Symbol'].values[0], cTrader_positions[cTrader_positions['ID']==i]['Direction'].values[0], amount)
                        if response == 200:
                            await bot.send_message(my_id, f"Open: {i}")
                            temp_positions.loc[len(temp_positions)] = cTrader_positions[cTrader_positions['ID']==i].values[0]
                            temp_positions.loc[len(temp_positions)-1,'Amount'] = amount
                        else:
                            await bot.send_message(my_id, f"Couldn't open: {i}")
                    else:
                        await bot.send_message(my_id, f"Too high spread to open position: {i}")

            for i in same_IDs:
                temp_positions.loc[len(temp_positions)] = existing_positions[existing_positions['ID']==i].values[0]


            existing_positions = temp_positions.copy(deep=True)
            existing_positions = existing_positions.reset_index(drop=True)
            existing_positions.to_csv('op.csv', index=False)

            await asyncio.sleep(refresh_cTrader)

        except Exception as error:
            await bot.send_message(my_id, f"Error: {error}")


existing_positions = pd.read_csv('op.csv')
browser.get(url_cTrader)


# asyncio.run(check())
with bot:
    bot.loop.run_until_complete(check())

browser.quit()

