# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/godlike/eric/aranduka/aranduka.ui'
#
# Created: Wed Sep  1 00:32:14 2010
#      by: PyQt4 UI code generator 4.7.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1032, 700)
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.widget = QtGui.QWidget(self.centralwidget)
        self.widget.setGeometry(QtCore.QRect(0, 10, 951, 581))
        self.widget.setObjectName("widget")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1032, 21))
        self.menubar.setObjectName("menubar")
        self.menuSi_aca_van_los_menuses = QtGui.QMenu(self.menubar)
        self.menuSi_aca_van_los_menuses.setObjectName("menuSi_aca_van_los_menuses")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.toolBar = QtGui.QToolBar(MainWindow)
        self.toolBar.setObjectName("toolBar")
        MainWindow.addToolBar(QtCore.Qt.ToolBarArea(QtCore.Qt.TopToolBarArea), self.toolBar)
        self.actionPero_no_puse_nada_todavia = QtGui.QAction(MainWindow)
        self.actionPero_no_puse_nada_todavia.setObjectName("actionPero_no_puse_nada_todavia")
        self.actionMain = QtGui.QAction(MainWindow)
        self.actionMain.setObjectName("actionMain")
        self.actionView_Queue = QtGui.QAction(MainWindow)
        self.actionView_Queue.setObjectName("actionView_Queue")
        self.actionShelves = QtGui.QAction(MainWindow)
        self.actionShelves.setObjectName("actionShelves")
        self.actionTags = QtGui.QAction(MainWindow)
        self.actionTags.setObjectName("actionTags")
        self.menuSi_aca_van_los_menuses.addAction(self.actionPero_no_puse_nada_todavia)
        self.menubar.addAction(self.menuSi_aca_van_los_menuses.menuAction())
        self.toolBar.addAction(self.actionMain)
        self.toolBar.addAction(self.actionView_Queue)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.actionShelves)
        self.toolBar.addAction(self.actionTags)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QtGui.QApplication.translate("MainWindow", "MainWindow", None, QtGui.QApplication.UnicodeUTF8))
        self.menuSi_aca_van_los_menuses.setTitle(QtGui.QApplication.translate("MainWindow", "Si, aca van los menuses", None, QtGui.QApplication.UnicodeUTF8))
        self.toolBar.setWindowTitle(QtGui.QApplication.translate("MainWindow", "toolBar", None, QtGui.QApplication.UnicodeUTF8))
        self.actionPero_no_puse_nada_todavia.setText(QtGui.QApplication.translate("MainWindow", "Pero no puse nada todavia", None, QtGui.QApplication.UnicodeUTF8))
        self.actionMain.setText(QtGui.QApplication.translate("MainWindow", "Main", None, QtGui.QApplication.UnicodeUTF8))
        self.actionView_Queue.setText(QtGui.QApplication.translate("MainWindow", "View Queue", None, QtGui.QApplication.UnicodeUTF8))
        self.actionShelves.setText(QtGui.QApplication.translate("MainWindow", "Shelves", None, QtGui.QApplication.UnicodeUTF8))
        self.actionTags.setText(QtGui.QApplication.translate("MainWindow", "Tags", None, QtGui.QApplication.UnicodeUTF8))


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    MainWindow = QtGui.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())

