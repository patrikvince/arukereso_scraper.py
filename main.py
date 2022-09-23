#! python3
# iphone.py - Save the iphones prizes to a csv file every week and send an email

import requests, time, schedule, os
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime

from email import encoders
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

from keep_alive import keep_alive

URLS = [
    'https://www.arukereso.hu/mobiltelefon-c3277/apple/',
    'https://www.arukereso.hu/mobiltelefon-c3277/apple/?start=25'
]
PATH = './iphone_prices.csv'


def get_soup(url):
    req = requests.get(url)
    req.raise_for_status()
    soup = BeautifulSoup(req.text, 'html.parser')

    return soup


def get_items(soup):
    names = get_iphones(soup)
    prices = get_prices(soup)

    results = get_name_and_prices(names, prices)

    return results


def get_links(soup):
    links = soup.find_all('a')
    li = [i.get_text().strip() for i in links if len(i.get_text()) > 1]

    return li


def get_iphones(soup):
    names = []

    name_divs = soup.find_all('div', {'class': 'name ulined-link'})

    for name in name_divs:
        name = name.text
        name = name.replace('Apple ', '')
        name = name.replace(' Mobiltelefon', '')
        names.append(name.strip())

    return names


def make_one_dict(li):
    results = dict()

    for items in li:
        for k, v in items.items():
            results[k] = v

    return results


def make_one_list(li):
    results = []

    for items in li:
        for item in items:
            results.append(item)

    return results


def get_prices(soup):
    prices = []

    price_divs = soup.find_all('div', {'class': 'price'})

    for price in price_divs:
        price = price.text
        price = price.replace(' Ft-tól', '')
        price = price.replace(' ', '')
        prices.append(price.strip())

    return prices


def get_name_and_prices(phones, prices):
    lis = dict(zip(phones, prices))

    return lis

def concate_dicts(dictionary, dictionary1):
    # need Python 3.9+
    #results = dictionary | dictionary1

    # Python 3
    results = {**dictionary, **dictionary1}

    return results


def make_excel(path, dictionary=None, data_frame=None, header=None, time=None):

    header = []
    df = pd.DataFrame()
    message = None

    if time is None:
        time = get_time()

    if header is not None:
        for h in header:
            header.append(h)

    if data_frame is None:
        df['Name'] = dictionary.keys()
        df['Price'] = dictionary.values()

        message = f'Excel is made at {time}'
    else:
        datas = pd.read_csv(path, sep=';')
        df = datas.merge(data_frame, how='outer')
      
        message = f'Excel updated in {time}'

    df.to_csv(path, sep=';', index=False)

    print(message)


def update_excel(dictionary, path):

    time = get_time()
    df = pd.DataFrame()
    df['Name'] = dictionary.keys()
    df[time] = dictionary.values()
  
    make_excel(path=path, data_frame=df)


def send_email(path):
    subject = 'Weekly iPhone prizes'
    body = 'mhm'
    sender_email = os.environ['SENDER_EMAIL']
    receiver_email = os.environ['RECEIVER_EMAIL']
    password = os.environ['PASSWORD']

    # Create a multipart message and set headers
    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = receiver_email
    message['Subject'] = subject
    message['Bcc'] = receiver_email  # Recommended for mass emails

    # Add body to email
    message.attach(MIMEText(body, 'plain'))

    filename = path[2:]

    # Open PDF file in binary mode
    with open(filename, 'rb') as attachment:
        # Add file as application/octet-stream
        # Email client can usually download this automatically as attachment
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.read())

    # Encode file in ASCII characters to send by email
    encoders.encode_base64(part)

    # Add header as key/value pair to attachment part
    part.add_header(
        'Content-Disposition',
        f'attachment; filename= {filename}',
    )

    # Add attachment to message and convert message to string
    message.attach(part)
    text = message.as_string()

    # Log in to server using secure context and send email
   # context = ssl.create_default_context()
    with smtplib.SMTP('smtp.office365.com', 587) as server:
        server.starttls()
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, text)

    print(f'Email sent to {receiver_email} at {get_time()}')


def get_time(mins=False):
    now = datetime.now()
    if not mins:
      time = now.strftime('%m/%d/%Y')
    else:
      time = now.strftime('%m/%d/%Y, %H:%M')
    return time


def alive(mins):
    message = f'The server is alive at {get_time(mins)}!\n'
    f = open('log.txt', 'a', encoding='UTF-8')
    f.write(message)
 

def main():
    items = []
    for url in URLS:

        soup = get_soup(url)
        items.append(get_items(soup))

    items = make_one_dict(items)

    print(get_time(mins=True))
    #make_excel(path=PATH, dictionary=items)

    
    #update_excel(items, PATH)
    #send_email(PATH)

    #schedule.every(10).minutes.do(alive, mins=True)
    
    schedule.every().monday.at('02:00').do(get_soup, url=url)
    schedule.every().monday.at('02:00').do(get_items, soup=soup)
    schedule.every().monday.at('02:00').do(update_excel, dictionary=items, path=PATH)
    schedule.every().monday.at('02:00').do(send_email, path=PATH)

    keep_alive()

    while True:
        schedule.run_pending()
        time.sleep(1)

      
if __name__ == '__main__':
    main()
