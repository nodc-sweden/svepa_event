import datetime
import pathlib
import pandas as pd
import logging


logger = logging.getLogger(__file__)

FILTERED_EVENTS = ['HOSE', 'PHYTOPLANKTON', 'SECCHI', 'ZOOPLANKTON', 'BOTTLE', 'FERRYBOX', 'MVP', 'CTD', 'ADCP', 'WEATHER']


class Event:
    def __init__(self, all_events: dict, event_info: pd.Series):
        self._all_events = all_events
        self._parent = None
        self._children = []

        self._info = {}
        for key in event_info.keys():
            value = str(event_info[key])
            if key in ['StartTime', 'StopTime'] and value:
                value = datetime.datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
            self._info[key] = value

    def __str__(self):
        return '\n'.join([
            '='*100,
            f'Platform:      {self.full_name}',
            f'EventID:       {self.event_id}',
            f'ParentEventID: {self.parent_event_id}',
            f'StartTime:     {self._info["StartTime"]}',
            f'StopTime:      {self._info["StopTime"]}',
            '-' * 100,
        ])

    def __repr__(self):
        return f'Event: {self.full_name} ({self.event_id})'

    def __eq__(self, other):
        if self.event_id == other.event_id:
            return True
        return False

    def _add_child(self, event):
        self._children.append(event)

    def add_parent_and_children(self):
        for event in self._all_events.values():
            if event == self:
                continue
            if self.parent_event_id == event.event_id:
                self._parent = event
                event._add_child(self)
                break

    def check_name_and_time(self, name: str, time: datetime.datetime):
        return self.check_name(name) and self.check_time(time)

    def check_time(self, time: datetime.datetime):
        if not (self.start_time and self.start_time):
            return False
        try:
            if self.start_time <= time <= self.stop_time:
                return True
        except TypeError as e:
            logger.warning(f'Error when checking {time=}: {e}')
        return False

    def check_name(self, name: str):
        if self.name == name:
            return True
        return False

    @property
    def event_type(self):
        return self._info['EventType']

    @property
    def id(self):
        return self.full_name.split('.')[-1]

    @property
    def start_lat(self):
        value = self._info['declat start'].replace(',', '.')
        if value == '':
            return None
        return float(value)

    @property
    def start_lon(self):
        value = self._info['declong start'].replace(',', '.')
        if value == '':
            return None
        return float(value)

    @property
    def stop_lat(self):
        value = self._info['declat stop'].replace(',', '.')
        if value == '':
            return None
        return float(value)

    @property
    def stop_lon(self):
        value = self._info['declong stop'].replace(',', '.')
        if value == '':
            return None
        return float(value)

    @property
    def full_name(self):
        return self._info['Name']

    @property
    def name(self):
        return self.full_name.split('.')[0].upper()

    @property
    def event_id(self):
        return self._info['EventID']

    @property
    def parent_event_id(self):
        value = self._info['ParentEventID']
        if not value:
            value = None
        return value

    @property
    def start_time(self):
        return self._info['StartTime']

    @property
    def stop_time(self):
        return self._info['StopTime']

    @property
    def air_pres(self):
        par = 'A_AverageAirPressure1'
        if par not in self._info:
            par = 'A_AverageAirPressure_QNH_1'
        if par not in self._info:
            return None
        value = self._info[par].replace(',', '.')
        if not value:
            return None
        return round(float(value), 1)

    @property
    def air_temp(self):
        value = self._info.get('A_AverageAirTemperature2', '').replace(',', '.')
        if not value:
            return None
        return round(float(value), 1)

    @property
    def wind_dir(self):
        value = self._info['A_AverageTrueWindDirSel'].replace(',', '.')
        if not value:
            return None
        return round(float(value))

    @property
    def wind_speed(self):
        value = self._info['A_AverageWindSpeed'].replace(',', '.')
        if not value:
            return None
        return round(float(value), 1)

    @property
    def min_depth(self):
        if not self._info.get('A_MinDepth'):
            return None
        value = self._info['A_MinDepth'].replace(',', '.')
        if not value:
            return None
        return round(float(value), 1)

    @property
    def max_depth(self):
        if not self._info.get('A_MaxDepth'):
            return None
        value = self._info['A_MaxDepth'].replace(',', '.')
        if not value:
            return None
        return round(float(value), 1)

    @property
    def departure_port(self):
        if not self._info.get('departure_port'):
            return None
        value = self._info['departure_port']
        if not value:
            return None
        return value

    @property
    def arrival_port(self):
        if not self._info.get('arrival_port'):
            return None
        value = self._info['arrival_port']
        if not value:
            return None
        return value

    @property
    def exp_leader(self):
        if not self._info.get('resp_staff'):
            return None
        value = self._info['resp_staff']
        if not value:
            return None
        return value

    @property
    def ices_rectangle(self):
        if not self._info.get('ICESrect'):
            return None
        value = self._info['ICESrect']
        if not value:
            return None
        return value

    @property
    def note(self):
        if not self._info.get('Note'):
            return None
        return self._info['Note'].strip()

    @property
    def parent(self):
        return self._parent

    @property
    def children(self):
        return list(self._children)

    def get_children(self, name: str = None) -> list:
        if name:
            return [event for event in self.children if event.name == name]
        return self.children

    def get_ongoing_events(self, **kwargs):
        ongoing_events = []
        for event in self._all_events.values():
            if self == event:
                continue
            if event.check_time(self.start_time) or event.check_time(self.stop_time):
                ongoing_events.append(event)
        if kwargs.get('filter'):
            new_ongoing_events = set()
            for event in ongoing_events:
                for name in FILTERED_EVENTS:
                    if name in event.name:
                        new_ongoing_events.add(event)
                        continue
            ongoing_events = list(new_ongoing_events)
            # ongoing_events = [event for event in ongoing_events if event.name in FILTERED_EVENTS]
        return ongoing_events

    def get_info(self) -> dict:
        """Returns a dict with information about the event"""
        info = dict(
            event_type=self.event_type,
            id=self.id,
            name=self.name,
            full_name=self.full_name,
            event_id=self.event_id,
            parent_event_id=self.parent_event_id,
            start_time=self.start_time,
            stop_time=self.stop_time,
            start_lat=self.start_lat,
            start_lon=self.start_lon,
            stop_lat=self.stop_lat,
            stop_lon=self.stop_lon,

            air_pres=self.air_pres,
            air_temp=self.air_temp,
            wind_dir =self.wind_dir,
            wind_speed=self.wind_speed,
            min_depth=self.min_depth,
            max_depth=self.max_depth,

            departure_port=self.departure_port,
            arrival_port=self.arrival_port,
            exp_leader=self.exp_leader,
            # ices_rectangle=self.ices_rectangle,
            note=self.note,
        )
        return info


