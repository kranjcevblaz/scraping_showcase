import requests
import pandas as pd
import argparse
import datetime
import sys
import os

listing_id_list = []
price_list = []
photo_link = []
bedrooms_list = []
district_list = []
surface_list = []
title_list = []
url_list = []
postalcode_list = []
latitude_list = []
longitude_list = []

run_from_editor = False
pathname = os.path.dirname(sys.argv[0])
full_pathname = os.path.abspath(pathname)


def request_api(city, district, price_from, price_to, surface_from, surface_to, bedrooms, pg):
    # default district is Berlin if no data provided
    city = city.lower()
    district = district.lower()
    headers = {
        'authority': 'www.immobilienscout24.de',
        'content-length': '0',
        'accept': 'application/json; charset=utf-8',
        'x-requested-with': 'XMLHttpRequest',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/96.0.4664.110 Safari/537.36',
        'content-type': 'application/json; charset=utf-8',
        'sec-gpc': '1',
        'origin': 'https://www.immobilienscout24.de',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-mode': 'cors',
        'sec-fetch-dest': 'empty',
        'referer': f'https://www.immobilienscout24.de/Suche/de/{city}/{district}/wohnung-kaufen?numberofrooms=1-{bedrooms}.0&price={price_from}.0-{price_to}.0&livingspace={surface_from}.0-{surface_to}.0',
        'accept-language': 'en-US,en;q=0.9',
    }

    params = (
        ('numberofrooms', f'1-{bedrooms}.0'),
        ('price', f'{price_from}.0-{price_to}.0'),
        ('livingspace', f'{surface_from}.0-{surface_to}.0'),
        ('pagenumber', f'{pg}'),
    )


    response = requests.post(f'https://www.immobilienscout24.de/Suche/de/{city}/{district}/wohnung-kaufen',
                             headers=headers, params=params
                             )
    json_data = response.json()
    print(f'Page: {pg}')
    return json_data


def number_of_listings(json_data):
    n_pages = json_data['searchResponseModel']['resultlist.resultlist']['paging']['numberOfPages']
    page_list = list(range(2, n_pages + 1))
    return page_list


