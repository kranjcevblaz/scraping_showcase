from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import pandas as pd
import urllib.parse
import re
from time import sleep
import os
import sys

# =============================================================================
# LIST OF SCRAPED FINDING AIDS URLs SO FAR
# =============================================================================
'''
    url = "https://iarchives.nysed.gov/xtf/view?docId=ead/findingaids/A1880.xml"
    url = "https://iarchives.nysed.gov/xtf/view?docId=ead/findingaids/A1882.xml"
    url = 'https://iarchives.nysed.gov/xtf/view?docId=ead/findingaids/A0270.xml'
'''

# =============================================================================
# HEADLESS BROWSER SETTINGS
# =============================================================================
# set to False to get browser UI (runs a bit slower but you see it running in separate browser window)
headless_chrome = False

pathname = os.path.dirname(sys.argv[0])
full_pathname = os.path.abspath(pathname)
CHROMEDRIVER_PATH = f"{full_pathname}/chromedriver"
ROOT_URL = 'https://digitalcollections.archives.nysed.gov/'

if headless_chrome:
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(CHROMEDRIVER_PATH, options=chrome_options)
else:
    driver = webdriver.Chrome(CHROMEDRIVER_PATH)
    
# =============================================================================
#  CORE SCRAPER FUNCTION 
# =============================================================================
def run_finding_aid_scraper(url):
    # function clicks on every item in finding aid list, scrapes details and translation page, returns back to
    # finding aid list and loops through all items
    finding_aids_list = []
    driver.get(url)
    
    source = driver.page_source
    sel_soup = BeautifulSoup(source, 'html.parser')
    finding_aids = sel_soup.find_all('table', {'id': 'table'})
    
    for fnd_aid in finding_aids:
        try:
            td_elements = fnd_aid.find_all('td')
            date = td_elements[0].text
            short_desc = td_elements[1].contents[0]
            short_desc = re.sub('\s+', ' ', short_desc)
            long_desc = td_elements[1].find('p').text
            long_desc = re.sub('\s+', ' ', long_desc)
            box = td_elements[2].text
            volume = td_elements[3].text
            item = td_elements[4].text
            
            inner_text_aid = []
            
            inner_text_aid.append(date)
            inner_text_aid.append(short_desc)
            inner_text_aid.append(long_desc)
            inner_text_aid.append(box)
            inner_text_aid.append(volume)
            inner_text_aid.append(item)
            
            link_volume = fnd_aid.find('a')['href']
            inner_text_aid.append(link_volume)
    # =============================================================================
    #       2nd PAGE - details for each finding aid (e.g. https://digitalcollections.archives.nysed.gov/index.php/Detail/objects/51334)
    # =============================================================================
            driver.get(link_volume)
            source = driver.page_source
            sel_soup = BeautifulSoup(source, 'html.parser')
            detail_title = sel_soup.find('div', {'class': 'col-sm-12'})
            detail_title_element = detail_title.find('h2').text
            inner_text_aid.append(detail_title_element)
            
            details_section = sel_soup.find('div', {'class':'col-sm-5 rightCol'})
            details_section_first_unit = details_section.find('div', {'class': 'unit'})
            inner_text_aid.append(details_section_first_unit.text)
            
            translation_link = details_section.find_all('div', {'class': 'unit'})[1]
            if translation_link.find('a'):
                trans_link = translation_link.find('a')['href']
                inner_text_aid.append(trans_link)
            else:
                inner_text_aid.append('None')
            
            # check if details page contains Contributor element, if not, add "None" entry
            if details_section.find_all(text='Language') or details_section.find_all(text='Contributor'):
                details_section_units = details_section.find_all('div', {'class': 'unit'})[1:7]
                if not details_section.find('a', {'class': 'btn btn-default'}):
                    details_section_units = details_section.find_all('div', {'class': 'unit'})[1:6]
                    
            else:
                details_section_units = details_section.find_all('div', {'class': 'unit'})[1:6]
                if not details_section.find('a', {'class': 'btn btn-default'}):
                    details_section_units = details_section.find_all('div', {'class': 'unit'})[1:5]
                
            for unit in details_section_units:
                for br in unit.find_all('br'):
                    next_string = br.nextSibling
                    inner_text_aid.append(next_string)
            
            special_project_check = details_section.find_all(text='Special Project')
            contributor_check = details_section.find_all(text='Contributor')
            language_check = details_section.find_all(text='Language')
            
            if not details_section.find_all(text='Rights'):
                if details_section.find_all(text='Special Project') and details_section.find_all(text='Geographic Locations'):
                    more_from_series_section = details_section.find_all('div', {'class': 'unit'})[-2]
                    special_project = details_section.find_all('div', {'class': 'unit'})[-3]
                
                if details_section.find_all(text='Special Project') and not details_section.find_all(text='Geographic Locations'):
                    more_from_series_section = details_section.find_all('div', {'class': 'unit'})[-1]
                    special_project = details_section.find_all('div', {'class': 'unit'})[-2]
            
            else:
                if details_section.find_all(text='Geographic Locations') and details_section.find_all(text='Special Project'):
                    more_from_series_section = details_section.find_all('div', {'class': 'unit'})[-2]
                    rights_section = details_section.find_all('div', {'class': 'unit'})[-4]
                    special_project = details_section.find_all('div', {'class': 'unit'})[-3]
                elif details_section.find_all(text='Geographic Locations') and not details_section.find_all(text='Special Project'):
                    more_from_series_section = details_section.find_all('div', {'class': 'unit'})[-2]
                    rights_section = details_section.find_all('div', {'class': 'unit'})[-3]
                elif details_section.find_all(text='Special Project') and not details_section.find_all(text='Geographic Locations'):
                    more_from_series_section = details_section.find_all('div', {'class': 'unit'})[-1]
                    rights_section = details_section.find_all('div', {'class': 'unit'})[-3]
                    special_project = details_section.find_all('div', {'class': 'unit'})[-2]
                else:
                    rights_section = details_section.find_all('div', {'class': 'unit'})[-2]
                    more_from_series_section = details_section.find_all('div', {'class': 'unit'})[-1]
            
                rights_section_text = rights_section.find('br').nextSibling
            
                rights_section_link_text = rights_section.find('a').text
                rights_section_link = rights_section.find('a')['href']
                rights_section_link = urllib.parse.urljoin(ROOT_URL, rights_section_link)
                
                rights_section_body = rights_section_text + rights_section_link_text
                
                inner_text_aid.append(rights_section_body)
                inner_text_aid.append(rights_section_link)
            
            if special_project_check:
                special_project_text = special_project.find('br').nextSibling
                inner_text_aid.append(special_project_text)
            else:
                inner_text_aid.append('None')

            if not contributor_check:
                inner_text_aid.insert(13, 'None')

            if not language_check:
                inner_text_aid.insert(14, 'None')

            geo_locations_section = details_section.find_all('div', {'class': 'unit'})[-1]
            more_from_series_text = more_from_series_section.find('a').text
            more_from_series_link = more_from_series_section.find('a')['href']
            
            inner_text_aid.append(more_from_series_text)
            inner_text_aid.append(urllib.parse.urljoin(ROOT_URL, more_from_series_link))
            
            geo_location_text_list = []
            geo_location_link_list = []
            if details_section.find_all(text='Geographic Locations'):
                for geo_loc in geo_locations_section.find_all('a'):
                    geo_location_text_list.append(geo_loc.text)
                    geo_complete_url = urllib.parse.urljoin(ROOT_URL, geo_loc['href'])
                    geo_location_link_list.append(geo_complete_url)
                    
                geo_location_text_list = ', '.join(geo_location_text_list)
                geo_location_link_list = ', '.join(geo_location_link_list)
                
                inner_text_aid.append(geo_location_text_list)
                inner_text_aid.append(geo_location_link_list)
            else:
                inner_text_aid.append('None')
                inner_text_aid.append('None')
        
            # image carousel - script click next image button a few times to record all image links
            image_carousel = sel_soup.find('div', {'id': 'repViewerCarousel'})
        
            image_src_list = []
            
            try:
                if image_carousel:
                    carousel_length = sel_soup.find('div', {'id': 'detailRepresentationThumbnails'})
                    carousel_length = len(carousel_length.select('div[id*="detailRepresentationThumbnail"]'))
                    next_icon = driver.find_element_by_id('detailRepNavNext')
                    carousel_img = sel_soup.select('img[id*="caMediaOverlayTileViewer"]')
                    
                    i = 1
                    while i < carousel_length+1:
                        next_icon.click()             
                        i += 1
                        
                    sleep(2)
                    source = driver.page_source
                    sel_soup = BeautifulSoup(source, 'html.parser')
                    carousel_img = sel_soup.select('img[id*="caMediaOverlayTileViewer"]')
                    for img in carousel_img:
                        image_src_list.append(img['src'])
                        
                    image_src_list = ", ".join(image_src_list)
                    inner_text_aid.append(image_src_list)
                        
                else: 
                    image_element = sel_soup.find('div', {'class':'repViewerCont'})
                    image_src = image_element.find('img')['src']
                    complete_url = urllib.parse.urljoin(ROOT_URL, image_src)
                    inner_text_aid.append(complete_url)
            except:
                inner_text_aid.append('None')
            
            # download full-size image link
            download_image = sel_soup.find('div', {'id': 'detailDD'})
            download_image_src = download_image.find_all('a')[1]['href']
            inner_text_aid.append(urllib.parse.urljoin(ROOT_URL, download_image_src))
            
    # =============================================================================
    #       3rd PAGE - translation page (e.g. https://iarchives.nysed.gov/xtf/view?docId=tei/A1882/NYSA_A1882-78_VHHpt1_0004.xml)
    # =============================================================================
            try:
                details_section_translation_button = details_section.find('a', {'class': 'btn btn-default'})['href']
                driver.get(details_section_translation_button)
                source = driver.page_source
                sel_soup = BeautifulSoup(source, 'html.parser')
                translation_page = sel_soup.find('div', {'id': 'mainContent'})
            
                # get translation title
                translation_title = translation_page.find_all('h2')[1].text
                translation_title = re.sub('\s+', ' ', translation_title)
                inner_text_aid.append(translation_title)
                
                translation_metadata = translation_page.find_all('div', {'id': 'labelinfo'})
                
                for metadata in translation_metadata:
                    inner_text_aid.append(metadata.find('a').text)
                    inner_text_aid.append(metadata.find('a')['href'])
                
                # main body translation
                translation_text = translation_page.find('div', {'id': 'transcriptlayout'})
                
                translation_p_list = []
                for p in translation_text(['p']):
                    p_str = re.sub('\s+', ' ', p.text)
                    p_str = p_str.replace('[ ]', '[      ]')
                    translation_p_list.append(p_str)
                translation_p_list = "\n\n".join(translation_p_list)
        
                    
                translation_signatures_list = []    
                for div in translation_text.find_all('div', attrs={'class': 'row'}):
                    div = re.sub('\s+', ' ', div.text)
                    translation_signatures_list.append(div)
                translation_signatures_list = "\n".join(translation_signatures_list)
                
                translation_body = '\n'.join([translation_p_list, translation_signatures_list])
                
                # references        
                translation_references = translation_page.find('div', {'id': 'notesection'})
                
                translation_notes_list = []
                translation_superscripts_list = []
                if translation_references.find_all('div', attrs={'class': 'note'}):
                    translation_notes_list_joined = "\n".join(translation_notes_list)
                    translation_body = '\n\n'.join([translation_p_list, translation_signatures_list, translation_notes_list_joined])
                    inner_text_aid.append(translation_body)
                    
                    translation_superscript_1 = translation_text.find_all('sup', {'class': 'ref'})
                    
                    for superscript in translation_superscript_1:
                        sup_text = superscript.find('a').text
                        sup_text = re.sub('\s+', ' ', sup_text)
                        translation_superscripts_list.append(sup_text)
                        
                    translation_superscripts_list = ['[' + superscript + ']' + ': ' for superscript in translation_superscripts_list]
                        
                    translation_notes = translation_references.find_all('div', attrs={'class': 'note'})
                    
                    if translation_notes:
                        for div in translation_notes:
                            div = re.sub('\s+', ' ', div.text)
                            translation_notes_list.append(div)
                            
                        translation_superscripts_list_paired = [list(pair) for pair in zip(translation_superscripts_list, translation_notes_list)]
                        translation_superscripts_list_paired = list(map(''.join, translation_superscripts_list_paired))
                        translation_notes_list = '\n'.join(translation_superscripts_list_paired)
                        
                        inner_text_aid.append(translation_notes_list)
                    else:
                        inner_text_aid.append(translation_superscripts_list)
                    
                else:
                    translation_body = '\n\n'.join([translation_p_list, translation_signatures_list])
                    inner_text_aid.append(translation_body)
                    if not translation_text.find_all('sup', {'class': 'ref'}):
                        inner_text_aid.append('None')
                
                # the last paragraph in Translation is located in References div element
                translation_references_text = translation_references.find('h4', {'class': 'normal'})
                translation_references_text = translation_references_text.nextSibling
                translation_references_link_text = translation_references.find('a').text
                translation_references_link = translation_references.find('a')['href']
                
                
                translation_references_combined = translation_references_text + translation_references_link_text
                inner_text_aid.append(translation_references_combined)
                inner_text_aid.append(translation_references_link)
                
            except:
                inner_text_aid.append('None')
                inner_text_aid.append('None')
            
            finding_aids_list.append(inner_text_aid)
         
            driver.back()
            driver.back()
            # the end of loop for each item in finding aid (navigates back twice to get to list of all items)
        except:
            continue
    # after all items on initial finding aid page have been scraped, driver closes the browser session
    driver.close()
    
    return finding_aids_list, language_check, contributor_check