class SvepaExportFile:
    def __init__(self, path):
        self._path = pathlib.Path(path)
        self._events = {}
        self.root_event = None
        self._load_information()
        self._save_hierarchy()

    def __repr__(self):
        return f'Svepa export file: {self.path}'

    @property
    def path(self):
        return self._path
    
    @property
    def events(self):
        return self._events

    @property
    def cruise(self):
        return self.root_event.full_name.split('.')[-1].strip('0')

    def _load_information(self):
        """ Loads the information in self._path """
        logger.info(f'Loading Svepa export file: {self.path}')
        df = pd.read_excel(self._path, dtype=str, keep_default_na=False)
        for i in df.index:
            event = Event(self._events, df.iloc[i])
            if not event.start_time:
                continue
            self._events[event.event_id] = event

    def _save_hierarchy(self):
        for event in self._events.values():
            event.add_parent_and_children()
            if not event.parent_event_id:
                if not event.event_id:
                    continue
                self.root_event = event

    def get_name_list(self):
        return sorted(set([event.name for event in self._events.values()]))

    def get_platform_events(self, name: str):
        events = []
        for event in self._events.values():
            if event.check_name(name):
                events.append(event)
        return events

    def get_event(self, event_id: str = None, name: str = None, time: datetime.datetime = None):
        if event_id:
            return self._events.get(event_id)
        for event in self._events.values():
            if event.check_name_and_time(name=name, time=time):
                return event

    def _add_general_info(self, info: dict) -> None:
        info['cruise'] = self.cruise

    def get_platforms_info(self) -> dict:
        all_info = {}
        # for plat in FILTERED_EVENTS:
        for plat in self.get_name_list():
            events = self.get_platform_events(plat)
            if not events:
                continue
            all_info[plat] = {}
            for event in events:
                info = event.get_info()
                all_info[plat][info['event_id']] = info
        return all_info


