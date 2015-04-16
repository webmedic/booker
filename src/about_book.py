#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import ui

from PyQt4 import QtCore, QtGui, QtWebKit, uic

import codecs
import models
from templite import Templite
import time


class WebView(QtWebKit.QWebView):
    """We have to reimplement a QWebView to be able
    to create a new window (popups)"""

    def createWindow(self, webwindowtype):
        print "New WebWindow created."
        self.pop = WebView()
        self.pop.show()
        return self.pop


class AboutBook(QtGui.QWidget):

    def __init__(self, book_id=None, *args):
        QtGui.QWidget.__init__(self, *args)
        uifile = ui.path('about_book.ui')
        uic.loadUi(uifile, self)
        self.ui = self

        self.about_web_view = WebView()
        self.verticalLayout.insertWidget(0, self.about_web_view)
        self.about_web_view.show()

        self.about_web_view.settings().setAttribute(
                    QtWebKit.QWebSettings.JavascriptEnabled, True)
        self.about_web_view.settings().setAttribute(
                    QtWebKit.QWebSettings.JavascriptCanOpenWindows, True)
        self.about_web_view.settings().setAttribute(
                    QtWebKit.QWebSettings.JavascriptCanAccessClipboard, True)
        self.about_web_view.page().setLinkDelegationPolicy(
                    self.about_web_view.page().DelegateAllLinks)
        # self.about_web_view.linkClicked.connect(self.openLink)
        # StyleSheet
        #self.about_web_view.settings().setUserStyleSheetUrl(
                    #QtCore.QUrl.fromLocalFile(
                        #os.path.join(os.path.dirname(__file__),
                                     #'about_book.css')))

        if book_id is not None:
            self.load_data(book_id)

    def load_data(self, book_id):
        self.book = models.Book.get_by(id=book_id)
        if not self.book:
            # Called with invalid book ID
            print "Wrong book ID"

        tplfile = codecs.open(os.path.join(os.path.dirname(__file__),
                                           'templates',
                                           'about_the_book.tmpl'),
                             'r', 'utf-8')
        self.template = Templite(tplfile.read())
        tplfile.close()
        t1 = time.time()
        html = self.template.render(
            title=self.book.title,
            authors=self.book.authors,
            identifiers=[[identifier.key, identifier.value]
                                for identifier in self.book.identifiers],
            files=[fname.file_name for fname in self.book.files],
            tags=[tag.name for tag in self.book.tags],
            thumb=QtCore.QUrl.fromLocalFile(self.book.cover()).toString(),
            quotes=['Sample Quote #1', 'Sample Quote #2'],
            )
        print "Rendered in: %s seconds" % (time.time() - t1)
        self.about_web_view.page().mainFrame().setHtml(html)


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    models.initDB()
    if len(sys.argv) == 1:
        # use a default book
        ventana = AboutBook(models.Book.get_by().id)
    else:
        ventana = AboutBook(int(sys.argv[1]))
    ventana.show()
    sys.exit(app.exec_())
