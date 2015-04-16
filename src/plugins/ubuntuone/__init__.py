from PyQt4 import QtCore, QtGui, uic
from pluginmgr import Device
import os
import models
import utils
import json
import unicodedata
import re
import shutil

from utils import slugify

class FolderDevice(object):
    """Syncs a set of tags' books to a folder, using specified
    formats.
    """
    def __init__(self, tags, formats, name, folder):
        self.tags = tags
        self.formats = formats
        self.name = name
        self.folder = folder

    def sync(self):
        """Perform the sync"""
        
        try:
            os.mkdir (self.folder)
        except: pass
        
        if not os.path.isdir(self.folder):
            raise IOError
        
        print "syncing tags:", self.tags, "to folder", self.folder
        files_to_sync = []
        book_set = set()
        for t in self.tags:
            tag = models.Tag.get_by(name = t)
            for b in tag.books:
                book_set.add(b)
        for b in book_set:
            for f in self.formats:
                fl = b.files_for_format("."+f)
                if fl:
                    files_to_sync.append([b, fl] )
                    break
            else:
                # FIXME: here we should autoconvert
                files_to_sync.append([b, []])

        print 'FTS:', files_to_sync

        for d in files_to_sync:
            b, fn = d
            if not fn:
                # FIXME: Whine that we can't sync this book
                continue
            _, ext = os.path.splitext(fn[0])
            new_name = slugify(b.title)+ext
            dest = os.path.join(self.folder, new_name)
            print fn[0],'=>', dest
            shutil.copyfile(fn[0],dest)

class NewDeviceDialog(QtGui.QDialog):
    def __init__(self):
        QtGui.QDialog.__init__(self)
        uifile = os.path.join(
            os.path.abspath(
                os.path.dirname(__file__)),'new_device.ui')
        self.w = uic.loadUi(uifile, self)
        for f in ["epub","pdf","mobi","fb2","txt"]:
            self.w.formats.addItem(f)

        for t in models.Tag.query.order_by("name").all():
            self.w.tags.addItem(t.name)

class UbuntuOnePlugin(Device, QtCore.QObject):
    """Sync one or more tags to ubuntu one"""

    name = "Ubuntu One"
    configurable = True

    def __init__(self):
        self.device = None
        self.load()
        QtCore.QObject.__init__(self)
                
    def deviceActions(self):
        """Returns a list of actions, one for each device"""
        print "XXX:", self.device
        if self.device:
            return [QtGui.QAction("Sync Now", self, triggered = self.device.sync)]
        return []

    def actionNew(self):
        self.action = QtGui.QAction("Configure", None)
        self.action.triggered.connect(self.configure)
        return self.action

    def save(self):
        devfn = os.path.join(utils.BASEPATH,"ubuntuoneoptions")
        f = open(devfn,"w+")
        data = json.dumps({"tags": self.device.tags,
                    "formats": self.device.formats,
                    "name": self.device.name,
                    "folder": self.device.folder
                })
        print data
        f.write(data)
        f.close()

    def load(self):
        try:
            devfn = os.path.join(utils.BASEPATH,"ubuntuoneoptions")
            f = open(devfn,"r")
            data = json.loads(f.read())
            f.close()
            self.device = FolderDevice(**data)
            
        except IOError:
            self.devices=[]

    def configure(self):
        while True:
            self.w = NewDeviceDialog()
            r = self.w.exec_()
            if r == self.w.Rejected:
                return
            # Accepted, create new device
            tags = [unicode(i.text()) for i in self.w.tags.selectedItems()]
            print tags
            formats = [unicode(i.text()) for i in self.w.formats.selectedItems()]
            print formats
            path = os.path.join(os.path.expanduser('~'),'Ubuntu One',"Aranduka Books")
            name = "Ubuntu One"

            # Validate
            if not path or not name or not tags:
                QtGui.QMessageBox.critical(None, "Error", "Path, name and tags are mandatory")
                continue
            self.device = FolderDevice(tags, formats, name, path)
            self.save()
            break
