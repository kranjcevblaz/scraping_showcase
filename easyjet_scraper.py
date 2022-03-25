import json
import requests
import pandas as pd
from bs4 import BeautifulSoup
from collections import defaultdict
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from datetime import date
from dateutil.relativedelta import relativedelta
import os
import sys
import datetime
import argparse
import numpy as np

# =============================================================================
# RUN SCRIPT FROM EDITOR (instead of command line) -> change run_from_editor = True
# =============================================================================
run_from_editor = False  # default False for scraper to run from command line
# ****** PARAMETERS ******** #
months = 3
dep_airport_list_input = ['LJU', 'SOF', 'GWT']

# =============================================================================
# HEADLESS BROWSER SETTINGS
# =============================================================================
# set to False to get browser UI (runs a bit slower but you see it running in separate browser window)
headless_chrome = True

pathname = os.path.dirname(sys.argv[0])
full_pathname = os.path.abspath(pathname)
CHROMEDRIVER_PATH = f"{full_pathname}/chromedriver"

if headless_chrome:
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(CHROMEDRIVER_PATH, options=chrome_options)
else:
    driver = webdriver.Chrome(CHROMEDRIVER_PATH)

# =============================================================================
# SCRAPE TIMETABLES PAGE
# =============================================================================
destination_source = requests.get('https://www.easyjet.com/en/cheap-flights/timetables').text
soup = BeautifulSoup(destination_source, 'html.parser')
route_list = soup.find('div', {'class': 'route-list'})
destination_link_text = route_list.find_all('a')
origin_rows = route_list.find_all('tr', {'class': 'origin-row'})

save_data_outbound = []
save_data_return = []
flight_id_list = []
flight_num_list = []
localDepTime_list = []
localArrTime_list = []
price_list = []
currency_list = []
outbound_return_list = []


def get_airport_code_from_name():
    # func scrapes and cleans airport codes from Timetables page and assigns to dict of format {
    # 'airport_name':'IATA_airport_code'}
    departure_airports_list = []
    for td in origin_rows:
        td_departure = td.find_all('td')
        for td_dep in td_departure:
            if td_dep.has_attr('rowspan'):
                departure_airports_list.append(td_dep.text)

    departure_airport_name = [i.rsplit(' (', 1)[0] for i in departure_airports_list]
    departure_airport_code = [i.rsplit(' (', 1)[1] for i in departure_airports_list]
    departure_airport_code = [i.replace(')', '') for i in departure_airport_code]

    departure_airport_dict = {departure_airport_code[i]: departure_airport_name[i] for i in
                              range(len(departure_airport_code))}
    return departure_airport_dict


def get_airport_code_country():
    # func gets country based on each IATA airport code
    lowfare_url = 'https://www.easyjet.com/en/low-fare-finder'
    driver.get(lowfare_url)

    source = driver.page_source
    sel_soup = BeautifulSoup(source, 'html.parser')
    dropdown_content = sel_soup.find_all('div', {'class': 'lff-filter-column-content'})[0].find_all('div', {
        'class': 'lff-filter-item'}
                                                                                                    )
    driver.close()
    airport_code_country_list = []
    for option in dropdown_content:
        airport_code_country_list.append(option.text)

    airport_code_country_list = [item.split(', ') for item in airport_code_country_list]
    airport_code_list = [item[0][-3:] for item in airport_code_country_list]
    airport_code_country_list = [item[1] for item in airport_code_country_list]

    airport_code_country_dict = {airport_code_list[i]: airport_code_country_list[i] for i in
                                 range(len(airport_code_list))}
    return airport_code_country_dict


def get_airport_codes():
    destination_list = []
    for link in destination_link_text:
        res = tuple(map(str, link.text.split(' to ')))
        destination_list.append(res)

    res = [(sub[0].replace('\n', ''), sub[1].replace('\n', '')) for sub in destination_list]
    flight_connections_dict = defaultdict(list)

    for k, v in res:
        flight_connections_dict[k].append(v)

    flight_connections_dict = {k: tuple(v) for k, v in flight_connections_dict.items()}
    return flight_connections_dict


def get_all_flights(dep_airport_code, flight_connections_dict, departure_airport_dict):
    arr_airport_names = list(flight_connections_dict[departure_airport_dict[dep_airport_code]])
    arr_airport_codes_list = []

    for airport_name in arr_airport_names:
        arr_airport_codes_list.append(airport_name)

    return arr_airport_codes_list


def get_json_data(dep_airport_code, airport_code_list, airport_code_country, departure_airport_dict):
    appended_flight_data = []
    arr_airport_code = 'None'
    dep_airport_code_country = airport_code_country[dep_airport_code]
    for arr_airport_name in airport_code_list:
        for k, v in departure_airport_dict.items():
            if v == arr_airport_name:
                arr_airport_code = k
        url = "https://www.easyjet.com/ejcms/nocache/jscallbacks/TimetableCallback.aspx?data={{" \
              "%22languageCode%22:%22en%22,%22originIata%22:%22{0}%22,%22destinationIata%22:%22{1}%22," \
              "%22passengers%22:1}}".format(
            dep_airport_code, arr_airport_code
        )
        r = requests.get(url, auth=('user', 'pass'))
        json_data = json.loads(r.text)

        json_flight_data = get_flight_names(json_data)
        for inner_list in json_flight_data:
            inner_list.append(departure_airport_dict[dep_airport_code])
            inner_list.append(dep_airport_code)
            inner_list.append(arr_airport_name)
            inner_list.append(arr_airport_code)
            inner_list.append(dep_airport_code_country)
            inner_list.append(airport_code_country[arr_airport_code])

        appended_flight_data.append(json_flight_data)

    return appended_flight_data


