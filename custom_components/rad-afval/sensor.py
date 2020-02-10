#!/usr/bin/env python3
"""
Sensor component for RAD Hoekschewaard Afval Kalender
Author: John van der Wulp

Version: 0.0.1  20200210 - Initial Release
"""

import voluptuous as vol
from datetime import datetime
import urllib.error
from .const import (
    MIN_TIME_BETWEEN_UPDATES,
    _LOGGER,
    CONF_POSTALCODE,
    CONF_STREET_NUMBER,
    CONF_DATE_FORMAT,
    SENSOR_PREFIX,
    ATTR_LAST_UPDATE,
    ATTR_HIDDEN,
    ATTR_NEXT_PICKUP_IN_DAYS,
    SENSOR_TYPES,
)

from .radhw import RadhwAfval
from homeassistant.components.sensor import PLATFORM_SCHEMA
import homeassistant.helpers.config_validation as cv
from homeassistant.const import CONF_RESOURCES
from homeassistant.util import Throttle
from homeassistant.helpers.entity import Entity

REQUIREMENTS = ["BeautifulSoup4==4.7.0"]

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_RESOURCES, default=[]): vol.All(cv.ensure_list, [vol.In(SENSOR_TYPES)]),
        vol.Required(CONF_POSTALCODE, default="3262CD"): cv.string,
        vol.Required(CONF_STREET_NUMBER, default="5"): cv.string,
        vol.Optional(CONF_DATE_FORMAT, default="%d-%m-%Y"): cv.string,
    }
)
DUTCH_TRANSLATION_DAYS = {
    'Monday': 'Maandag',
    'Tuesday': 'Dinsdag',
    'Wednesday': 'Woensdag',
    'Thursday': 'Donderdag',
    'Friday': 'Vrijdag',
    'Saturday': 'Zaterdag',
    'Sunday': 'Zondag',
    'Mon': 'Ma',
    'Tue': 'Di',
    'Wed': 'Wo',
    'Thu': 'Do',
    'Fri': 'Vr',
    'Sat': 'Za',
    'Sun': 'Zo'
}
DUTCH_TRANSLATION_MONTHS ={
    'Mar': 'Mrt',
    'May': 'Mei',
    'Oct': 'Okt',
    'January': 'Januari',
    'February': 'Februari',
    'March': 'Maart',
    'June': 'Juni',
    'July': 'Juli',
    'August': 'Augustus',
    'October': 'Oktober'
}

def setup_platform(hass, config, add_entities, discovery_info=None):
    _LOGGER.debug("Setup rad-afval sensor")

    postalcode = config.get(CONF_POSTALCODE)
    street_number = config.get(CONF_STREET_NUMBER)
    date_format = config.get(CONF_DATE_FORMAT)

    try:
        data = RadhwAfvalData(postalcode, street_number)
    except urllib.error.HTTPError as error:
        _LOGGER.error(error.reason)
        return False

    entities = []

    for resource in config[CONF_RESOURCES]:
        sensor_type = resource.lower()
        if sensor_type not in SENSOR_TYPES:
            SENSOR_TYPES[sensor_type] = [sensor_type.title(), "", "mdi:recycle"]

        entities.append(RadhwAfvalSensor(data, sensor_type, date_format))
    add_entities(entities)


class RadhwAfvalData(object):
    def __init__(self, postalcode, street_number):
        self.data = None
        self.postalcode = postalcode
        self.street_number = street_number

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        _LOGGER.debug("Updating RadhwAfvalSensors")
        self.data = RadhwAfval().get_data(self.postalcode, self.street_number)

class RadhwAfvalSensor(Entity):
    def __init__(self, data, sensor_type, date_format):
        self.data = data
        self.date_format = date_format
        self.type = sensor_type
        self._name = SENSOR_TYPES[sensor_type][0]
        self._entity_picture = None
        self._hidden = False
        self._next_pickup_in_days = None
        self._state = None
        self._last_update = None

    @property
    def name(self):
        return SENSOR_PREFIX + self._name
    
    @property
    def entity_picture(self):
        return self._entity_picture

    @property
    def state(self):
        return self._state

    @property
    def device_state_attributes(self):
        return {ATTR_LAST_UPDATE: self._last_update, ATTR_HIDDEN: self._hidden, ATTR_NEXT_PICKUP_IN_DAYS: self._next_pickup_in_days}

    def update(self):
        self._entity_picture = SENSOR_TYPES[self.type][1]
        self.data.update()
        waste_data = self.data.data

        try:
            if waste_data:
                if self.type in waste_data:
                    today = datetime.today()

                    collection_date = datetime.strptime(
                        waste_data[self.type], "%Y-%m-%d"
                    ).date()

                    if collection_date:
                        # Set the values of the sensor
                        delta = collection_date - today.date()
                        self._last_update = today.strftime("%d-%m-%Y %H:%M")
                        self._state = collection_date.strftime(self.date_format)
                        for EN_day, NL_day in DUTCH_TRANSLATION_DAYS.items():
                            self._state = self._state.replace(EN_day, NL_day)
                        for EN_month, NL_month in DUTCH_TRANSLATION_MONTHS.items():
                            self._state = self._state.replace(EN_month, NL_month)
                        self._next_pickup_in_days = delta.days
                    else:
                        raise ValueError()
                else:
                    raise ValueError()
        except ValueError:
            self._state = None
            self._hidden = True
