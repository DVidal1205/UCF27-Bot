from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import nextcord
from nextcord.ext import commands
import asyncio
from datetime import datetime, timedelta
import os
import requests, bs4
import re

class Daily(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.schedule_event = asyncio.Event()

    @commands.Cog.listener()
    async def on_ready(self):
        # Set the scheduled task to run at 9:00 AM
        scheduled_time = "9:00"
        scheduled_time = datetime.strptime(scheduled_time, "%H:%M").time()

        while True:
            # Get the current time
            now = datetime.now().replace(microsecond=0, second=0).time()  # Truncate milliseconds
            print(now, scheduled_time)
            print(scheduled_time == now)

            # Check if the current time matches the scheduled time
            if now == scheduled_time:
                # Gather all Scraped Events
                events = scrape_events()
                if events:
                    channel_id = 1169414824531341352
                    channel= self.bot.get_channel(channel_id)
                    await channel.send(f'Good morning everyone, here are the events for today and tomorrow!')
                    for event in events:
                        await channel.send(embed=event)

            # Check Every Minute
            await asyncio.sleep(60)

def is_today_or_tomorrow(date_str):
    
    # Use regular expressions to extract date and time
    date_match = re.search(r'\w+, (\w+ \d+)', date_str)
    time_match = re.search(r'(\d+:\d+\w+)', date_str)

    if date_match and time_match:
        extracted_date = date_match.group(1)
        extracted_time = time_match.group(1)

        # Get today's date and tomorrow's date
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)

        # Parse the extracted date into a datetime object
        event_date = datetime.strptime(extracted_date, "%B %d").replace(year=datetime.now().year)

        # Check if the event date is today or tomorrow
        if event_date.date() == today and datetime.strptime(extracted_time, "%I:%M%p").time() > datetime.now().time():
            return True
        elif event_date.date() == tomorrow:
            return True

    return False

def scrape_events():
 
    chrome_options = webdriver.ChromeOptions()
    chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), chrome_options=chrome_options)
    driver.get("https://knightconnect.campuslabs.com/engage/events")
    wait = WebDriverWait(driver, 20)  

    # Press Show More a maximum amount of times
    while True:
        try:
            # Find and click the "Show More" button
            show_more_button = driver.find_element(By.XPATH, '//span[@style="position: relative; opacity: 1; font-size: 1rem; letter-spacing: 0px; text-transform: uppercase; font-weight: 500; margin: 0px; user-select: none; padding-left: 16px; padding-right: 16px; color: rgb(0, 0, 0);"][text()="Load More"]')
            driver.execute_script("arguments[0].click();", show_more_button)
            time.sleep(1)
        except:
            break
    
    # Use XPath to find div elements with the inline style for an event - BAD DOM PRACTICE, KNIGHTCONNECT SUCKS
    xpath_expression = '//div[@style="box-sizing: border-box; padding: 10px; width: 100%; height: auto;"]'
    elements = wait.until(EC.presence_of_all_elements_located((By.XPATH, xpath_expression)))

    # Create the list of event embeds to return
    events = []

    # Gather all of the element formats and create embed objects to append to the return type
    for element in elements:

        # Grab the link to the event on KnightConnect
        link_element = element.find_element(By.TAG_NAME, "a")
        link_url = link_element.get_attribute("href")

        # Grab the style block of the image element, then grab the URL from the style block - AGAIN BAD PRACTICE, GET ON THIS KNIGHTCONNECT
        img_div = element.find_element(By.XPATH, './/div[@role="img"]')
        style_attribute = img_div.get_attribute('style')

        # Find the start and end positions of the URL
        start = style_attribute.find('url("')
        end = style_attribute.find('.png', start) + len('.png')

        # Base Case URL
        image_url = None
        if start != -1 and end != -1:
            start += len('url("')
            image_url = style_attribute[start:end]
        if image_url == None:
            # 404 Error not Found Image
            image_url = "https://i0.wp.com/learn.onemonth.com/wp-content/uploads/2017/08/1-10.png?fit=845%2C503&ssl=1"

        # Grab the text from the element and split it into the proper fields
        text = element.text.split("\n")
        title = text[0]
        date = text[1]
        location = text[2]
        club = text[3]
        
        if is_today_or_tomorrow(date):
            # Create the embed object with the proper fields
            event_embed = nextcord.Embed(
                    title = f'{title}',
                    description = f'{club} is hosting an event!',
                    color = nextcord.Colour.purple(),
                    url=link_url
                )
            event_embed.set_image(url=image_url)
            event_embed.add_field(name='Date', value=f'{date}', inline=False)
            event_embed.add_field(name='Location', value=f'{location}', inline=False)
            event_embed.add_field(name='Link', value=f'Click the link for more details!\n{link_url}', inline=False)

            # Append the embed object to the list of events
            events.append(event_embed)

    # Close the Chrome window
    driver.quit()  

    return events



def setup(bot):
    bot.add_cog(Daily(bot))