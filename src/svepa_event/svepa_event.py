from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from svepa_event.svepa_info import StoredSvepaInfo


class SvepaEventCollection(list):

    def __getattr__(self, item):
        """Returns first occurrence of event with name equals item"""
        for event in sorted(self):
            if item.upper() in event.name:
                return event

    def __str__(self):
        lines = []
        for event in sorted(self):
            start_time = ''
            if event.start_time:
                start_time = event.start_time.date()
            stop_time = ''
            if event.stop_time:
                stop_time = event.stop_time.date()
            duration = f'({event.duration or "?"})'
            lines.append(f'{event.full_name.ljust(20)}{start_time}  >>>  {str(stop_time).ljust(15)} {duration.ljust(20)}')
        return '\n'.join(lines)


class SvepaEvent:
    def __init__(self, stored_svepa_info: StoredSvepaInfo = None, info: dict = None):
        self._stored_svepa_info = stored_svepa_info
        self._info = info

    def __repr__(self):
        return f'{self.__class__.__name__}: {self.full_name} [{self.start_time} - {self.stop_time}] ({self.event_id})'

    def __str__(self):
        lst = [
            '=' * 110,
            self.__repr__(),
            '-' * 110,
        ]
        ljust = 30
        for key in sorted(self._info):
            lst.append(f'  {key.ljust(ljust)}{self._info[key]}')
        ongoing_events = ', '.join(sorted(set([event.name for event in self.ongoing_events])))
        lst.append(f'  {"ongoing_events".ljust(ljust)}{ongoing_events}')
        lst.append('')
        return '\n'.join(lst)

    def __getattr__(self, item):
        if item not in self._info:
            raise AttributeError(item)
        return self._info.get(item)

    def __getitem__(self, item):
        return self._info.get(item)

    def __lt__(self, other):
        if self.start_time and other.start_time:
            return self.start_time < other.start_time
        if self.start_time:
            return True
        return False

    @property
    def attributes(self) -> list[str]:
        return sorted(self._info)

    @property
    def parent(self):
        if not self.parent_event_id:
            return
        return self._stored_svepa_info.get_event(event_id=self.parent_event_id)

    @property
    def station_event(self) -> SvepaEvent | None:
        event = self
        while True:
            event = event.parent
            if event.event_type.upper() == 'STATION':
                return event
            if not event:
                return

    @property
    def cruise_event(self) -> SvepaEvent | None:
        event = self
        while True:
            event = event.parent
            if event.event_type.upper() == 'TRIP':
                return event
            if not event:
                return

    @property
    def children(self) -> SvepaEventCollection[SvepaEvent]:
        return self._stored_svepa_info.get_children_events(self.event_id)

    @property
    def ongoing_events(self) -> SvepaEventCollection[SvepaEvent]:
        return self._stored_svepa_info.get_ongoing_events(self)

    @property
    def duration(self) -> datetime.timedelta | None:
        if self.start_time and self.stop_time:
            return self.stop_time - self.start_time

    def get_ongoing_event(self, event_name: str = None, first: bool = True) -> SvepaEvent | SvepaEventCollection[SvepaEvent] | None:
        if not event_name:
            return self.ongoing_events
        ongoing_events = SvepaEventCollection()
        en = event_name.upper()
        for event in self.ongoing_events:
            if en in event.name.upper():
                if first:
                    return event
                ongoing_events.append(event)
        if first:
            return None
        return ongoing_events