def extract_json(json_data):
    resultList = json_data['searchResponseModel']['resultlist.resultlist']['resultlistEntries'][0]['resultlistEntry']
    for card in resultList:
        listing_id_list.append(card['@id'])
        card_attributes = card['attributes'][0]['attribute']

        if not any(d['label'] == 'Wohnfläche' for d in card_attributes):
            surface_list.append('None')
        if not any(d['label'] == 'Kaufpreis' for d in card_attributes):
            price_list.append('None')
        if not any(d['label'] == 'Zimmer' for d in card_attributes):
            bedrooms_list.append('None')


        for attr in card_attributes:
            if attr['label'] == 'Wohnfläche':
                surface_list.append(attr['value'])
            elif attr['label'] == 'Kaufpreis':
                price_list.append(attr['value'])
            elif attr['label'] == 'Zimmer':
                bedrooms_list.append(attr['value'])

        district_list.append(card['resultlist.realEstate']['address']['quarter'])
        postalcode_list.append(card['resultlist.realEstate']['address']['postcode'])
        title_list.append(card['resultlist.realEstate']['title'])

        def check_for_coordinates(card):
            if 'wgs84Coordinate' in card['resultlist.realEstate']['address']:
                latitude_list.append(card['resultlist.realEstate']['address']['wgs84Coordinate']['latitude'])
                longitude_list.append(card['resultlist.realEstate']['address']['wgs84Coordinate']['longitude'])
            else:
                latitude_list.append('None')
                longitude_list.append('None')

        check_for_coordinates(card)

        if 'project' in card:
            url_list.append(card['project']['link'])
            photo_uri = card['project']['picture']['uri']
            if photo_uri is not None:
                photo_link.append(photo_uri)
            else:
                photo_link.append('None')
        else:
            url_list.append('None')
            if 'galleryAttachments' in card['resultlist.realEstate']:
                listing_attachment = card['resultlist.realEstate']['galleryAttachments']['attachment']
                if isinstance(listing_attachment, dict):
                    listing_attachment_href = listing_attachment['urls'][0]['url']['@href']
                    if listing_attachment_href is not None:
                        photo_link.append(listing_attachment_href)
                    else:
                        photo_link.append('None')
                elif isinstance(listing_attachment, list):
                    listing_attachment_href = listing_attachment[0]['urls'][0]['url']['@href']
                    if listing_attachment_href is not None:
                        photo_link.append(listing_attachment_href)
                    else:
                        photo_link.append('None')
                else:
                    photo_link.append('None')
            else:
                photo_link.append('None')

        if 'similarObjects' in card:
            similar_objects = card['similarObjects']

            if isinstance(similar_objects[0]['similarObject'], list):
                for i in similar_objects[0]['similarObject']:
                    listing_id_list.append(i['@id'])
                    price_list.append(i['attributes'][0]['attribute'][0]['value'])
                    surface_list.append(i['attributes'][0]['attribute'][1]['value'])
                    bedrooms_list.append(i['attributes'][0]['attribute'][2]['value'])
                    url_list.append(card['project']['link'])
                    photo_link.append(card['project']['picture']['uri'])
                    district_list.append(card['resultlist.realEstate']['address']['quarter'])
                    postalcode_list.append(card['resultlist.realEstate']['address']['postcode'])
                    title_list.append(card['resultlist.realEstate']['title'])
                    check_for_coordinates(card)

            elif isinstance(similar_objects[0]['similarObject'], dict):
                listing_id_list.append(similar_objects[0]['similarObject']['@id'])
                price_list.append(similar_objects[0]['similarObject']['attributes'][0]['attribute'][0]['value'])
                surface_list.append(similar_objects[0]['similarObject']['attributes'][0]['attribute'][1]['value'])
                bedrooms_list.append(similar_objects[0]['similarObject']['attributes'][0]['attribute'][2]['value'])
                url_list.append(card['project']['link'])
                photo_link.append(card['project']['picture']['uri'])
                district_list.append(card['resultlist.realEstate']['address']['quarter'])
                postalcode_list.append(card['resultlist.realEstate']['address']['postcode'])
                title_list.append(card['resultlist.realEstate']['title'])
                check_for_coordinates(card)


def transform_df(master_list, city, district, price_from, price_to, surface_from, surface_to, bedrooms):
    city = city.lower()
    district = district.lower()
    df = pd.DataFrame(master_list).transpose()
    df.columns = ['Title', 'ID', 'Price', 'Photo_Link', 'Bedrooms', 'Location', 'QM', 'Postal_Code', 'Link', 'Latitude',
                  'Longitude']
    df['Price'] = df['Price'].str.replace(' €', '')
    df['Price'] = df['Price'].str.replace('.', '')
    df['Bedrooms'] = df['Bedrooms'].astype(str).str.replace(',', '.')
    df['QM'] = df['QM'].str.replace(',', '.')
    df['QM'] = df['QM'].str.replace(' m²', '')
    numeric_cols = ['Price', 'QM', 'Bedrooms']
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')
    df.fillna('None', inplace=True)

    listing_link_list = []
    for url, listing_id in df[['Link', 'ID']].itertuples(index=False):
        if url == 'None':
            generate_url = f'https://www.immobilienscout24.de/Suche/controller/exposeNavigation/goToExpose.go?exposeId={listing_id}&searchUrl=%2FSuche%2Fde%2F{city}%2F{district}%2Fwohnung-kaufen%3Fnumberofrooms%3D1.0-{bedrooms}.0%26price%3D{price_from}.0-{price_to}.0%26livingspace%3D{surface_from}.0-{surface_to}.0%26pagenumber%3D2&referrer=RESULT_LIST_LISTING&searchType=district'
            listing_link_list.append(generate_url)
        else:
            listing_link_list.append(url)

    df['Link'] = listing_link_list

    # reformat certain photo links that have raw format
    photo_link_list = []
    for photo_url_link in df['Photo_Link']:
        if 'legacy_thumbnail' in photo_url_link:
            link = photo_url_link.split('/listings/')[1]
            link = link.split('/ORIG/')[0]
            photo_format = link.split('.')[1]
            new_link = f'https://pictures.immobilienscout24.de/listings/{link}/ORIG/resize/1106x830%3E/format/{photo_format}/quality/50 '
            photo_link_list.append(new_link)
        else:
            print(photo_url_link)
            photo_link_list.append(photo_url_link)

    df['Photo_Link'] = photo_link_list

    # reorder columns
    df_cols = ['Title', 'ID', 'Price', 'QM', 'Bedrooms', 'Location', 'Postal_Code', 'Link', 'Photo_Link', 'Latitude',
               'Longitude']
    df = df[df_cols]
    return df


