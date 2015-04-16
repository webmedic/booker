import os
import zipfile

try:
    from elementtree.ElementTree import XML
except:
    from xml.etree.ElementTree import XML


class EpubDocument(object):
    """A class that parses and provides
    data about an ePub file"""

    def __init__(self, fname):
        # This is done according to this:
        # http://stackoverflow.com/questions/1388467/reading-epub-format

        print "Opening:", fname
        try:
            self.book = zipfile.ZipFile(fname, "r")
        except zipfile.BadZipfile:
            raise ValueError("Invalid format")

        f = self.book.open('META-INF/container.xml')
        self.container = XML(f.read())
        f.close()
        roots = self.container.findall(
                './/{urn:oasis:names:tc:opendocument:xmlns:container}rootfile')
        self.roots = []
        for r in roots:
            self.roots.append(r.attrib['full-path'])
        opf = self.book.open(self.roots[0])
        self.basepath = os.path.dirname(self.roots[0]) + "/"
        if self.basepath == '/':
            self.basepath = ""
        print "BASEPATH:", self.basepath

        data = opf.read()
        self.opf = XML(data)
        opf.close()
        self.manifest = self.opf.find('{http://www.idpf.org/2007/opf}manifest')
        self.manifest_dict = {}
        for elem in self.manifest.findall(
                            '{http://www.idpf.org/2007/opf}item'):
            self.manifest_dict[elem.attrib['id']] = self.basepath + \
                                                    elem.attrib['href']

        self.spine = self.opf.find('{http://www.idpf.org/2007/opf}spine')

        self.tocentries = []
        self.toc_id = self.spine.attrib.get('toc', None)
        if self.toc_id:
            self.toc_fn = self.manifest_dict[self.toc_id]
            print "TOC:", self.toc_fn
            f = self.book.open(self.toc_fn)
            data = f.read()
            self.toc = XML(data)
            self.navmap = self.toc.find(
                            '{http://www.daisy.org/z3986/2005/ncx/}navMap')
            # FIXME: support nested navpoints
            self.navpoints = self.navmap.findall(
                        './/{http://www.daisy.org/z3986/2005/ncx/}navPoint')
            for np in self.navpoints:
                label = np.find(
                    '{http://www.daisy.org/z3986/2005/ncx/}navLabel').find(
                            '{http://www.daisy.org/z3986/2005/ncx/}text').text
                content = np.find(
                 '{http://www.daisy.org/z3986/2005/ncx/}content').attrib['src']
                if label and content:
                    self.tocentries.append([label, content])

        self.itemrefs = self.spine.findall(
                                    '{http://www.idpf.org/2007/opf}itemref')
        print "IR:", self.itemrefs
        self.spinerefs = [
            self.manifest_dict[item.attrib['idref']][len(self.basepath):]
                                                    for item in self.itemrefs]
        # I found one book that has a spine but no navmap:
        # "Der schwarze Baal" from manybooks.net
        # Also another has more entries on the spine than on the navmap
        # (Dinosauria, from feedbooks).
        # So, we need to merge these suckers. I will assume it's not completely
        # insane and the spine is always more complete.

        spinerefs2 = [[x, x] for x in self.spinerefs]

        for te in self.tocentries:
            idx = self.spinerefs.index(te[1])
            spinerefs2[idx] = te

        self.tocentries = spinerefs2
        # if not self.tocentries:
            # # Alternative toc
            # self.tocentries = [[item.attrib['idref'],
             #self.manifest_dict[item.attrib['idref']][len(self.basepath):]]
                                                    #for item in self.itemrefs]

        print self.tocentries
        print self.spinerefs

    def getData(self, path):
        """Return the contents of a file in the document"""

        path = "%s%s" % (self.basepath, path)
        try:
            f = self.book.open(path)
        except KeyError:  # File missing in the zip
            return []
        data = f.read()
        f.close()
        return data
