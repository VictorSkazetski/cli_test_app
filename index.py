import sys
from month import Month
from datetime import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
import concurrent.futures
from selenium import webdriver
import requests
import re
import os
import shutil


def RepresentsInt(s):
    try: 
        int(s)
        return True
    except ValueError:
        return False


def get_user_input():
    check_user_input(sys.argv[1:])
    return  list([int(arg) for arg in sys.argv[1:]]) 


def check_user_input(arg):
    current_year = datetime.today().year
    year_list = list(range(current_year,current_year - 22, -1))
    if not arg:
        print("Не ввели параметры :(")
        exit(1)
    elif len(arg) != 2:
        print("Не ввели нужное(2) количество параметров :(")
        exit(1)
    else:
        month, year = list(arg)
        if RepresentsInt(month) and RepresentsInt(year):   
            if int(month) in list(map(int, Month)) and int(year) in year_list:
                print("Аргументы валидны :)")
            else:
                print("Поменяйте аргументы местами либо сделайте их меньше :(")
                exit(1)
        else:
            print("Ввели не числовой формат :(")
            exit(1)


def get_urls():
    urls = []
    page = 1
    while True:
        url = f"https://www.smashingmagazine.com/category/wallpapers/page/{page}/"
        req = requests.get(url)
        soup = BeautifulSoup(req.text, 'html.parser')
        if soup.find('h2'):
            if soup.find('h2').text == "Uh-Oh, We Lost Your Page! (404) ":
                return urls
        urls.append(url)
        page+=1


def send_req(url):
    op = webdriver.ChromeOptions()
    op.add_argument('headless')
    driver = webdriver.Chrome(ChromeDriverManager().install(),options=op)
    driver.get(url)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    driver.quit()
    return soup


def get_pages(urls):
    pages = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for url in urls:
            futures.append(executor.submit(send_req, url))
        for future in concurrent.futures.as_completed(futures):
            pages.append(future.result())
        return pages


def get_date_urls_from_pages(pages):
    urls = { "data":[]}


    def add_url(url):
        urls["data"].append(url)
    
    
    for page in pages:
        tag_inside = [tag for tag in page.find_all("h1",class_='article--post__title')]
        for tag in tag_inside:
            month_year = tag.find('a').get('href').split("-")
            key = "-".join(month_year[-2:]).replace('/', '')
            url = {}
            url[key] = "https://www.smashingmagazine.com"+tag.find('a').get('href')
            add_url(url)
    only_date_urls = []
    i = 0
    for item in urls['data']:
        for key in item.keys():
            if any(char.isdigit() for char in key):
                only_date_urls.append(urls['data'][i])
            i+=1
    return only_date_urls


def match_url(date_urls, user_date):
    i=0
    for item in date_urls:
        for date in item.keys():
            if date == user_date:
                print(date_urls[i][date] )
                return date_urls[i][date] 
        i+=1


def get_imgs_urls(url):
    if url == None:
        print("Нету картинок на эту дату :(")
        exit(1)
    else:
        soup = send_req(url)
        links = [a['href'] for a in soup.find_all('a', href=re.compile('wallpapers'))]
        return links


def get_month_name(month_num):
    for month in Month:
        if month.value == month_num:
            return month.name


def create_directory(dir_name):
    directory = f"{os.path.dirname(os.path.realpath(__file__))}\{dir_name}"
    if not os.path.isdir(directory):
        os.makedirs(dir_name)
        return directory
    else:
        shutil.rmtree(dir_name)
        os.makedirs(dir_name)
        return directory
    


def extract_single_image(img, dir_path):
    file_name = img.split('/')[-1]
    path = f"{dir_path}/{file_name}"
    print(path)
    try:
        r = requests.get(img, stream=True)
        if r.status_code == 200:
            with open(path, 'wb') as f:
                for chunk in r:
                    f.write(chunk)
            return "Completed"
    except Exception as e:
            return "Failed"


def download_imgs(images_urls, dir_path):
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_url = {executor.submit(extract_single_image, image_url, dir_path) for image_url in images_urls}
        for future in concurrent.futures.as_completed(future_to_url):
            try:
                url = future_to_url[future]
            except Exception as e:
                pass
            try:
                data = future.result()
                print(data)
            except Exception as exc:
                print('%r generated an exception: %s' % (url, exc))


if __name__ == "__main__":
    urls = get_urls()
    pages = get_pages(urls)
    date_urls = get_date_urls_from_pages(pages)
    month, year = get_user_input()
    user_url = match_url(date_urls, f"{get_month_name(month)}-{year}")
    imgs_urls = get_imgs_urls(user_url)
    dir_path = create_directory(f"{get_month_name(month)}-{year}")
    download_imgs(imgs_urls, dir_path)
    
    

