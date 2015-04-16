from feedparser import parse
from PyQt4 import QtGui, QtCore, QtWebKit, uic
import sys, os, urllib
from models import *
from pprint import pprint
from math import ceil
from pluginmgr import BookStore
from templite import Templite
import codecs
import urlparse
import time

# This gets the main catalog from feedbooks.

EBOOK_EXTENSIONS=['epub','mobi','pdf']

class Catalog(BookStore):

    title = "FeedBooks: Free and Public Domain Books"
    itemText = "FeedBooks.com"
    def __init__(self):
        BookStore.__init__(self)
        self.w = None
        
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
            self.openUrl(QtCore.QUrl('http://www.feedbooks.com/catalog.atom'))
            self.w.store_web.page().setLinkDelegationPolicy(QtWebKit.QWebPage.DelegateExternalLinks)
            self.w.store_web.page().linkClicked.connect(self.openUrl)
            self.w.crumbs.linkActivated.connect(self.openUrl)
            self.w.store_web.loadStarted.connect(self.loadStarted)
            self.w.store_web.loadProgress.connect(self.loadProgress)
            self.w.store_web.loadFinished.connect(self.loadFinished)
        self.widget.stack.setCurrentIndex(self.pageNumber)

    showGrid = operate
    showList = operate
            
    def search (self, terms):
        url = "http://www.feedbooks.com/search.atom?"+urllib.urlencode(dict(query=terms))
        self.crumbs=[self.crumbs[0],["Search: %s"%terms, url]]
        self.openUrl(QtCore.QUrl(url))

    def openUrl(self, url):
        if isinstance(url, QtCore.QUrl):
            url = url.toString()
        url = unicode(url)
        # This happens for catalogs by language
        if url.startswith('/'):
            url=urlparse.urljoin('http://feedbooks.com',url)
        extension = url.split('.')[-1]
        print "Opening:",url
        if url.split('/')[-1].isdigit() or url.split('/')[-2].isdigit():
            # A details page
            crumb = ["#%s"%url.split('/')[-1],url]
            if crumb in self.crumbs:
                self.crumbs = self.crumbs[:self.crumbs.index(crumb)+1]
            else:
                self.crumbs.append(crumb)
            self.showCrumbs()
            self.w.store_web.load(QtCore.QUrl(url))
        elif extension in EBOOK_EXTENSIONS:
            # It's a book, get metadata, file and download
            book_id = url.split('/')[-1].split('.')[0]
            bookdata = parse("http://www.feedbooks.com/book/%s.atom"%book_id)
            if bookdata.status == 404:
                bookdata = parse("http://www.feedbooks.com/userbook/%s.atom"%book_id)
                
            bookdata = bookdata.entries[0]
            title = bookdata.title
            self.setStatusMessage.emit(u"Downloading: "+title)
            book = Book.get_by(title = title)
            if not book:
                # Let's create a lot of data
                tags = []
                for tag in bookdata.get('tags',[]):
                    t = Tag.get_by(name = tag.label)
                    if not t:
                        t = Tag(name = tag.label)
                    tags.append(t)
                ident = Identifier(key="FEEDBOOKS_ID", value=book_id)
                author = Author.get_by (name = bookdata.author)
                if not author:
                    author = Author(name = bookdata.author)
                book = Book (
                    title = title,
                    authors = [author],
                    tags = tags,
                    identifiers = [ident]
                )
            session.commit()
            
            # Get the file
            book.fetch_file(url, extension)
            book.fetch_cover("http://www.feedbooks.com/book/%s.jpg"%book_id)
            
        else:
            self.showBranch(url)

    def showCrumbs(self):
        ctext = []
        for c in self.crumbs:
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
        
    @QtCore.pyqtSlot()
    def parseBranch(self):
        """Replaces the content of the web page (which is assumed to be
        an Atom feed from Feedbooks) with the generated HTML.        
        """
        self.w.store_web.page().loadFinished.disconnect(self.parseBranch)
        url = unicode(self.w.store_web.page().mainFrame().requestedUrl().toString())
        print "Parsing the branch:", url
        t1 = time.time()
        data = parse(unicode(self.w.store_web.page().mainFrame().toHtml()).encode('utf-8'))
        print "Parsed branch in: %s seconds"%(time.time()-t1)
        title = data.feed.get('title','')
        if 'page=' in url: # A page
            print "DELETING LAST CRUMB" 
            if 'page=' in self.crumbs[-1][1]: 
                #last one was also a page
                del self.crumbs[-1]
        if title:
            crumb = [title.split("|")[0].split("/")[-1].strip(), url]
            try:
                r=self.crumbs.index(crumb)
                self.crumbs=self.crumbs[:r+1]
            except ValueError:
                self.crumbs.append(crumb)
        self.showCrumbs()
        books = []
        links = []        
        for entry in data.entries:
            # Find acquisition links
            acq_links = [l.href for l in entry.links if l.rel=='http://opds-spec.org/acquisition']

            if acq_links: # Can be acquired
                books.append(entry)
            else:
                links.append(entry)

        totPages = int(ceil(float(data.feed.get('opensearch_totalresults', 1))/int(data.feed.get('opensearch_itemsperpage', 1))))
        curPage = int(urlparse.parse_qs(urlparse.urlparse(url).query).get('page',[1])[-1])
        
        t1 = time.time()
        html = self.template.render(
            title = title,
            books = books,
            links = links,
            url = url,
            totPages = totPages,
            curPage = int(curPage)
            )
        print "Rendered in: %s seconds"%(time.time()-t1)
        # open('x.html','w+').write(html)
        self.w.store_web.page().mainFrame().setHtml(html)
        self.w.store_web.setUpdatesEnabled(True)
