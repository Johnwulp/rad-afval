from ..const.const import (
    _LOGGER,
)
from bs4 import BeautifulSoup
from datetime import datetime
import urllib.request
import urllib.error

class RadhwAfval(object):
    def get_data(self, postalcode, street_number):
        _LOGGER.debug("Updating Waste collection dates")

        try:
            url = "https://www.radhw.nl/inwoners/ophaalschema?p={}+{}&h={}".format(postalcode[:4], postalcode[-2:], street_number)
            _LOGGER.debug("URL: " + url)
            req = urllib.request.Request(url=url)
            f = urllib.request.urlopen(req)
            html = f.read().decode("utf-8")
            soup = BeautifulSoup(html, "html.parser")
            waste_dict = {}
            for item in soup.findAll('ul',{'class':'downloads'}):
                sub_items = item.findAll('li')
                for sub_item in sub_items:
                    t = sub_item()[0].get('class')[1]
                    t = t.split("-")
                    d = sub_item()[1].text.split(" ")[1:4]
                    i = ["januari", "februari", "maart", "april", "mei", "juni", "juli", "augustus", "september", "oktober", "november", "december"].index(d[1])
                    waste_dict[t[2]] = d[2] + "-" + str(i+1) + "-" + d[0]
            return waste_dict
            
        except urllib.error.URLError as exc:
            _LOGGER.error("Error occurred while fetching data: %r", exc.reason)
            return False
