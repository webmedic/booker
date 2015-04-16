from feedparser import parse
from PyQt4 import QtGui, QtCore, QtWebKit, uic
import sys, os, urllib
from models import *
from pprint import pprint
from math import ceil
from pluginmgr import BookStore
import time
import codecs
import urlparse
from templite import Templite

try:
    from elementtree.ElementTree import XML
except:
    from xml.etree.ElementTree import XML

# This gets the main catalog from Archive.org.

EBOOK_EXTENSIONS=['epub','mobi','pdf']

class Catalog(BookStore):

    title = "Archive.org: Free and Public Domain Books"
    itemText = "Archive.org"
    
    def __init__(self):
        BookStore.__init__(self)
        self.w = None
        self.cover_cache={}

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
            self.openUrl(QtCore.QUrl('http://bookserver.archive.org/catalog/'))
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
        url = "http://bookserver.archive.org/catalog/opensearch?"+urllib.urlencode(dict(q=terms))
        self.crumbs=[self.crumbs[0],["Search: %s"%terms, url]]
        self.openUrl(QtCore.QUrl(url))

    def openUrl(self, url):
        print "CRUMBS:", self.crumbs
        if isinstance(url, QtCore.QUrl):
            url = url.toString()
        url = unicode(url)
        print "URL:", url
        if not url.startswith('http'):
            url=urlparse.urljoin('http://bookserver.archive.org/catalog/',url)
        extension = url.split('.')[-1]
        print "Opening:",url
        if extension in EBOOK_EXTENSIONS:
            # It's a book, get metadata, file and download
            meta_url = url[:-len(extension)-1]+'_meta.xml'
            data = urllib.urlopen(meta_url).read()
            root_elem = XML(data)
            title = root_elem.find('title').text
            authors = root_elem.findall('creator')
            book_id = root_elem.find('identifier').text
            tags = root_elem.find('subject')
            if tags:
                tags = tags.text.split(';')
            else:
                tags = []
            self.setStatusMessage.emit(u"Downloading: "+title)
            book = Book.get_by(title = title)
            if not book:
                _tags = []
                # FIXME: it doesn't work. No idea why.
                #for tag in tags:
                    #t = Tag.get_by(name = "subject", value = tag.strip())
                    #if not t:
                        #t = Tag(name = "subject", value = tag.strip())
                    #_tags.append(t)
                    #print _tags
                ident = Identifier(key="Archive.org_ID", value=book_id)
                a_list = []
                for a in authors:
                    name = a.text or ""
                    if not name:
                        continue
                    author = Author.get_by (name = name)
                    if not author:
                        author = Author(name = name)
                        a_list.append(author)
                book = Book (
                    title = title,
                    authors = a_list,
                    identifiers = [ident],
                    tags = _tags,
                )
            session.commit()
            
            # Get the file
            fname = os.path.abspath(os.path.join("ebooks", str(book.id) + '.' + extension))
            book.fetch_file(url, extension)
            cover_url = self.cover_cache.get(url,None)
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
       
    @QtCore.pyqtSlot()        
    def parseBranch(self):
        """Replaces the content of the web page (which is assumed to be
        an Atom feed from Archive.org) with the generated HTML.        
        """
        self.w.store_web.page().loadFinished.disconnect(self.parseBranch)
        url = unicode(self.w.store_web.page().mainFrame().requestedUrl().toString())
        print "Parsing the branch:", url
        t1 = time.time()
        data = parse(unicode(self.w.store_web.page().mainFrame().toHtml()).encode('utf-8'))

        title = data.feed.get('title',data.feed.get('subtitle','###'))
        
        if url.split('/')[-1].isdigit(): # It's a pageNumber
            pn = int(url.split('/')[-1])+1
            crumb = [title.split("books",1)[-1]+"[%d]"%pn, url]
            if self.crumbs[-1][1].split('/')[-1].isdigit(): # Don't show two numbered pages
                del(self.crumbs[-1])
        else:
            crumb = [title.split("-")[-1].strip(), url]
        try:
            r=self.crumbs.index(crumb)
            self.crumbs=self.crumbs[:r+1]
        except ValueError:
            self.crumbs.append(crumb)
        self.showCrumbs()

        self.cover_cache={}
        
        books = []
        links = []
        for entry in data.entries:
            # iurl = entry.links[0].href
            if entry.links[0].type == u'application/atom+xml':
                # A category
                links.append(entry)
            else: # A book
                books.append(entry)
                print entry

        nextPage = ''
        prevPage = ''
        for l in data.feed.get('links',[]):
            print "LINK:", l
            if l.rel == 'next':
                nextPage = '<a href="%s">Next Page</a>'%l.href
            elif l.rel == 'prev':
                prevPage = '<a href="%s">Previous Page</a>'%l.href

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
        
        # html='\n'.join(html)
        self.w.store_web.setHtml(html)
