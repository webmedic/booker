import os, sys, time, re
from PyQt4 import QtCore, QtGui, uic

import models
from pprint import pprint
from utils import VALID_EXTENSIONS
from pluginmgr import Importer
from progress import progress

COMPRESSED_EXTENSIONS = ['gz','bz2','lzma']

def clean_name (fname):
    "Clean a file name so it works better for a google query"
    fname = os.path.basename(fname)
    fname = fname.lower()
    fname = fname.replace('_',' ')
    splitted = fname.split('.')
    while splitted[-1] in VALID_EXTENSIONS+COMPRESSED_EXTENSIONS:
        splitted=splitted[:-1]
    fname = '.'.join(splitted)
    fname = fname.replace('.',' ')
    # FIXME: here we should use the system's encoding, but that's not
    # a sure thing to work, either.
    return fname.decode('latin1')

def import_file(fname):
    """Given a filename, tries to import it into
    the database with metadata from Google.

    Return value is as file_status
    """

    def try_import(fname, p):
        metadata=[]
        try:
            print "Fetching: ",p
            # The guessers go here
            # metadata = get_metadata(p) or []
            metadata = []
            print "Candidates:", [d.title for d in metadata]
            time.sleep(2)
        except Exception, e:
            print e
        for data in metadata:
            # Does it look valid?
            if data.title.lower() in p:
                # FIXME: should check by other identifier?
                b = models.Book.get_by(title = data.title)
                if not b:
                    # TODO: add more metadata
                    b = models.Book(
                        title = data.title,
                    )
                # Add Identifiers (ISBN, etc)
                for key, value in data.identifiers:
                    ident = models.Identifier.get_by(key=key,value=value)
                    if not ident:
                        ident = models.Identifier(key=key, value=value)
                    ident.book = b

                # Add Author(s)
                for name in data.authors:
                    author = models.Author.get_by(name=name)
                    if not author:
                        author = models.Author(name = name)
                        print "Added author: ", name
                    b.authors.append(author)

                # Fetch cover
                b.fetch_cover()
                
                print "Accepted: ", data.title
                f = models.File(file_name=fname, book=b)
                models.session.commit()
                return 1
        return 0

    # print fname
    # extension = fname.split('.')[-1].lower()
    # if extension in COMPRESSED_EXTENSIONS:
        # extension = fname.split('.')[-2].lower()
    # if extension not in VALID_EXTENSIONS:
        # print "Not an ebook: ", extension
        # return 
    # f = models.File.get_by(file_name = fname)
    # if f:
        # # Already imported
        # return file_status(fname)
        
    # # First try the clean name as-is
    p = clean_name(fname)
    # r1 = try_import(fname, u'TITLE '+p)
    # if r1:
        # return r1

    # # Try removing 'tags'
    # p2 = re.sub(u'[\(\[].*[\)\]]',' ',p)
    # r1 = try_import(fname, u'TITLE '+p2)
    # if r1:
        # return r1
    # # Try separating pieces
    # p3 = p2.replace(u'-',u' - ')
    # r1 = try_import(fname, u'TITLE '+p3)
    # if r1:
        # return r1

    # # Maybe it's author - title
    # l = p.split(u'-',1)
    # if len(l)==2:
    	# _, p4 = l
        # r1 = try_import(fname, u'TITLE '+p4)
        # if r1:
            # return r1
        
    # #TODO Keep trying in other ways
    
    print 'Importing as-is'
    b = models.Book.get_by(title = p)
    if not b:
        # TODO: add more metadata
        b = models.Book(
            title = p,
        )
        
    f = models.File(file_name=fname, book=b)
    models.session.commit()
    return 2

def file_status(fname):
    """Given a full path, it checks if it has been imported into
    the library.

    It returns:

    0 -- it has not been imported
    1 -- it has been imported and metadata has been added
    2 -- it has been imported but metadata seems insufficient
    """
    f = models.File.get_by(file_name = fname.decode('latin1'))
    if not f:
        return 0
    # FIXME really check that metadata is insufficient
    elif not f.book or f.book.title == clean_name(fname) and not f.book.authors:
        return 2
    return 1

class ImportFolder(Importer):
    def actions(self):
        self._action1 = QtGui.QAction("Folder", None)
        self._action1.triggered.connect(self.do_import_folder)
        self._action2 = QtGui.QAction("File", None)
        self._action2.triggered.connect(self.do_import_file)
        return [self._action1, self._action2]
    
    def do_import_folder(self):
        fname = unicode(QtGui.QFileDialog.getExistingDirectory(None, "Import Folder"))
        if not fname: return
        # Get a list of all files to be imported
        flist = []
        for data in os.walk(fname, followlinks = True):
            for f in data[2]:
                flist.append(os.path.join(data[0],f))
        for f in progress(flist, "Importing Files","Stop"):
            status = import_file(f)
            print status
            
    def do_import_file(self):
        fname = unicode(QtGui.QFileDialog.getOpenFileName(None, "Import File"))
        if not fname: return
        status = import_file(fname)
        print status
                        