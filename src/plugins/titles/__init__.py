from PyQt4 import QtGui, QtCore
import sys, os
import models
from pluginmgr import ShelfView
from functools import partial

# This plugin lists the books by title

EBOOK_EXTENSIONS=['epub','mobi','pdf']

class Catalog(ShelfView):

    title = "Books By Title"
    itemText = "Titles"
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
            books = models.Book.query.filter(models.Book.title.like("%%%s%%"%search))
        else:
            books = models.Book.query.order_by("title").all()
        
        for b in books:
            icon = QtGui.QIcon(QtGui.QPixmap(b.cover()).scaledToHeight(128, QtCore.Qt.SmoothTransformation))
            print icon
            item = QtGui.QListWidgetItem(icon, b.title, self.shelf)
            item.book = b
            self.items[b.id] = item
        self.shelvesLayout.addStretch(1)
        self.widget.shelfStack.setWidget(self.shelf)


    def showGrid(self, search=None):
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


        # Group books by initial (FIXME: make the DB do it)
        grouped_books={}
        def add_book(b, k):
            if k in grouped_books:
                grouped_books[k].append(b)
            else:
                grouped_books[k]=[b]
        
        # Fill the shelf
        if search:
            books = models.Book.query.filter(models.Book.title.like("%%%s%%"%search))
        else:
            books = models.Book.query.order_by("title").all()
            
        for b in books:
            initial = b.title[0].upper()
            if initial.isdigit():
                add_book(b,'#')
            elif initial.isalpha():
                add_book(b,initial)
            else:
                add_book(b,'@')
        keys = grouped_books.keys()
        keys.sort()
        for k in keys:
            # Make a shelf
            shelf_label = QtGui.QLabel("Books starting with: %s"%k)
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
            shelf.setMinimumWidth(153*len(grouped_books[k]))
            shelf.setFlow(shelf.LeftToRight)
            shelf.setWrapping(False)
            shelf.setDragEnabled(False)
            shelf.setSelectionMode(shelf.NoSelection)

            # Hook the shelf context menu
            shelf.customContextMenuRequested.connect(self.shelfContextMenu)
            
            # Hook book editor
            shelf.itemActivated.connect(self.widget.on_books_itemActivated)
            
            # Fill the shelf
            for b in grouped_books[k]:
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
        
