import os, sys, codecs
from feedparser import parse
from templite import Templite
import tempfile, zipfile
from xml.sax.saxutils import escape

class RSS2ePub(object):

    def load_template (self, name):
        f = codecs.open(os.path.join(
            os.path.abspath(
            os.path.dirname(__file__)),name),
                'r', 'utf-8')
        tpl = Templite(f.read())
        f.close()
        return tpl

    def save_file(self, name, data):
        fn = os.path.join(self.tempdir,name)
        f=codecs.open(fn, 'w+','utf-8')
        f.write(data)
        f.close()
        self.epub.write(fn, name)
        
    def convert(self, url, output):
        self.tempdir = tempfile.mkdtemp()
        data = parse(url)
        self.epub = zipfile.ZipFile(output, 'w')


        # The HTML index page
        feedtmpl = self.load_template('feed.tmpl')
        self.save_file('out.html',feedtmpl.render(feed=data.feed, posts = data.entries))
        

        # The toc.ncx
        toctmpl = self.load_template('toc_ncx.tmpl')
        self.save_file('toc.ncx', toctmpl.render(feed=data.feed, posts = data.entries, escape = escape))

        # The title page
        titletmpl = self.load_template('titlepage.tmpl')
        self.save_file('titlepage.xhtml', titletmpl.render(feed=data.feed))

        # content.opf
        opftmpl = self.load_template('content_opf.tmpl')
        self.save_file('content.opf', opftmpl.render(feed=data.feed, posts = data.entries))


        # Individual HTML files for each post
        posttmpl = self.load_template('post.tmpl')
        for i, post in enumerate(data.entries):
            self.save_file('%s.html'%i, posttmpl.render(post = post))

        # Static files
        for sf, df in [
            ['container.xml', 'META-INF/container.xml'],
            ['screen.css', 'screen.css'],
            ['style.css', 'style.css'],
            ['cover_image.jpg', 'cover_image.jpg'],
            ['images/icons/external.png','images/icons/external.png'],
            ['images/icons/doc.png','images/icons/doc.png'],
            ['images/icons/pdf.png','images/icons/pdf.png'],
            ['images/icons/visited.png','images/icons/visited.png'],
            ['images/icons/im.png','images/icons/im.png'],
            ['images/icons/email.png','images/icons/email.png'],
            ['images/icons/information.png','images/icons/information.png'],
            ['images/icons/tick.png','images/icons/tick.png'],
            ['images/icons/cross.png','images/icons/cross.png'],
            ['images/icons/key.png','images/icons/key.png'],
            ['images/icons/feed.png','images/icons/feed.png'],
            ['images/icons/xls.png','images/icons/xls.png'],
            ]:

            self.epub.write(os.path.join(
                os.path.abspath(
                os.path.dirname(__file__)),sf),df)
        self.epub.close

if __name__ == "__main__":
    RSS2ePub().convert('http://lateral.netmanagers.com.ar/weblog/rss.xml','lateral.epub')