def transform_df(finding_aids_list, language_check, contributor_check):
    # function wraps list of lists into dataframe object, assigns column names and language/contributor logic
    
    df_finding_aid = pd.DataFrame(finding_aids_list)
    # logic to name columns based on varying cagories (e.g. contributor, special, project, geo locations)
    df_finding_aid.columns = ['Dates', 'Short Description', 'Long Description', 'Box', 'Volume', 'Item', 'Item Link', 'Title2', 'Long2', 'Translation Link', 'Identifier', 'Date2', 'Language_Contributor', 'Contributor', 'Source', 'Rights2', 'Rights', 'Rights Link', 'Special Project', 'More From Series', 'More From Series Link', 'Geographic Location', 'Geographic Location Link', 'Small Image', 'Full Image', 'Translation Title', 'Series', 'Series Link', 'Scanned Doc', 'Scanned Doc Link', 'Translation', 'Translation Superscripts', 'Translation Reference', 'Translation Reference Link']
    df_finding_aid.drop('Rights2', axis=1, inplace=True)
    
    return df_finding_aid


def save_to_csv(df, url):
    finding_aid_code = url.rsplit('/', 1)[1].split('.', 1)[0]
    df.to_csv(f"{full_pathname}/finding_aid_{finding_aid_code}.csv", index=False, header=True)
    return 0


def scrape_finding_aid(url):
    finding_aids_list, language_check, contributor_check = run_finding_aid_scraper(url)
    transformed_df = transform_df(finding_aids_list, language_check, contributor_check)
    save_to_csv(transformed_df, url)


scrape_finding_aid(sys.argv[1])