def immoscout_scraper(city, district, price_from, price_to, surface_from, surface_to, bedrooms):
    json_data = request_api(city, district, price_from, price_to, surface_from, surface_to, bedrooms, 1)
    page_list = number_of_listings(json_data)

    extract_json(json_data)

    for pg in page_list:
        json_data = request_api(city, district, price_from, price_to, surface_from, surface_to, bedrooms, pg)
        extract_json(json_data)

    master_list = [title_list, listing_id_list, price_list, photo_link, bedrooms_list, district_list, surface_list,
                   postalcode_list, url_list, latitude_list, longitude_list]
    return master_list


def main_func(city, district, price_from, price_to, surface_from, surface_to, bedrooms):
    for d in district:
        master_list = immoscout_scraper(city, d, price_from, price_to, surface_from, surface_to, bedrooms)
        df = transform_df(master_list, city, d, price_from, price_to, surface_from, surface_to, bedrooms)
        save_to_csv(df, city, d, price_from, price_to)


def save_to_csv(df, city, district, price_from, price_to):
    currentDate = datetime.datetime.now().strftime('%Y%m%d')
    # save CSV file to same location as the script
    # for saving to another folder - edit {full_pathname} variable or add "/desired_folder/ after the var
    filename = f'{full_pathname}/{city}_{district}_{currentDate}_{price_from}_{price_to}_immoscout24_listings.csv'
    df.to_csv(filename, index=False, header=True)
    print(f'Total number of listings in CSV: {len(df)}')
    print(f'CSV file saved saved: {filename}')


if run_from_editor:
    pass
    # example function with arguments
    # main_func('Berlin', ['Berlin'], 0, 800000, 1, 999, 9)
else:
    parser = argparse.ArgumentParser(
        description='Scrape ImmobilienScout24.de for listings based on city and districts'
    )
    parser.add_argument('-c', '--city', help='City', required=True,
                        default='Berlin'
                        )
    parser.add_argument('-d', '--districts', nargs='+', type=str, help='District list', required=False,
                        default=['Berlin']
                        )
    parser.add_argument('-pf', '--price_from', type=int, help='Price from', required=False,
                        default=0
                        )
    parser.add_argument('-pt', '--price_to', type=int, help='Price to', required=False,
                        default=9999999
                        )
    parser.add_argument('-qf', '--surface_from', type=int, help='Square meter from', required=False,
                        default=1
                        )
    parser.add_argument('-qt', '--surface_to', type=int, help='Square meter to', required=False,
                        default=999
                        )
    parser.add_argument('-bd', '--bedrooms_max', type=int, help='Maximum bedroom number', required=False,
                        default=9
                        )

    args = parser.parse_args()
    main_func(args.city, args.districts, args.price_from, args.price_to, args.surface_from, args.surface_to,
              args.bedrooms_max)
