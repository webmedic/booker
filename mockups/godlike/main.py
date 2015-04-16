# -*- coding: utf-8 -*-

"""
Module implementing MainView.
"""

from PyQt4.QtGui import *
from PyQt4.QtCore import pyqtSignature

from Ui_main import Ui_Form

class MainView(QWidget, Ui_Form):
    """
    Class documentation goes here.
    """
    def __init__(self, parent = None):
        """
        Constructor
        """
        QWidget.__init__(self, parent)
        self.setupUi(self)
        martian_pixmap = QPixmap("martian.jpg")
        fahrenheit_pixmap = QPixmap("fahrenheit.jpg")
        f_item = QTreeWidgetItem(["", "Fahrenheit 451",  "Ray Bradbury", "5", "No"])
        m_item = QTreeWidgetItem(["", "The Martian Chronicles", "Ray Bradbury", "4", "Yes"])
        f_item.setIcon(0,  QIcon(fahrenheit_pixmap))
        m_item.setIcon(0,  QIcon(martian_pixmap))
        self.tw_books.addTopLevelItem(f_item)
        self.tw_books.addTopLevelItem(m_item)
        self.show()
