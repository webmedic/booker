from PyQt4 import QtGui, QtCore, QtNetwork
import sys


class Downloads(QtGui.QProgressBar):

    setStatusMessage = QtCore.pyqtSignal("PyQt_PyObject")

    def __init__(self, parent=None):
        super(Downloads, self).__init__(parent)
        self.popup = QtGui.QWidget()

        self.bars = {}
        self.layout = QtGui.QVBoxLayout()
        self.popup.setLayout(self.layout)
        self.manager = QtNetwork.QNetworkAccessManager(self)
        self.setVisible(False)
        self.setMaximumWidth(100)

    def fetch(self, url, destination):
        if url in self.bars:
            print "Already downloading:", url
            return
        print "Downloading:", url
        address = QtCore.QUrl(url)
        reply = self.manager.get(QtNetwork.QNetworkRequest(address))
        reply.downloadProgress.connect(self.progress)
        reply.finished.connect(self.finished)
        bar = QtGui.QProgressBar()
        self.layout.addWidget(bar)
        self.bars[url] = [url, bar, reply, destination]

    def finished(self):
        reply = self.sender()
        url = unicode(reply.url().toString())
        _, bar, _, fname = self.bars[url]
        redirURL = unicode(reply.attribute(
            QtNetwork.QNetworkRequest.RedirectionTargetAttribute).toString())
        del self.bars[url]
        bar.deleteLater()
        if redirURL and redirURL != url:
            # Need to redirect
            print "Following redirect to:", redirURL
            self.fetch(redirURL, fname)
        else:
            data = str(reply.readAll())
            f = open(fname, 'wb')
            f.write(data)
            f.close()
            print "Finished downloading:", url

    def progress(self, received, total):
        url = unicode(self.sender().url().toString())
        print "progress:", url
        _, bar, reply, fname = self.bars[url]
        bar.setMaximum(total)
        bar.setValue(received)

        # Calculate average bar
        tot = 0
        val = 0
        for u in self.bars:
            bar = self.bars[u][1]
            if bar.maximum() == -1:
                tot += 100000  # Yes, this is evil
            else:
                tot += bar.maximum()
            val += bar.value()
        print tot, val
        self.setMaximum(tot)
        self.setValue(val)
        if tot == 0 or tot == val:
            self.setVisible(False)
            self.setStatusMessage.emit(u"")
        else:
            self.setVisible(True)


def main():
    app = QtGui.QApplication(sys.argv)
    window = Downloads()
    window.show()
    window.fetch("http://www.kde.org")
    window.fetch("http://www.gnome.org")
    window.fetch("http://www.ubuntu.com")
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
