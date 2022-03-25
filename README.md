# Web scraping showcase scripts
A collection of Python scripts for web scraping and data manipulation purposes. The techniques used are scraping the DOM tree, fetching site's hidden APIs and geospatial data.

## outages.py
The script was written for tracking power outages by a local power grid operator in Tennessee. The operator has a map that displays areas with power outage and number of customers affected. Available here (only available to US IPs): http://viewer.sces.net:88/. Since the operator provides limited info and functionality, the client asked to build a new tracking system that scrapes the outage data and adds more features. 

I also used my full-stack skills to build a Flask app featuring Postgres database where users can create accounts, receive outage notifications and configure their tracking addressses. It interact with Google Maps API to deliver mapping capabilities. Production app: https://avadaproperties.com/pigeon-forge-sevierville-gatlinburg-power-outage-map/

The script scrapes JSON response with geospatial polygons of outages and the number of customers without power. It's scheduled to run concurrently via crontab on the server. When user provides their tracking address, the script checks if address lies in any of active outage polygons using Shapely. It reurns the data to the front-end where user gets an alert.

Main libraries: Shapely, requests, pandas, Flask, SQLAlchemy

## immoscout24.py
The client wanted to scrape Germany's largest real estate site (https://www.immobilienscout24.de/) to analyse buy/rental prices for desired parameters. The script sends a POST request to the site which returns JSON file with listings info via their hidden API. It then loops through all available pages making POST requests. The JSON response varies often so, I built the logic to detect the changes and scrape the correct info. Script is run from the command line in a style: 'python immoscout24.py -city Berlin -price_from 3000000 -price_to 800000'. Final output is a CSV file. 

Main libraries: requests, BeautifulSoup, pandas

## easyjet_scraper.py
Similar approach to Immoscout before but for https://www.easyjet.com/en/. The script scrapes the table with all possible flying destinations and then sends POST requests to get back JSON data with flight details. Final output is a CSV file.

Main libraries: requests, BeautifulSoup, pandas

## NYSA_scraper.py
The client wanted to scrape a large number of historical documents that were digitised from NY State Archives (https://iarchives.nysed.gov/xtf/view?docId=ead/findingaids/A1880.xml. The documents have convoluted DOM tree that has lots of conditionals. Some categories appear in combination with others and so on. This meant I had to extensively test and update the content logic when scraping. Selenium is used due to dynamic content loading and specific requirements from the client.

Main libraries: pandas, Selenium, BeautifulSoup

