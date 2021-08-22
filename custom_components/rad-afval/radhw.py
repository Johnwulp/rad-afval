from .const import (
    _LOGGER,
)
from urllib import request, parse
import json
from datetime import datetime, timedelta, date

class RadhwAfval(object):
    def get_data(self, postalcode, street_number, companycode):
        _LOGGER.debug("Updating Waste collection dates")

        try:
            url = 'https://wasteprod2api.ximmio.com/api/FetchAdress'
            data = {"postCode": str(postalcode),"houseNumber": str(street_number),"companyCode": str(companycode)}
            _LOGGER.debug("FetchAdress data: " + str(data))
            data = json.dumps(data)
            data = data.encode()
            headers = {'content-type': 'application/json;charset=UTF-8'}
            req = request.Request(url, data=data, headers=headers)
            response = request.urlopen(req)
            data = json.load(response)
            uniqueid = data['dataList'][0]['UniqueId']
            _LOGGER.debug("uniqueid: " + str(uniqueid))
            
            startdate = date.today()
            enddate = date.today() + timedelta(days=31)

            url = 'https://wasteprod2api.ximmio.com/api/GetCalendar'
            data = {"companyCode": str(companycode),"startDate": str(startdate),"endDate": str(enddate),"community":"Hoeksche Waard","uniqueAddressID": str(uniqueid)}
            _LOGGER.debug("GetCalendar data: " + str(data))
            data = json.dumps(data)
            data = data.encode()
            req = request.Request(url, data=data, headers=headers)
            response = request.urlopen(req)
            data = json.load(response)
            _LOGGER.debug("Result data: " + str(data))
            data = (data['dataList'])

            SENSORNAMES = {
                'GREEN': 'gft',
                'GREY': 'rest',
                'PAPER': 'papier',
                'PACKAGES': 'pmd'
            }

            waste_dict = {}
            for item in data:
                pickupdate = item['pickupDates'][0]
                pickuptype = item['_pickupTypeText']
                for siteType, hassType in SENSORNAMES.items():
                    pickuptype = pickuptype.replace(siteType, hassType)
                collection_date = datetime.strptime(pickupdate, "%Y-%m-%dT%H:%M:%S").date()
                waste_dict[pickuptype] = collection_date.strftime("%Y-%m-%d")
            return waste_dict
            
        except urllib.error.URLError as exc:
            _LOGGER.error("Error occurred while fetching data: %r", exc.reason)
            return False