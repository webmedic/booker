# -*- coding: utf-8 -*-

# Singleton config object

import configparser
import os
from json import dumps, loads
from utils import BASEPATH

cfname = os.path.join(BASEPATH, 'config')


def getValue(section, key, default=None):
    section = section.lower()
    key = key.lower()
    try:
        return loads(conf.get(section, key))
    except:
        return default


def setValue(section, key, value):
    section = str(section)
    key = str(key)
    section = section.lower()
    key = key.lower()
    value = dumps(value)
    try:
        r = conf.set(section, key, value)
    except configparser.NoSectionError:
        conf.add_section(section)
        r = conf.set(section, key, value)
    f = open(cfname, 'w')
    conf.write(f)
    return r


class ConfigError(Exception):

    def __init__(self, modulename, msg):
        self.modulename = modulename
        self.msg = msg


conf = configparser.SafeConfigParser()
if not os.path.isfile(cfname):
    open(cfname, 'w').close()
f = open(cfname, 'r')
conf.readfp(f)
f.close()
