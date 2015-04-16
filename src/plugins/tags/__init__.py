from PyQt4 import QtGui, QtCore
import sys, os
import models
from pluginmgr import ShelfView

# This plugin lists the books by tag

EBOOK_EXTENSIONS=['epub','mobi','pdf']

class Catalog(ShelfView):

    title = "Books By Tag"
    itemText = "Tags"
    items = {}
    
    def showList(self, search = None):
        """Get all books from the DB and show them"""

        if not self.widget:
            print "Call setWidget first"
            return
        self.operate = self.showList
        self.items = {}
        css = '''
        ::item {
                padding: 0;
                margin: 0;
                height: 48;
            }
        '''

        self.widget.title.setText(self.title)
        # Setup widgetry
        self.widget.stack.setCurrentIndex(0)
        self.shelf = QtGui.QListWidget()
        # Make it look right
        self.shelf.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.shelf.setFrameShape(self.shelf.NoFrame)
        self.shelf.setDragEnabled(False)
        self.shelf.setSelectionMode(self.shelf.NoSelection)
        self.shelf.setStyleSheet(css)
        self.shelf.setIconSize(QtCore.QSize(48,48))
        # Hook the shelf context menu
        self.shelf.customContextMenuRequested.connect(self.shelfContextMenu)

        # Hook book editor
        self.shelf.itemActivated.connect(self.widget.on_books_itemActivated)

        # Fill the shelf
        if search:
            tags = models.Tag.query.order_by("name").filter(models.Tag.name.like("%%%s%%"%search))
        else:
            tags = models.Tag.query.order_by("name").all()
        
        for a in tags:
            a_item = QtGui.QListWidgetItem(a.name, self.shelf)
            for b in a.books:
                icon = QtGui.QIcon(QtGui.QPixmap(b.cover()).scaledToHeight(128, QtCore.Qt.SmoothTransformation))
                item = QtGui.QListWidgetItem(icon, b.title, self.shelf)
                item.book = b
                self.items[b.id] = item

        self.widget.shelfStack.setWidget(self.shelf)


    def showGrid(self, search = None):
        """Get all books from the DB and show them"""
        if not self.widget:
            print "Call setWidget first"
            return
        self.operate = self.showGrid
        self.items = {}
        
        self.widget.title.setText(self.title)
        css = '''
        ::item {
                padding: 0;
                margin: 0;
                width: 150px;
                height: 150px;
            }
        '''

        # Setup widgetry
        self.widget.stack.setCurrentIndex(0)
        self.shelves = QtGui.QWidget()
        self.shelvesLayout = QtGui.QVBoxLayout()
        self.shelves.setLayout(self.shelvesLayout)
        
        if search:
            tags = models.Tag.query.order_by("name").filter(models.Tag.name.like("%%%s%%"%search))
        else:
            tags = models.Tag.query.order_by("name").all()
        for a in tags:
            # Make a shelf
            shelf_label = QtGui.QLabel(a.name)
            shelf = QtGui.QListWidget()
            self.shelvesLayout.addWidget(shelf_label)
            self.shelvesLayout.addWidget(shelf)
            # Make it look right
            shelf.setStyleSheet(css)
            shelf.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
            shelf.setFrameShape(shelf.NoFrame)
            shelf.setIconSize(QtCore.QSize(128,128))
            shelf.setViewMode(shelf.IconMode)
            shelf.setMinimumHeight(153)
            shelf.setMaximumHeight(153)
            shelf.setMinimumWidth(153*len(a.books))
            shelf.setFlow(shelf.LeftToRight)
            shelf.setWrapping(False)
            shelf.setDragEnabled(False)
            shelf.setSelectionMode(shelf.NoSelection)

            # Hook the shelf context menu
            shelf.customContextMenuRequested.connect(self.shelfContextMenu)

            # Hook book editor
            shelf.itemActivated.connect(self.widget.on_books_itemActivated)
            
            # Fill the shelf
            for b in a.books:
                pixmap = QtGui.QPixmap(b.cover())
                if pixmap.isNull():
                    pixmap = QtGui.QPixmap(b.default_cover())
                icon =  QtGui.QIcon(pixmap.scaledToHeight(128, QtCore.Qt.SmoothTransformation))
                item = QtGui.QListWidgetItem(icon, b.title, shelf)
                item.book = b
                self.items[b.id] = item
                
        self.shelvesLayout.addStretch(1)
        self.widget.shelfStack.setWidget(self.shelves)

    def updateBook(self, book):
        # This may get called when no books
        # have been loaded in this view, so make it cheap
        if self.items and book.id in self.items:
            item = self.items[book.id]
            icon = QtGui.QIcon(QtGui.QPixmap(book.cover()).scaledToHeight(128, QtCore.Qt.SmoothTransformation))
            item.setText(book.title)
            item.setIcon(icon)
            item.book = book