def append_json_results(json_data, save_data_list):
    for day in json_data:
        day_access = day['days']
        for flight in day_access:
            flight_access = flight['flights']
            for flight_dict in flight_access:
                if flight_dict is not None:
                    save_data_list.append(flight_dict)


def append_additional_info(save_data_list, flight_leg):
    for item in save_data_list:
        flight_id_list.append(item['id'])
        flight_num_list.append(item['flightNum'])
        localDepTime_list.append(item['localDepTime'])
        localArrTime_list.append(item['localArrTime'])
        price_list.append(item['price'])
        currency_list.append('GBP')
        outbound_return_list.append(flight_leg)


def get_flight_names(json_data):

    json_access_outbound = json_data['outboundLeg']
    json_access_return = json_data['returnLeg']

    # append data for outbound and return flights
    append_json_results(json_access_outbound, save_data_outbound)
    append_json_results(json_access_return, save_data_return)

    append_additional_info(save_data_outbound, 'outboundLeg')
    append_additional_info(save_data_return, 'ReturnLeg')

    flight_info_list = [list(i) for i in
                        zip(flight_id_list, flight_num_list, localDepTime_list, localArrTime_list, price_list,
                            currency_list, outbound_return_list
                            )]
    return flight_info_list


def transform_dataframe(df):
    df.columns = ['flight_id', 'flight_number', 'LocalDepTime', 'LocalArrTime', 'price', 'currency', 'direction',
                  'from_airport_city', 'from_airport_code', 'to_airport_city', 'to_airport_code', 'from_country',
                  'to_country']
    df['LocalDepTime'] = pd.to_datetime(df['LocalDepTime'], format='%Y-%m-%d')
    df['LocalArrTime'] = pd.to_datetime(df['LocalArrTime'], format='%Y-%m-%d')

    df['depart_date'] = [d.date() for d in df['LocalDepTime']]
    df['arrival_date'] = [d.date() for d in df['LocalArrTime']]
    df['depart_time'] = [d.time() for d in df['LocalDepTime']]
    df['arrival_time'] = [d.time() for d in df['LocalArrTime']]

    df['from_airport_code'], df['to_airport_code'] = np.where(df['direction'] == 'ReturnLeg',
                                                              (df['to_airport_code'], df['from_airport_code']),
                                                              (df['from_airport_code'], df['to_airport_code'])
                                                              )
    df['from_airport_city'], df['to_airport_city'] = np.where(df['direction'] == 'ReturnLeg',
                                                              (df['to_airport_city'], df['from_airport_city']),
                                                              (df['from_airport_city'], df['to_airport_city'])
                                                              )

    df.drop('direction', 1, inplace=True)
    return df


def time_slice_dataframe(df, months=None):
    if months is not None:
        today = pd.to_datetime(date.today()).floor('D')
        end_date = pd.to_datetime(today + relativedelta(months=months)).floor('D')
        mask = (df['LocalDepTime'] > today) & (df['LocalDepTime'] <= end_date)
        df = df.loc[mask]
        return df

    else:
        return df


def save_to_csv(df, months):
    currentDate = datetime.datetime.now().strftime('%Y%m%d')
    if months is not None:
        df.to_csv(f"{full_pathname}/{currentDate}_{months}_months.csv", index=False, header=True)
    else:
        df.to_csv(f"{full_pathname}/{currentDate}_full.csv", index=False, header=True)
    return 0


def main_func(dep_airport_list_input, months=None):
    massive_flight_list = []
    flight_connections_dict = get_airport_codes()
    departure_airport_dict = get_airport_code_from_name()
    airport_code_country_dict = get_airport_code_country()
    for dep_airport_code in dep_airport_list_input:
        airport_code_list = get_all_flights(dep_airport_code, flight_connections_dict, departure_airport_dict)
        raw_df = get_json_data(dep_airport_code, airport_code_list, airport_code_country_dict, departure_airport_dict)
        massive_flight_list.append(raw_df)
    flat_list = [item for sublist in massive_flight_list for item in sublist]
    flat_list = [item for sublist in flat_list for item in sublist]
    df = pd.DataFrame(flat_list)
    transformed_df = transform_dataframe(df)
    time_sliced_df = time_slice_dataframe(transformed_df, months=months)
    save_to_csv(time_sliced_df, months)
    print('CSV successfully saved.')


# =============================================================================
# EXECUTE SCRAPER FROM EDITOR OR COMMAND LINE (command line default) - do not change
# =============================================================================
if run_from_editor:
    main_func(dep_airport_list_input, months)
else:
    parser = argparse.ArgumentParser(
        description='Scrape EasyJet flights based on departure airports and number of months'
    )
    parser.add_argument('-d', '--airports', nargs='+', help='list of departure airport codes', required=True,
                        default=[]
                        )
    parser.add_argument('-m', '--months', type=int, help='number of months to show flights for')
    args = parser.parse_args()
    main_func(args.airports, args.months)
