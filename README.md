# Web scraping showcase scripts
A collection of Python scripts for web scraping and data manipulation purposes. The techniques used are scraping the DOM tree, fetching site's hidden APIs and geospatial data.

## outages.py
The script was written for tracking power outages by a local power grid operator in Tennessee. The operator has a map that displays areas with power outage and number of customers affected. Available here (only available to US IPs): http://viewer.sces.net:88/. Since the operator provides limited info and functionality, the client asked to build a new tracking system that scrapes the outage data and adds more features. 

I also used my full-stack skills to build a Flask app featuring Postgres database where users can create accounts, receive outage notifications and configure their tracking addressses. It interact with Google Maps API to deliver mapping capabilities. Production app: https://avadaproperties.com/pigeon-forge-sevierville-gatlinburg-power-outage-map/

### Code functionality
The script scrapes JSON response with geospatial polygons of outages and the number of customers without power. It's scheduled to run concurrently via crontab on the server. When user provides their tracking address, the script checks if address lies in any of active outage polygons using Shapely. It reurns the data to the front-end where user gets an alert.

