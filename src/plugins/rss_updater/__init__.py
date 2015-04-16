from pluginmgr import Tool
from PyQt4 import QtCore, QtGui, uic
import config
import os
from feedfinder import feeds as findFeed
import feedparser
import models
from rss2epub import RSS2ePub
import tempfile

class RSSTool(Tool):
    def action(self):
        self._action = QtGui.QAction("Update Feeds", None)
        self._action.triggered.connect(self.updateFeeds)
        return self._action
    
    def updateFeeds(self):
        self.feeds = config.getValue("RSSPlugin", "feeds", [])
        for title, url in self.feeds:
            updateFeedBook(title, url)

# FIXME: this is in two plugins, see how to refactor
def updateFeedBook(title, url):
    b = models.Book.get_by(title = 'RSS - %s'%(title))
    if not b:
        b = models.Book(title = 'RSS - %s'%(title))
        models.session.commit()
        self.updateShelves.emit()
    # If there's an epub file for this book, overwrite it
    files = b.files_for_format('epub')

    if files:
        fname = files[0].file_name
        need_import = False
    else:
        # There isn't one, create it
        f = tempfile.NamedTemporaryFile(suffix='.epub', delete = False)
        f.close()
        fname = f.name
        need_import = True
    RSS2ePub().convert(url, fname)
    if need_import:
        if '\\' in fname: fname = fname.replace('\\','/')
        if fname[0] != '/': fname='/'+fname
        b.fetch_file('file://%s'%fname, 'epub')
    return b