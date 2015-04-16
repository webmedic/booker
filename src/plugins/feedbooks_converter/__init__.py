"""If a book is a feedbooks download, then this plugin will
"convert" the book to other formats by downloading them"""

from pluginmgr import Converter
import sys, os, urllib
from models import File, session

SUPPORTED = ['epub','pdf','mobi']

def extract_id (book):
    """Returns the book's feedbooks ID or None"""
    for i in book.identifiers:
        if i.key == "FEEDBOOKS_ID":
            return i.value
    return None

class FBConverter(Converter):

    name = "FeedBooks"

    def __init__(self):
        print "INIT: feedbooks_converter"

    def can_convert(self, book):
        """Given a book object, return the list of formats to
        which it can be converted"""
        i = extract_id(book)
        if i:
            return SUPPORTED
        else:
            return []

    def convert(self, book, dest_format):
        """Convert that book to that destination format"""
        # Get the file
        book_id = extract_id(book)
        url="http://www.feedbooks.com/book/%s.%s"%(book_id, dest_format)
        book.fetch_file(url, dest_format)
        
