import datetime
import logging
import pickle
import pathlib
from functools import lru_cache

import yaml


logger = logging.getLogger(__file__)

THIS_DIR = pathlib.Path(__file__).parent
DATA_DIR = THIS_DIR / "DATA_FILES"

SVEPA_INFO_URL = r'https://raw.githubusercontent.com/nodc-sweden/svepa_event/main/src/svepa_event/DATA_FILES/svepa_info.yaml'

INFO_FILE_PATH = DATA_DIR / 'svepa_info.yaml'
PICKLE_INFO_FILE_PATH = DATA_DIR / 'svepa_info.pickle'


TIME_FORMATS = [
    '%Y%m%d%H%M',
    '%Y%m%d%H%M%S',
    '%Y-%m-%d %H:%M',
    '%Y-%m-%d %H:%M:%S',
]


# @lru_cache
def load_stored_svepa_info():
    return load() or {}


def _load_pickle():
    if not PICKLE_INFO_FILE_PATH.exists():
        return {}
    with open(PICKLE_INFO_FILE_PATH, 'rb') as fid:
        return pickle.load(fid)


def _load_yaml():
    if not INFO_FILE_PATH.exists():
        return {}
    with open(INFO_FILE_PATH) as fid:
        return yaml.safe_load(fid)


def save_pickle_from_yaml():
    all_info = _load_yaml()
    _save_pickle(all_info)


def _save_pickle(all_info: dict):
    with open(PICKLE_INFO_FILE_PATH, 'wb') as fid:
        pickle.dump(all_info, fid)


def _save_yaml(all_info: dict):
    with open(INFO_FILE_PATH, 'w') as fid:
        yaml.safe_dump(all_info, fid)


def load() -> dict:
    all_info = {}
    try:
        all_info = _load_pickle()
        logger.info('Pickle file loaded')
    except:
        pass
    if not all_info:
        all_info = _load_yaml()
        logger.info('YAML file loaded')
        _save_pickle(all_info)
    _convert_to_datetime(all_info)
    return all_info


def save(all_info):
    _convert_to_date_string(all_info)
    _save_pickle(all_info)
    _save_yaml(all_info)


def _convert_to_date_string(info):
    if not isinstance(info, dict):
        return
    for key, value in info.items():
        if 'time' in key:
            if not value:
                logger.info(f'{key=} has no value!')
                continue
            info[key] = value.strftime('%Y%m%d%H%M%S')
        _convert_to_date_string(info[key])


def _convert_to_datetime(info):
    if not isinstance(info, dict):
        return
    for key, value in info.items():
        if 'time' in key:
            if not value:
                logger.info(f'{key=} has no value!')
                continue
            info[key] = datetime.datetime.strptime(value, '%Y%m%d%H%M%S')
        _convert_to_datetime(info[key])


def get_datetime_object(time_str: str) -> datetime.datetime:
    for fmt in TIME_FORMATS:
        try:
            return datetime.datetime.strptime(time_str, fmt)
        except ValueError:
            pass

