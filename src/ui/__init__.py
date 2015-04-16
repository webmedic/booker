# -*- coding: utf-8 -*-
import os


def path(filename):
    """Returns the full path to an .ui file within
       the module's folder"""
    path = os.path.join(os.path.dirname(__file__), filename)
    if not (os.path.isfile(path) and os.access(path, os.R_OK)):
        raise Exception("The file %s does not exist or is not readable" %
                                                                    filename)
    return path
