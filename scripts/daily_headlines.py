from bs4 import BeautifulSoup
import requests
from datetime import datetime
import csv


URL = "https://www.voaswahili.com/"

page = requests.get(URL)
soup = BeautifulSoup(page.content, "html.parser")
home_page_links = []

for a_href in soup.find_all("a", href=True, class_="img-wrap"):
    if a_href["href"].startswith('/a/'):
        home_page_links.append("https://www.voaswahili.com"+a_href["href"])

"""
- Loop through the list of links from the home page. 
- Open the links and look for the content in the article,
- Split the paragraphs into sentences then write the sentence to a csv file
"""

for link in home_page_links:
    page = requests.get(link)
    soup = BeautifulSoup(page.content, "html.parser")
    page_paragraph = soup.find_all('div', class_="content-floated-wrap fb-quotable")
    for paragraph in page_paragraph:
        paragraph_list = paragraph.get_text().splitlines()
        
        # remove empty strings from list
        while("" in paragraph_list) :
            paragraph_list.remove("")
            
        # split at fullstops
        nested_list = [string.split(".") for string in paragraph_list]
        
        # flatten the now nested list
        flat_list = [nest for sublist in nested_list for nest in sublist]
        
        # remove empty strings from list
        while("" in flat_list) :
            flat_list.remove("")
            
        # make everything a flat nested list, for purposes of saving to csv
        list_of_list = [[string] for string in flat_list]
            
        # current date
        current_date = datetime.today().strftime("%d-%m-%y")
            
        with open(f'./datasets/{current_date}.csv', 'a', newline='') as csvfile:
            writer= csv.writer(csvfile, delimiter=' ')
            writer.writerows(list_of_list)
