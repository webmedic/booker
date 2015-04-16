from PyQt4 import QtNetwork, QtCore, QtGui, uic
import sys
from epubparser import EpubDocument
import feedparser
import ui
from config import *
import hashlib


class Main(QtGui.QMainWindow):

    def __init__(self, fname):
        QtGui.QMainWindow.__init__(self)

        self.fname = fname
        self.epub = EpubDocument(fname)
        uifile = ui.path('epubviewer.ui')
        uic.loadUi(uifile, self)
        self.ui = self
        self.addAction(self.actionPageDown)

        for l, c in self.epub.tocentries:
            item = QtGui.QListWidgetItem(l)
            item.contents = c
            self.chapters.addItem(item)

        self.old_manager = self.view.page().networkAccessManager()
        self.new_manager = NetworkAccessManager(self.old_manager, self)
        self.view.page().setNetworkAccessManager(self.new_manager)

        self.cur_path = ''
        sv, curSpineRef = getValue("epubviewer",
                                   "position-" +
                                   hashlib.sha224(self.fname).hexdigest(),
                                   [0, None])
        row = -1
        if curSpineRef:
            try:
                row = [j for i, j in self.epub.tocentries].index(curSpineRef)
            except ValueError:
                pass
        if row == -1:
            if self.epub.spinerefs[0] == self.epub.tocentries[0][1]:
                row = 0
        if row != -1:
            self.chapters.setCurrentRow(row)
            self.openPath(self.epub.tocentries[row][1])
        else:  # The first spineref is not in the toc. Usually means the cover.
            self.openPath(self.epub.spinerefs[0])

        self.actionClose.triggered.connect(self.close)
        self.actionShow_Contents.toggled.connect(self.chapters.setVisible)

    def closeEvent(self, ev):
        # Save position keyed by filename
        frame = self.view.page().mainFrame()
        sv = frame.scrollPosition().y()
        frame = self.view.page().mainFrame()
        curSpineRef = unicode(frame.url().toString())[12:]
        setValue("epubviewer",
                 "position-" + hashlib.sha224(self.fname).hexdigest(),
                 [sv, curSpineRef])
        QtGui.QMainWindow.closeEvent(self, ev)

    @QtCore.pyqtSlot("bool")
    def on_actionFull_Screen_toggled(self, b):
        if b:
            self.showFullScreen()
            # self.actionShow_Contents.setChecked(False)
        else:
            self.showNormal()
            # self.actionShow_Contents.setChecked(True)

    @QtCore.pyqtSlot()
    def on_actionPageDown_triggered(self):
        frame = self.view.page().mainFrame()
        if frame.scrollBarMaximum(QtCore.Qt.Vertical) == \
            frame.scrollPosition().y():
                self.on_actionNext_Chapter_triggered()
        else:
            frame.scroll(0, self.view.height())

    @QtCore.pyqtSlot()
    def on_actionNext_Chapter_triggered(self):
        # Find where on the spine we are
        frame = self.view.page().mainFrame()
        curSpineRef = unicode(frame.url().toString())[12:]
        try:
            curIdx = [j for i, j in self.epub.tocentries].index(curSpineRef)
        except ValueError:
            curIdx = -1
        if curIdx + 1 < len(self.epub.tocentries):
            self.chapters.setCurrentRow(curIdx + 1)
            self.openPath(self.epub.tocentries[curIdx + 1][1])

    @QtCore.pyqtSlot()
    def on_actionPrevious_Chapter_triggered(self):
        # Find where on the spine we are
        frame = self.view.page().mainFrame()
        curSpineRef = unicode(frame.url().toString())[12:]
        try:
            curIdx = [j for i, j in self.epub.tocentries].index(curSpineRef)
        except ValueError:
            curIdx = -1
        if curIdx > 0:
            self.chapters.setCurrentRow(curIdx - 1)
            self.openPath(self.epub.tocentries[curIdx - 1][1])

    def on_chapters_itemClicked(self, item):
        self.openPath(item.contents)

    def openPath(self, path, fragment=None):
        if "#" in path:
            path, fragment = path.split('#', 1)
        path = QtCore.QUrl.fromPercentEncoding(path)

        if self.cur_path != path:
            self.cur_path = path
            xml = self.epub.getData(path)
            encoding = feedparser._getCharacterEncoding({}, xml)[0]
            xml = xml.decode(encoding)
            self.view.page().mainFrame().setHtml(xml,
                                            QtCore.QUrl("epub://book/" + path))

        if fragment:
            self.javascript('document.location.hash = "%s"' % fragment)

    def javascript(self, string, typ=None):
        ans = self.view.page().mainFrame().evaluateJavaScript(string)
        if typ == 'int':
            ans = ans.toInt()
            if ans[1]:
                return ans[0]
            return 0
        if typ == 'string':
            return unicode(ans.toString())
        return ans

    def linkClicked(self, url):
        if url.isRelative():  # They all should be
            frag = unicode(url.fragment())
            path = unicode(url.path())
            self.openPath(path, frag)


class DownloadReply(QtNetwork. QNetworkReply):

    def __init__(self, parent, url, operation, w):
        self._w = w
        QtNetwork.QNetworkReply.__init__(self, parent)
        self.content = self._w.epub.getData(unicode(url.path())[1:])
        self.offset = 0

        self.setHeader(QtNetwork.QNetworkRequest.ContentTypeHeader,
                       QtCore.QVariant("application/binary"))
        self.setHeader(QtNetwork.QNetworkRequest.ContentLengthHeader,
                       QtCore.QVariant(len(self.content)))
        QtCore.QTimer.singleShot(0, self, QtCore.SIGNAL("readyRead()"))
        QtCore.QTimer.singleShot(0, self, QtCore.SIGNAL("finished()"))
        self.open(self.ReadOnly | self.Unbuffered)
        self.setUrl(url)

    def abort(self):
        pass

    def bytesAvailable(self):
        return len(self.content) - self.offset

    def isSequential(self):
        return True

    def readData(self, maxSize):
        if self.offset < len(self.content):
            end = min(self.offset + maxSize, len(self.content))
            data = self.content[self.offset:end]
            self.offset = end
            return data


class NetworkAccessManager(QtNetwork.QNetworkAccessManager):

    def __init__(self, old_manager, w):
        self._w = w
        QtNetwork.QNetworkAccessManager.__init__(self)
        self.old_manager = old_manager
        self.setCache(old_manager.cache())
        self.setCookieJar(old_manager.cookieJar())
        self.setProxy(old_manager.proxy())
        self.setProxyFactory(old_manager.proxyFactory())

    def createRequest(self, operation, request, data):

        if request.url().scheme() != "epub":
            return QtNetwork.QNetworkAccessManager.createRequest(self,
                                                                 operation,
                                                                 request,
                                                                 data)

        if operation == self.GetOperation:
            # Handle download:// URLs separately by creating custom
            # QNetworkReply objects.
            reply = DownloadReply(self, request.url(),
                                  self.GetOperation, self._w)
            return reply
        else:
            return QtNetwork.QNetworkAccessManager.createRequest(self,
                                                                 operation,
                                                                 request,
                                                                 data)


def main():
    # Again, this is boilerplate, it's going to be the same on
    # almost every app you write
    app = QtGui.QApplication(sys.argv)
    window = Main(sys.argv[1])
    window.show()
    # It's exec_ because exec is a reserved word in Python
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
