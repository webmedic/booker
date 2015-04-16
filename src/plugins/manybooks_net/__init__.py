from feedparser import parse
from PyQt4 import QtGui, QtCore, QtWebKit, uic
import sys, os, urllib
from models import *
from pprint import pprint
from math import ceil
from pluginmgr import BookStore
import codecs
import time
from templite import Templite
import urlparse

# This gets the main catalog from ManyBooks.net.

EBOOK_EXTENSIONS=['epub', \
                 'pdb', \
                 'fb2', \
                 'zip', \
                 'azw', \
                 'mobi', \
                 'prc', \
                 'lit', \
                 'pdf', \
                 'rb', \
                 'rtf', \
                 'lrf', \
                 'tcr', \
                 'jar']
_FILE_FORMATS = ['1:epub:.epub:epub', \
                 '1:pml:.pdb:pml', \
                 '1:fb2:.fb2:fb2', \
                 '1:ipod:.zip:ipod', \
                 '1:isiloX:.pdb:isiloX', \
                 '1:kindle:.azw:kindle', \
                 '1:mobi2:.mobi:mobi2', \
                 '1:mobi:.prc:mobi', \
                 '1:lit:.lit:lit', \
                 '1:doc:.pdb:doc', \
                 '1:pdf:.pdf:pdf', \
                 '1:plkr:.pdb:plkr', \
                 '1:rbk:.rb:rbk', \
                 '1:rtf:.rtf:rtf', \
                 '1:librie:.lrf:librie', \
                 '1:tcr:.tcr:tcr', \
                 '1:wr:.pdb:w', \
                 'mnybksjar']

