#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Module implementing MainWindow.
"""
import sys
from PyQt4.QtGui import QMainWindow, QApplication
from PyQt4.QtCore import pyqtSignature

from Ui_aranduka import Ui_MainWindow
from main import MainView
from queue import Queue

class MainWindow(QMainWindow, Ui_MainWindow):
    """
    Class documentation goes here.
    """
    def __init__(self, parent = None):
        """
        Constructor
        """
        QMainWindow.__init__(self, parent)
        self.setupUi(self)
        self.main = MainView(self.centralWidget())
        self.queue = Queue(self.centralWidget())
        #self.setCentralWidget(self.main)
        self.queue.hide()
        self.show()
    
    @pyqtSignature("")
    def on_actionMain_triggered(self):
        """
        Slot documentation goes here.
        """
        self.queue.hide()
        self.main.show()
        #self.setCentralWidget(self.main)
    
    @pyqtSignature("")
    def on_actionView_Queue_triggered(self):
        """
        Slot documentation goes here.
        """
        self.main.hide()
        self.queue.show()
        #self.setCentralWidget(self.queue)
        
if __name__ == "__main__":
        app = QApplication(sys.argv)
        mw = MainWindow()
        sys.exit(app.exec_())
