import re
from bs4 import BeautifulSoup
import requests
from requests.adapters import ConnectionError
import csv
from datetime import datetime


class VoaSwahili():
    def __init__(self, url, sub_folder=None):
        self.url = url
        self.sub_folder = sub_folder
        self.current_date = datetime.today().strftime("%d-%m-%y")
        self.page_links = []

    def get_page_headlines(self):
        page_title_list = []
        page = requests.get(self.url)
        soup = BeautifulSoup(page.content, "html.parser")

        for headline_title in soup.find_all("h4", class_="media-block__title"):
            page_title_list.append(headline_title.get_text())
    
   
        with open(f'sentences/{self.current_date}.csv', 'a') as csvfile:
            writer= csv.writer(csvfile, delimiter='\n')
            writer.writerow(page_title_list)

        for a_href in soup.find_all("a", href=True, class_="img-wrap"):
            self.page_links.append("https://www.voaswahili.com"+a_href["href"])


    def get_page_content(self, content_class):
        for link in self.page_links:
            print(link)
            try: 
                page = requests.get(link)
                soup = BeautifulSoup(page.content, "html.parser")
                page_paragraph = soup.find_all('div', class_=content_class)
                for paragraph in page_paragraph:
                    paragraph_list = paragraph.get_text().splitlines()
                    
                    # remove these items from list strings from list
                    while("" in paragraph_list):
                        paragraph_list.remove("")
                        
                    # split at fullstops
                    # nested_list = [string.split(".") for string in paragraph_list]
                    nested_list = [re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', string) for string in paragraph_list]
                    
                    # flatten the now nested list
                    flat_list = [nest for sublist in nested_list for nest in sublist]

                    # remove some words, spaces from the flat_list
                    to_be_removed_from_list = [" ", "", "Facebook Forum", "live\nDuniani Leo Video Tube", "Duniani Leo"]
                    for i in flat_list:
                        for to_remove in to_be_removed_from_list:
                            if to_remove in flat_list:
                                flat_list.remove(to_remove)
                        
                    # make everything a flat nested list, for purposes of saving to csv
                    list_of_list = [[string] for string in flat_list]
                        
                    with open(f'./sentences/{self.current_date}.csv', 'a', newline='') as csvfile:
                        writer= csv.writer(csvfile, delimiter=' ')
                        writer.writerows(list_of_list)
            except ConnectionError:
                print("CONNECTION ERROR!!!!") 
            

