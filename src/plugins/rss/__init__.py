from pluginmgr import BookStore, Tool
from PyQt4 import QtCore, QtGui, uic
import config
import os
from feedfinder import feeds as findFeed
import feedparser
import models
from rss2epub import RSS2ePub
import tempfile

class RSSWidget(QtGui.QWidget):
    updateBook = QtCore.pyqtSignal(models.Book)
    updateShelves = QtCore.pyqtSignal()
    def __init__(self, parent = None):
        QtGui.QWidget.__init__(self, parent)
        uifile = os.path.join(
            os.path.abspath(
                os.path.dirname(__file__)),'store.ui')
        uic.loadUi(uifile, self)
        self.ui = self
        self.loadFeeds()
        self.splitter.setSizes([1,0])

    def loadFeeds(self):
        self.feeds = config.getValue("RSSPlugin", "feeds", [])
        self.feedList.clear()
        for title,url in self.feeds:
            i = QtGui.QListWidgetItem(title, self.feedList)
            self.feedList.addItem(i)

    def saveFeeds(self):
        config.setValue("RSSPlugin", "feeds", self.feeds)

    @QtCore.pyqtSlot()
    def on_add_clicked(self):
        t, ok = QtGui.QInputDialog.getText(self, "Aranduka - Add Feed", "Enter the URL of the feed or site:")
        if not ok:
            return
        t = unicode(t)
        print t
        # FIXME: make unblocking
        # FIXME: make the user choose a feed
        feeds = findFeed(unicode(t))
        print feeds
        feed = feeds[0]
        data = feedparser.parse(feed)
        self.feeds.append([data.feed.title, feed])

        # Create a book for this feed
        b = models.Book(title = 'RSS - %s'%(data.feed.title))
        models.session.commit()
        
        self.saveFeeds()
        self.loadFeeds()

    @QtCore.pyqtSlot()
    def on_remove_clicked(self):
        i = self.feedList.currentRow()
        if i==-1:
            return
        del(self.feeds[i])
        self.saveFeeds()
        self.loadFeeds()

    def on_feedList_currentRowChanged(self, row):
        title, url = self.feeds[row]
        self.title.setText(title)
        self.url.setText(url)

    @QtCore.pyqtSlot()
    def on_edit_clicked(self):
        i = self.feedList.currentRow()
        if i==-1:
            return
        self.splitter.setSizes([1,1])

    @QtCore.pyqtSlot()
    def on_save_clicked(self):
        i = self.feedList.currentRow()
        self.feeds[i] = [unicode(self.title.text()), unicode(self.url.text())]
        self.saveFeeds()
        self.loadFeeds()
        self.splitter.setSizes([1,0])
        
    
    @QtCore.pyqtSlot()
    def on_refresh_clicked(self):
        i = self.feedList.currentRow()
        if i==-1:
            return
        title, url = self.feeds[i]
        b = updateFeedBook(title, url)
        self.updateBook.emit(b)

class RSSStore(BookStore):
    """Fetch RSS feeds as ePub"""

    title = "RSS Feeds"
    itemText = "RSS Feeds"

    def __init__(self):
        print "INIT:", self.title
        self.widget = None
        self.w = None
        BookStore.__init__(self)

    def treeItem(self):
        """Returns a QTreeWidgetItem representing this
        plugin"""
        return QtGui.QTreeWidgetItem([self.itemText])

    def setWidget (self, widget):
        self.widget = widget

    def operate(self):
        "Show the store"
        if not self.widget:
            print "Call setWidget first"
            return
        self.widget.title.setText(self.title)
        if not self.w:
            self.w = RSSWidget()
            self.w.updateBook.connect(self.widget.updateBook)
            self.w.updateShelves.connect(self.widget.updateShelves)
            self.pageNumber = self.widget.stack.addWidget(self.w)
        self.widget.stack.setCurrentIndex(self.pageNumber)

    showGrid = operate
    showList = operate


    @QtCore.pyqtSlot()
    def doSearch(self, *args):
        "No search here"
        pass

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