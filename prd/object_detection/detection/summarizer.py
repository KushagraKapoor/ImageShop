from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
from bs4 import BeautifulSoup
from .sum import initialize

summarizer=initialize()

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

def prd_info(URL):
    page_content = get_page_content_with_selenium(URL)
    soup = BeautifulSoup(page_content, "html.parser")

    # Finding the product details on the product page
    product = soup.find("div", attrs={"id": "dp"})

    prd_details = {}

    # Retrieving product title
    try:
        title_element = soup.find("span", attrs={"id": "productTitle"})
        prd_details['title'] = title_element.text.strip() if title_element else "NA"
    except AttributeError:
        prd_details['title'] = "NA"

    # Retrieving price
    try:
        price_element = soup.find("span", attrs={'class': 'a-price-whole'})
        prd_details['price'] = price_element.text.strip() if price_element else "NA"
    except AttributeError:
        prd_details['price'] = "NA"

    # Retrieving product rating
    try:
        rating_element = soup.find("span", attrs={'class': 'a-icon-alt'})
        prd_details['rating'] = rating_element.text.strip() if rating_element else "NA"
    except AttributeError:
        prd_details['rating'] = "NA"

    # Retrieving review count
    try:
        review_count_element = soup.find("span", attrs={'id': 'acrCustomerReviewText'})
        prd_details['reviews'] = review_count_element.text.strip() if review_count_element else "NA"
    except AttributeError:
        prd_details['reviews'] = "NA"

    # Retrieving image URL
    try:
        image_element = soup.find("img", attrs={"id": "landingImage"})
        prd_details['image'] = image_element['src'] if image_element else "NA"
    except AttributeError:
        prd_details['image'] = "NA"

    # Retrieving product description
    try:
        description_element = soup.find("ul", attrs={'class': 'a-unordered-list a-vertical a-spacing-mini'})
        description_text = " ".join([item.text.strip() for item in description_element.find_all("li", attrs={'class': 'a-spacing-mini'})]) if description_element else "NA"
    except AttributeError:
        description_text = "NA"

    # Summarizing product description if available
    try:
        if description_text and description_text != "NA":
            summary = summarizer(description_text, max_length=150, min_length=25, do_sample=False)
            prd_details['summary'] = summary[0]['summary_text']
        else:
            prd_details['summary'] = "NA"
    except Exception as e:
        prd_details['summary'] = f"Error summarizing description: {str(e)}"

    # Retrieving product link
    try:
        link_element = product.find("a", attrs={"class": 'a-link-normal s-no-outline'})
        if link_element:
            # Removing session-specific parameters from URL
            link = link_element['href'].split('?')[0]
            prd_details['link'] = f"https://www.amazon.in{link}"
        else:
            prd_details['link'] = "NA"
    except AttributeError:
        prd_details['link'] = "NA"

    # Retrieving customer review summary
    try:
        review_summary_element = soup.find("div", attrs={"id": "product-summary"})
        review_summary_text = review_summary_element.find("span").text.strip() if review_summary_element else "NA"
        prd_details['review_summary'] = review_summary_text
    except AttributeError:
        review_element_S = product.find("span", attrs={"class": 'a-spacing-small'})
        prd_details['review_summary'] = review_element_S

    return prd_details

# Example usage
