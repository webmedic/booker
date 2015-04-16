from PyQt4 import QtCore, QtGui
from pluginmgr import Tool
import multiprocessing
import Queue
import sys, os

class Plugin(Tool):

    _proc = None
    _action = None
    
    def action(self):
        if self._action is None:
            self._action = QtGui.QAction("Publish Catalog", None)
            self._action.setCheckable(True)
            self._action.triggered.connect(self.publish)
        return self._action

    def check_url (self):
        publisher = __import__('publisher')
        try:
            data = publisher.queue.get(False)
            if data is not None:
                if 'url' in data:
                    QtGui.QMessageBox.information(None, \
                                                  u'Catalog published', \
                                                  u'You can access your catalog on: %s'%data['url'], \
                                                  QtGui.QMessageBox.Ok, \
                                                  QtGui.QMessageBox.NoButton, \
                                                  QtGui.QMessageBox.NoButton)
                elif 'error' in data:
                    print "Error publishing catalog: %s"%data['error']
                    QtGui.QMessageBox.critical(self, \
                                              u'Failed to publish catalog', \
                                              u'An error ocurred while trying to publish your catalog.')
                self.timer.stop()
        except Queue.Empty:
            pass

    def publish(self, checked):
        print "Publish: ", checked
        if not checked and self._proc:
            print "Stopping OPDS server"
            self._proc.terminate()
            self._proc = None
            return 

        if not self._proc:
            dirname = os.path.join(
                os.path.abspath(
                    os.path.dirname(__file__)))
            sys.path.append(dirname)

            self.timer = QtCore.QTimer()
            self.timer.timeout.connect(self.check_url)
            self.timer.start(1000)

            publisher = __import__('publisher')
            self._proc = multiprocessing.Process(target = publisher.real_publish)
            self._proc.daemon = True
            self._proc.start()
