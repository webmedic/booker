"""Plugin manager for Aranduka, using Yapsy"""

import utils
import config
import logging
logging.basicConfig(level=logging.DEBUG)

from PyQt4 import QtCore, QtGui
from yapsy.PluginManager import PluginManager


# These classes define our plugin categories
class Guesser(object):
    """These plugins take a filename and guess data from it.
    They can read the file itself, parse it and get data,
    or could look it up on the internet"""

    name = "Base Guesser"
    configurable = False

    def __init__(self):
        print "INIT: ", self.name

    def can_guess(self, book):
        """Given a book object, it will return True if it
        believes it can guess something.

        For example, a guesser that parses ePub files will only
        guess if the book has an ePub file assigned.
        """
        return False

    def guess(self, book):
        """Try to fill in as much metadata as possible,
        offer the user alternatives if needed.

        Returns an instance of Metadata, or None.
        """
        return None


class Device(object):
    """A plugin that represents a device to read books.
    These get added in the 'Devices' menu
    """
    configurable = False


class Tool(object):
    """A plugin that gets added to the Tools menu in the main.ui"""
    configurable = False


class Importer(object):
    """A plugin that gets added to the Tools menu in the main.ui"""
    configurable = False


class ShelfView(QtCore.QObject):
    """Plugins that inherit this class display the contents
    of your book database."""

    title = "Base ShelfView"
    itemText = "BASE"
    configurable = False

    def __init__(self):
        print "INIT: ", self.title
        self.widget = None
        QtCore.QObject.__init__(self)

    def setWidget(self, widget):
        self.widget = widget
        self.widget.updateShelves.connect(self.updateShelves)
        self.widget.updateBook.connect(self.updateBook)

    def treeItem(self):
        """Returns a QTreeWidgetItem representing this
        plugin"""
        return QtGui.QTreeWidgetItem([self.itemText])

    def showGrid(self, search=None):
        """Show a grid containing the (possibly filtered) books."""
        pass

    def showList(self, search=None):
        """Show a list containing the (possibly filtered) books."""
        pass

    def updateBook(self, book):
        """Update the item of this specific book, because
        it has been edited"""
        pass

    operate = showGrid

    def updateShelves(self):
        """Update the whole listing"""
        self.operate()

    @QtCore.pyqtSlot()
    def doSearch(self, *args):
        """Perform a search and display the results"""
        self.operate(search=unicode(self.widget.searchWidget.text.text()))

    def shelfContextMenu(self, point):
        """Show context menu for the book where the user
        right-clicked.
        If you are not using QListViews to display the
        books, you probably need to reimplement this"""

        shelf = self.sender()
        item = shelf.currentItem()
        book = item.book
        point = shelf.mapToGlobal(point)
        self.widget.bookContextMenuRequested(book, point)


class BookStore(QtCore.QObject):
    """Plugins that inherit this class give access to some
    mechanism for book acquisition"""

    title = "Base Bookstore"
    itemText = "BASE"
    configurable = False

    # These are signals the plugin uses to provide feedback
    # to the main UI
    loadStarted = QtCore.pyqtSignal()
    loadFinished = QtCore.pyqtSignal()
    loadProgress = QtCore.pyqtSignal("int")
    setStatusMessage = QtCore.pyqtSignal("PyQt_PyObject")

    def __init__(self):
        print "INIT:", self.title
        self.widget = None
        super(QtCore.QObject, self).__init__(None)

    def treeItem(self):
        """Returns a QTreeWidgetItem representing this
        plugin"""
        return QtGui.QTreeWidgetItem([self.itemText])

    def setWidget(self, widget):
        self.widget = widget

    @QtCore.pyqtSlot()
    def doSearch(self, *args):
        """Slot that triggers search on this store"""
        self.search(unicode(self.widget.searchWidget.text.text()))

    def search(self, key):
        """Search the store contents for this key, and display the results"""

    def showGrid(self):
        """Show contents in a grid, if applicable."""

    def showList(self):
        """Show contents in a list, if applicable."""


class Converter(object):
    configurable = False


def isPluginEnabled(name):
    enabled_plugins = set(config.getValue("general",
                                          "enabledPlugins",
                                          [None]))
    print "EP:", enabled_plugins
    if enabled_plugins == set([None]):
        print "FLAG"
        #Never configured... enable everything! (will change later ;-)
        enabled_plugins = set()
        for c in manager.getCategories():
            for p in manager.getPluginsOfCategory(c):
                enabled_plugins.add(p.name)
    return name in enabled_plugins

manager = PluginManager(
    categories_filter={
        "ShelfView": ShelfView,
        "BookStore": BookStore,
        "Converter": Converter,
        "Tool": Tool,
        "Importer": Importer,
        "Device": Device,
        "Guesser": Guesser,
    })

manager.setPluginPlaces(utils.PLUGINPATH)
