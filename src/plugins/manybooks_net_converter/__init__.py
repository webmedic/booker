"""If a book is a manybooks.net download, then this plugin will
"convert" the book to other formats by downloading them"""

import urllib.request, urllib.parse, urllib.error
from pluginmgr import Converter

_FILE_FORMATS = {'ePub (.epub)': '1:epub:.epub:epub', \
                 'eReader (.pdb)': '1:pml:.pdb:pml', \
                 'FictionBook2 (.fb2)': '1:fb2:.fb2:fb2', \
                 'iPod Notes (.zip)': '1:ipod:.zip:ipod', \
                 'iSilo (.pdb)': '1:isiloX:.pdb:isiloX', \
                 'Kindle (.awz)': '1:kindle:.azw:kindle', \
                 'Mobipocket (.mobi)': '1:mobi2:.mobi:mobi2', \
                 'Mobipocket (.prc)': '1:mobi:.prc:mobi', \
                 'MS lit (slow) (.lit)': '1:lit:.lit:lit', \
                 'PalmDOC (.pdb)': '1:doc:.pdb:doc', \
                 'PDF (.pdf)': '1:pdf:.pdf:pdf', \
                 'PDF Large Print (.pdf)': '1:pdfLRG:.pdf:pdfLRG', \
                 'Plucker (.pdb)': '1:plkr:.pdb:plkr', \
                 'Rocketbook (.rb)': '1:rbk:.rb:rbk', \
                 'RTF (.rtf)': '1:rtf:.rtf:rtf', \
                 'Sony Reader (.lrf)': '1:librie:.lrf:librie', \
                 'TCR (.tcr)': '1:tcr:.tcr:tcr', \
                 'zTXT (.pdb)': '1:wr:.pdb:w', \
                 'JAR file': 'mnybksjar'}

_SERVICE_URL = 'http://manybooks.net/send'

SUPPORTED = sorted(_FILE_FORMATS.keys())

def extract_id (book):
    """Returns the book's ManyBooks.net ID or None"""
    for i in book.identifiers:
        if i.key == "ManyBooks.net_TID":
            return i.value
    return None

class ManyBooksNetConverter(Converter):

    name = "ManyBooksNetConverter"

    def __init__(self):
        print("INIT: manybooks_net_converter")

    def can_convert(self, book):
        """Given a book object, return the list of formats to
        which it can be converted"""
        i = extract_id(book)
        if i:
            return SUPPORTED
        else:
            return []

    def _get_extension (self, file_format):
        if _FILE_FORMATS[file_format] == 'mnybksjar':
            return '.jar'
        else:
            return _FILE_FORMATS[file_format].split(':')[2]

    def _get_file_url (self, book_id, file_format):
        if file_format not in SUPPORTED:
            return
        return "%s/%s/%s/%s%s"%(_SERVICE_URL, \
                                 urllib.parse.quote_plus(_FILE_FORMATS[file_format]), \
                                 book_id, \
                                 book_id, \
                                 self._get_extension(file_format))

    def convert(self, book, dest_format):
        """Convert that book to that destination format"""
        # Get the file
        book_id = extract_id(book)
        url = self._get_file_url(book_id, dest_format)
        book.fetch_file(url, self._get_extension(dest_format)[1:])
