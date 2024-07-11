from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
from bs4 import BeautifulSoup
import random


def get_page_content_with_selenium(URL):
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1200')
    options.add_argument('--ignore-certificate-errors')

    driver = webdriver.Chrome(options=options)
    driver.get(URL)

    # Check if CAPTCHA is present
    if "Type the characters you see in this image" in driver.page_source:
        print("CAPTCHA detected. Please solve it manually.")

        # Open a new browser window for manual CAPTCHA solving
        options.headless = False
        driver.quit()
        driver = webdriver.Chrome(options=options)
        driver.get(URL)

        # Wait for the user to solve CAPTCHA
        input("Press Enter after solving the CAPTCHA...")

    # Wait for the page to load completely after CAPTCHA solving
    time.sleep(5)

    page_content = driver.page_source
    driver.quit()
    return page_content

def scrape_amazon(label, color):
    valid_colors = ['red', 'blue', 'black', 'grey', 'pink', 'purple', 'dimgrey', 'white']
    
    person_names = ['person']
    if label.lower() in person_names:
        label = "action figure"
    
    if color.lower() not in valid_colors:
        query = label.lower()
    else:
        query = f"{color.lower()}+{label.lower()}"

    URL = f"https://www.amazon.in/s?k={query}"
    
    page_content = get_page_content_with_selenium(URL)
    soup = BeautifulSoup(page_content, "html.parser")

    # Finding all products on the search results page
    products = soup.find_all("div", attrs={"data-component-type": "s-search-result"})
    
    scraped_data = []

    for product in products:
        # Check if the product link is an SSPA link, ignore if true
        link_element = product.find("a", attrs={"class": 'a-link-normal s-no-outline'})
        if link_element and "/sspa/click" in link_element['href']:
            continue
        
        prd_details = {}

        # Retrieving product title
        try:
            title_element = (product.find("span", attrs={"class": 'a-size-medium a-color-base a-text-normal'}) or 
                             product.find("span", attrs={"class": "a-size-base-plus a-color-base a-text-normal"}) or 
                             product.find("span", attrs={"class": "a-section a-spacing-none a-spacing-top-small s-title-instructions-style"}))
            prd_details['title'] = title_element.text.strip() if title_element else "NA"
        except AttributeError:
            prd_details['title'] = "NA"

        # Retrieving product link
        try:
            raw_link = f"https://www.amazon.in{link_element['href']}" if link_element else "NA"
            prd_details['link'] = raw_link.split("?")[0]  # Extract the canonical link before any query parameters
        except AttributeError:
            prd_details['link'] = "NA"

        # Retrieving price
        try:
            price_element = product.find("span", attrs={'class': 'a-price-whole'})
            prd_details['price'] = price_element.text.strip().replace(',', '') if price_element else "NA"
        except AttributeError:
            prd_details['price'] = "NA"

        # Retrieving product rating
        try:
            rating_element = product.find("span", attrs={'class': 'a-icon-alt'})
            prd_details['rating'] = rating_element.text.strip().replace(',', '') if rating_element else "NA"
        except AttributeError:
            prd_details['rating'] = "NA"

        # Retrieving review count
        try:
            review_count_element = product.find("span", attrs={'class': 'a-size-base'})
            prd_details['reviews'] = review_count_element.text.strip().replace(',', '') if review_count_element else "NA"
        except AttributeError:
            prd_details['reviews'] = "NA"

        # Retrieving image URL
        try:
            image_element = product.find("img", attrs={"class": "s-image"})
            prd_details['image'] = image_element['src'] if image_element else "NA"
        except AttributeError:
            prd_details['image'] = "NA"

        # Availability (usually not available on search results, so setting as N/A)
        prd_details['availability'] = "N/A"

        # Append product details to list
        scraped_data.append(prd_details)
    
    return scraped_data

# Example usage:

