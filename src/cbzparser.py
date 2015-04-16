import zipfile


class CBZDocument(object):
    """A class that parses and provides
    data about a CBZ file"""

    def __init__(self, fname):

        print "Opening:", fname
        try:
            self.book = zipfile.ZipFile(fname, "r")
        except zipfile.BadZipfile:
            raise ValueError("Invalid format")

        self.tocentries = self.book.namelist()
        self.tocentries.sort()

    def getData(self, path):
        """Return the contents of a file in the document"""

        print "GD:", path
        try:
            f = self.book.open(path)
        except KeyError:  # File missing in the zip
            return []
        data = f.read()
        f.close()
        return data
