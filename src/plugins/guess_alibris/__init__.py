# -*- coding: utf-8 -*-
"""
Alibris Book Guesser

This plugin allows you to search for a book's information
using Alibris' API 

More information about the API:
http://developer.alibris.com/docs
"""
import datetime
import urllib2
import json
from urllib import urlencode
from pluginmgr import Guesser
from metadata import BookMetadata

# Base URL for Alibris' Search Method
__baseurl__ = 'http://api.alibris.com/v1/public/search?'

# Alibris API Key
__apikey__ = '9q3rk555cg4aqttx6tyehwuk'

class AlibrisGuesser(Guesser):
    name = "Alibris"

    def can_guess(self, book):
        return True

    def _translateQuery (self, query):
        q = []
        if query.title is not None:
            q.append(('qtit', query.title.encode('utf-8')))
        if query.authors is not None:
            q.append(('qauth', query.authors.encode('utf-8')))
        if query.identifiers[0] is not None:
            q.append(('qisbn', query.identifiers[0].encode('utf-8')))
        return q

    def _get_url (self, query):
        query = self._translateQuery(query)
        url = __baseurl__
        url += 'outputtype=json&'
        url += urlencode(query)
        url += '&apikey=%s' % __apikey__
        return url

    def search (self, query):
        """Implements Alibris' Search Method to retrieve the
           information of a book.

           More info on this method:
           http://developer.alibris.com/docs/read/Search_Method

           JSON Response example:
           http://developer.alibris.com/files/json-freakonomics.txt.
        """
        data = urllib2.urlopen(self._get_url(query)).read()
        return json.loads(data)

    def guess(self, query):
        md = self.search(query)
        if 'status' in md \
            and md['status'] == '0': 
            if 'book' in md:
                bookList = []
                _isbn = []
                for book in md['book']:
                    if 'isbn' in book and book['isbn'] in _isbn:
                        continue
                    title = book.get('title', 'No Title')
                    thumbnail = book.get('imageurl','')
                    date = datetime.date(1970,1,1)
                    subjects = []
                    authors = []
                    identifiers = []
                    description = ''

                    if 'keywords' in book and book['keywords'] != '':
                        subjects = [book['keywords']] # FIXME: Check which token use to split this

                    if 'author' in book and book['author'] != '':
                        authors = [book['author']] # FIXME: Check which token use to split this
                    
                    if 'isbn' in book and book['isbn'] != '':
                        _isbn.append(book['isbn'])
                        identifiers.append(('ISBN', book['isbn']))

                    if 'bin' in book and book['bin'] != '':
                        identifiers.append(('alibris_sku', book['bin']))

                    bookList.append(BookMetadata(title=title,
                                                 thumbnail=thumbnail,
                                                 date=date,
                                                 subjects=subjects,
                                                 authors=authors,
                                                 identifiers=identifiers,
                                                 description=description))
                return bookList        
            else:
                return None
        else:
            raise Exception("Failed to load Alibris")