class Catalog(BookStore):

    title = "ManyBooks.net: Free and Public Domain Books"
    itemText = "ManyBooks.net"
    
    def __init__(self):
        print "INIT: ManyBooks.net"
        BookStore.__init__(self)
        self.widget = None
        self.w = None
        self.cache = {}
       
    def setWidget (self, widget):
        tplfile = os.path.join(
            os.path.abspath(
                os.path.dirname(__file__)),'category.tmpl')

        tplfile = codecs.open(tplfile,'r','utf-8')
        self.template = Templite(tplfile.read())
        tplfile.close()
        self.widget = widget

    def operate(self):
        "Show the store"
        if not self.widget:
            print "Call setWidget first"
            return
        self.widget.title.setText(self.title)
        if not self.w:
            uifile = os.path.join(
                os.path.abspath(
                    os.path.dirname(__file__)),'store.ui')
            self.w = uic.loadUi(uifile)
            self.pageNumber = self.widget.stack.addWidget(self.w)
            self.crumbs=[]
            self.openUrl(QtCore.QUrl('http://manybooks.net/opds/'))
            self.w.store_web.page().setLinkDelegationPolicy(QtWebKit.QWebPage.DelegateExternalLinks)
            self.w.store_web.page().linkClicked.connect(self.openUrl)
            self.w.crumbs.linkActivated.connect(self.openUrl)
            self.w.store_web.loadStarted.connect(self.loadStarted)
            self.w.store_web.loadProgress.connect(self.loadProgress)
            self.w.store_web.loadFinished.connect(self.loadFinished)
            self.w.store_web.page().mainFrame().javaScriptWindowObjectCleared.connect(self.addJSObject)
           
        self.widget.stack.setCurrentIndex(self.pageNumber)
        
    showGrid = operate
    showList = operate

    def addJSObject(self):
        print "DEBUG: JS Window Object Cleared"
        self.w.store_web.page().mainFrame().addToJavaScriptWindowObject(QtCore.QString('catalog'), self)
        
    def search (self, terms):
        url = "http://manybooks.net/opds/search.php?"+urllib.urlencode(dict(q=terms))
        self.crumbs=[self.crumbs[0],["Search: %s"%terms, url]]
        self.openUrl(QtCore.QUrl(url))

    @QtCore.pyqtSlot(QtCore.QString)
    @QtCore.pyqtSlot(QtCore.QUrl)    
    def openUrl(self, url):
        print "openURL:", url
        if isinstance(url, QtCore.QUrl):
            url = url.toString()
        url = unicode(url)
        if not url.startswith('http'):
            url=urlparse.urljoin('http://manybooks.net/opds/',url)        
        extension = url.split('.')[-1]
        if extension in EBOOK_EXTENSIONS:
            # It's a book, get metadata, file and download
            # Metadata is cached
            cache = self.cache[self.get_url_key(url)]
            title = cache['title']
            _author = cache['author']
            book_id = cache['id']
            cover_url = cache['cover'][0]
            self.setStatusMessage.emit(u"Downloading: "+title)
            book = Book.get_by(title = title)
            book_tid = url.split('/')[-2]
            if not book:
                ident_urn = Identifier(key="ManyBooks.net_ID", value=book_id)
                ident_tid = Identifier(key="ManyBooks.net_TID", value=book_tid)
                author = Author.get_by (name = _author)
                if not author:
                    author = Author(name = _author)
                book = Book (
                    title = title,
                    authors = [author],
                    identifiers = [ident_urn, ident_tid],
                )
            session.commit()
            
            # Get the file
            fname = os.path.abspath(os.path.join("ebooks", str(book.id) + '.' + extension))
            book.fetch_file(url, extension)
            if cover_url:
                book.fetch_cover(cover_url)
            
        else:
            self.showBranch(url)

    def showCrumbs(self):
        ctext = []
        for c in self.crumbs[-4:]:
            ctext.append('<a href="%s">%s</a>'%(c[1],c[0]))
        ctext = "&nbsp;>&nbsp;".join(ctext)
        self.w.crumbs.setText(ctext)

    def showBranch(self, url):
        """Trigger download of the branch, then trigger
        parseBranch when it's downloaded"""
        print "Showing:", url
        # Disable updates to prevent flickering
        self.w.store_web.setUpdatesEnabled(False)
        self.w.store_web.page().mainFrame().load(QtCore.QUrl(url))
        self.setStatusMessage.emit(u"Loading: "+url)
        self.w.store_web.page().loadFinished.connect(self.parseBranch)
        return

    def _generate_links (self, epub_url):
        """Takes the link for an epub file and returns the list
           of links to download the ebook in all the formats that
           are supported by ManyBooks.net"""
        links = []
        book_tid = epub_url.split('/')[-2]
        for fmt in _FILE_FORMATS:
            if fmt == 'mnybksjar':
                ext = '.jar'
            else:
                ext = fmt.split(':')[2]
            links.append(u'http://manybooks.net/send/%s/%s/%s%s' % \
                         (fmt, book_tid, book_tid, ext))
        return links
        
    @QtCore.pyqtSlot()
    def parseBranch(self):
        """Replaces the content of the web page (which is assumed to be
        an Atom feed from ManyBooks) with the generated HTML.        
        """
        self.w.store_web.page().loadFinished.disconnect(self.parseBranch)
        url = unicode(self.w.store_web.page().mainFrame().requestedUrl().toString())
        print "Parsing the branch:", url
        t1 = time.time()
        data = parse(unicode(self.w.store_web.page().mainFrame().toHtml()).encode('utf-8'))
        if not data.entries:
            QtGui.QMessageBox.critical(None, \
                                      u'Failed to load ManyBooks.net', \
                                      u'An error ocurred and the ManyBooks.net catalog could not be loaded.')
        nextPage = ''
        prevPage = ''
        for l in data.feed.get('links',[]):
            print "LINK:", l
            if l.rel == 'next':
                nextPage = '<a href="%s">Next Page</a>'%l.href
            elif l.rel == 'prev':
                prevPage = '<a href="%s">Previous Page</a>'%l.href
        
        title = data.feed.get('title',data.feed.get('subtitle','###'))
        if '?n=' in url: # It's paginated
            pnum = int(url.split('=')[-1])/10+1
            title = title+'(%s)'%pnum
            if '?n=' in self.crumbs[-1][1]:
                # Don't show two numbered pages in a row
                del(self.crumbs[-1])
            
        crumb = [title, url]
        if crumb in self.crumbs:
            self.crumbs = self.crumbs[:self.crumbs.index(crumb)+1]
        else:
            self.crumbs.append(crumb)
        self.showCrumbs()

        # FIXME: this leaks memory forever (not very much, though)
        # REVIEW: I don't know where the leak was, but maybe my latest
        #         change helped (or not).
        self.cache = {}
        
        books = []
        links = []        
        for entry in data.entries:
            # Find acquisition links
            acq_links = [l.href for l in entry.get('links',[]) if l.rel=='http://opds-spec.org/acquisition']

            if acq_links:
                cover_url = [l.href for l in entry.links if l.rel==u'http://opds-spec.org/cover']
                if cover_url:
                    entry.cover_url = cover_url[0]
                if len(acq_links) == 1:
                    entry.links = self._generate_links(acq_links[0])
                # A book
                books.append(entry)
                for href in acq_links:
                    key = self.get_url_key(href)
                    self.cache[key] = { \
                        'cover': cover_url, \
                        'id': entry.get('id'), \
                        'author': entry.author, \
                        'title': entry.title \
                    }
            else:
                # A category
                links.append(entry)
                
        t1 = time.time()
        html = self.template.render(
            title = title,
            books = books,
            links = links,
            url = url,
            nextPage = nextPage,
            prevPage = prevPage
            )
        print "Rendered in: %s seconds"%(time.time()-t1)
        # open('x.html','w+').write(html)        
        self.w.store_web.setHtml(html)
        self.w.store_web.setUpdatesEnabled(True)

    def get_url_key (self, url):
        """Takes a book URL and extracts the product key"""
        return url.split('/')[-1].split('.')[0]

    def on_catalog_itemExpanded(self, item):
        if item.childCount()==0:
            self.addBranch(item, item.url)

    def on_catalog_itemActivated(self, item, column):
        url=item.url
        if url.split('/')[-1].isdigit():
            # It's a book
            self.web.load(QtCore.QUrl(url))
