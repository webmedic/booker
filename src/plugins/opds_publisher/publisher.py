import os
import models
import bottle
import socket
import errno

from templite import Templite
from bottle import route, run, response
from multiprocessing import Queue

bottle.debug = True

_default_addr = 'localhost'
_default_port = 8080

queue = Queue()

def real_publish():
    # FIXME: move to another process or something
    
    app = bottle.default_app() # or bottle.app() since 0.7
    app.catchall = False
    @route('/')
    def index():
        """Creates a OPDS catalog from the book database"""
        template = Templite(TPL)
        books = []
        models.initDB()
        for book in models.Book.query.order_by("title").all():
            epub_fn = None
            pdf_fn = None
            mobi_fn = None
            exts = book.available_formats()
            print "EXTS:", exts
            if '.epub' in exts:
                epub_fn = "/book/%s.epub"%book.id
            if '.mobi' in exts:
                epub_fn = "/book/%s.mobi"%book.id
            if '.pdf' in exts:
                epub_fn = "/book/%s.pdf"%book.id

            books.append([
                book.title,
                book.id,
                u','.join([a.name for a in book.authors]),
                book.comments,
                epub_fn,
                pdf_fn,
                mobi_fn,
            ])
        response.content_type='application/atom+xml'
        return template.render(books = books)

    @route('/cover/:id')
    def cover(id):
        """Returns the cover of a book"""
        book = models.Book.get_by(id=int(id))
        fname = book.cover()
        f = open(fname).read()
        response.content_type='image/jpeg'
        return (f)

    @route('/book/:name')
    def book(name):
        """Returns the book matching name in id and type"""

        mimetypes = {
            ".pdf": "application/pdf",
            ".epub": "application/epub+zip",
            ".mobi": "application/x-mobipocket-ebook",
        }

        id,extension=os.path.splitext(name)
        book = models.Book.get_by(id=id)
        files = book.files_for_format(extension)
        fname = files[0]
        f = open(fname).read()
        # FIXME: use correct content-types
        response.content_type=mimetypes[extension]
        return (f)

    def get_bind_address ():
        """Get the configured network address and port
           to bind the HTTP server"""
        return (_default_addr, _default_port)

    def get_address ():
        """Returns a host:port tuple available for binding"""
        _host, _port = get_bind_address()
        for n in xrange(1,1024):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                sock.bind((_host, _port))
                sock.close()
                break
            except socket.error, e:
                sock.close()
                code, string = e
                if code == errno.EADDRINUSE:
                    # If the port is in use, try another one        
                    _port += 1
                else:
                    queue.put({'error': str(e)})
                    raise e
        return (_host, _port)

    def start ():
        """Starts the HTTP server
           It attempts to bind to the configured
           address and port, and if they're in use,
           it tries with another port"""
        try:
            (_host, _port) =  get_address()
        except Exception:
            return
        url = "http://%s:%d"%(_host, _port)
        print "Appending URL to queue: %s"%url
        queue.put({'url': url})
        run(host=_host, port=_port, quiet=True)
    start()
    
            
TPL = r"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:dc="http://purl.org/dc/terms/"
      xmlns:opds="http://opds-spec.org/2010/catalog">
  <id>urn:uuid:433a5d6a-0b8c-4933-af65-4ca4f02763eb</id>

  <link rel="self"
        href="/"
        type="application/atom+xml;type=feed;profile=opds-catalog"/>

  <title>Aranduka Catalog</title>
  <updated>2010-01-10T10:01:11Z</updated>
  <author>
    <name>Aranduka</name>
    <uri>http://aranduka.googlecode.com</uri>
  </author>

${ for book in books: }$
  <entry>
    <title>${book[0]}$</title>
    <id>${book[1]}$</id>
    <updated>2010-01-10T10:01:11Z</updated>
    <author>
      <name>${book[2]}$</name>
    </author>
    <summary>${book[3]}$</summary>
    <link type="image/png"
          rel="http://opds-spec.org/cover"
          href="/cover/${book[1]}$"/>
    <link type="image/gif"
          rel="http://opds-spec.org/thumbnail"
          href="/cover/${book[1]}$"/>

    ${
        if book[4]:
            emit('<link type="application/epub+zip" rel="http://opds-spec.org/acquisition" href="%s"/>'%book[4])
        if book[5]:
            emit('<link type="application/pdf" rel="http://opds-spec.org/acquisition" href="%s"/>'%book[5])
        if book[6]:
            emit('<link type="application/x-mobipocket-ebook" rel="http://opds-spec.org/acquisition" href="%s"/>'%book[6])
    }$
 </entry>
${:end-for}$

</feed>
"""


