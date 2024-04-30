import datetime
from svepa_event import helpers
from svepa_event.svepa_event import SvepaEvent
from svepa_event.svepa_event import SvepaEventCollection
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)


class StoredSvepaInfo:
    def __init__(self):
        self._info = dict()
        self._load_info()

    def _load_info(self):
        self._info = helpers.load_stored_svepa_info()

    def reload_data(self):
        self._info = helpers.load()

    def get_info(self, platform: str = None, time: datetime.datetime | str = None, event_id: str = None) -> dict:
        if not event_id and not (platform and time):
            raise Exception('Missing platform and time or event_id when trying to get svepa information')
        dtime = time
        if time and type(time) == str:
            dtime = helpers.get_datetime_object(time)
            if not dtime:
                time_fmts = ', '.join(helpers.TIME_FORMATS)
                raise f'Invalid time format "{time}". Must be datetime object or have one of these formats: {time_fmts}'
        info = {}
        found = False
        if event_id:
            for key in self._info:
                if found:
                    break
                for _id, _info in self._info[key].items():
                    if _id == event_id:
                        return _info

        elif platform and dtime:
            plat = platform.upper()
            if plat not in self._info:
                return {}
            for _id, _info in self._info[plat].items():
                if _info['start_time'] <= dtime <= _info['stop_time']:
                    return _info
        return info

    def get_event(self, platform: str = None, time: datetime.datetime = None, event_id: str = None):
        info = self.get_info(platform=platform, time=time, event_id=event_id)
        return SvepaEvent(stored_svepa_info=self, info=info)

    @lru_cache
    def get_infos(self, platform: str = None, time: datetime.datetime | str = None, lat: float = None, lon: float = None,
                  year: int = None, month: int = None):
        dtime = time
        if time and type(time) == str:
            dtime = helpers.get_datetime_object(time)
            if not dtime:
                time_fmts = ', '.join(helpers.TIME_FORMATS)
                raise f'Invalid time format "{time}". Must be datetime object or have one of these formats: {time_fmts}'
        lst = []
        for key in self._info:
            if platform and key.upper() != platform.upper():
                continue
            for _id, _info in self._info[key].items():
                if any([year, month, dtime]):
                    if not _info['start_time']:
                        msg = f'Missing start time for event: {_info["event_id"]}'
                        logger.info(msg)
                        continue
                    if not _info['stop_time']:
                        msg = f'Missing stop time for event: {_info["event_id"]}'
                        logger.info(msg)
                        continue
                if year and not (_info['start_time'].year == year or _info['stop_time'].year == year):
                    continue
                if month and not (_info['start_time'].month == month or _info['stop_time'].month == month):
                    continue
                if dtime and not (_info['start_time'] <= dtime <= _info['stop_time']):
                    continue
                if lat:
                    if not (_info['start_lat'] and _info['stop_lat']):
                        continue
                    if not (_info['start_lat'] <= lat <= _info['stop_lat']):
                        continue
                if lon:
                    if not (_info['start_lon'] and _info['stop_lon']):
                        continue
                    if not (_info['start_lon'] <= lon <= _info['stop_lon']):
                        continue
                lst.append(_info)
        return lst

    def get_events(self, platform: str = None, time: datetime.datetime = None, lat: float = None, lon: float = None,
                   year: int = None, month: int = None) -> SvepaEventCollection[SvepaEvent]:
        info_lst = self.get_infos(platform=platform, time=time, lat=lat, lon=lon, year=year, month=month)
        events = SvepaEventCollection()
        for info in info_lst:
            events.append(SvepaEvent(stored_svepa_info=self, info=info))
        return events
        # return [SvepaEvent(stored_svepa_info=self, info=info) for info in info_lst]

    def get_children_info(self, event_id: str) -> list[str]:
        lst = []
        for key in self._info:
            for _id, _info in self._info[key].items():
                if _info.get('parent_event_id') == event_id:
                    lst.append(_info)
        return lst

    def get_children_events(self, event_id: str) -> SvepaEventCollection[SvepaEvent]:
        info_lst = self.get_children_info(event_id=event_id)
        lst = SvepaEventCollection()
        for info in info_lst:
            lst.append(SvepaEvent(stored_svepa_info=self, info=info))
        return lst

    @lru_cache
    def get_ongoing_events(self, event: SvepaEvent) -> SvepaEventCollection[SvepaEvent]:
        # event_lst = []
        event_lst = SvepaEventCollection()
        for key in self._info:
            for _id, _info in self._info[key].items():
                ev = None
                if _info['start_time'] and event.start_time <= _info['start_time'] <= event.stop_time:
                    ev = SvepaEvent(stored_svepa_info=self, info=_info)
                elif _info['stop_time'] and event.start_time <= _info['stop_time'] <= event.stop_time:
                    ev = SvepaEvent(stored_svepa_info=self, info=_info)
                elif _info['start_time'] and _info['stop_time']:
                    if _info['start_time'] <= event.start_time <= _info['stop_time']:
                        ev = SvepaEvent(stored_svepa_info=self, info=_info)
                if not ev:
                    continue
                if ev.event_id == event.event_id:
                    continue
                event_lst.append(ev)
        return event_lst

