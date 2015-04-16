#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import urllib2
import ui

from PyQt4 import QtCore, QtGui, uic

import models
from utils import validate_ISBN, SCRIPTPATH
from metadata import BookMetadata
from pluginmgr import manager, isPluginEnabled

from templite import Templite
import time


class IdentifierDialog(QtGui.QDialog):

    def __init__(self, id_key, id_value, *args):
        QtGui.QDialog.__init__(self, *args)
        uifile = ui.path('identifier.ui')
        uic.loadUi(uifile, self)
        self.ui = self
        self._query = None
        self.id_key.setText(id_key)
        self.id_value.setText(id_value)


class TagDialog(QtGui.QDialog):

    def __init__(self, tag_name, *args):
        QtGui.QDialog.__init__(self, *args)
        uifile = ui.path('tag.ui')
        uic.loadUi(uifile, self)
        self.ui = self
        self._query = None
        for t in models.Tag.query.all():
            self.tag_name.addItem(t.name, t.name)
        self.tag_name.setEditText(tag_name)


class GuessDialog(QtGui.QDialog):

    def __init__(self, book, *args):
        QtGui.QDialog.__init__(self, *args)
        uifile = ui.path('guess.ui')
        uic.loadUi(uifile, self)
        self.ui = self
        self.setWindowTitle('Guess book information')
        self._query = None
        self.md = []
        self.currentMD = None
        self.book = book
        self.titleText.setText(book.title or "")
        self.authorText.setText((u', '.join([a.name for a in book.authors])
                                 or ""))
        ident = models.Identifier.get_by(key='ISBN', book=book)
        if ident:
            self.isbnText.setText(ident.value)
            self._isbn = ident.value
        else:
            self.isbn.hide()
            self.isbnText.hide()

        self.candidates.page().setLinkDelegationPolicy(
                                    self.candidates.page().DelegateAllLinks)
        self.candidates.linkClicked.connect(self.updateWithCandidate)

        self.guesser_dict = {}
        self.guessers.clear()
        # Fill the guessers combo with appropiate names
        for plugin in manager.getPluginsOfCategory("Guesser"):
            if isPluginEnabled(plugin.name) and \
               plugin.plugin_object.can_guess(self.book):
                self.guesser_dict[unicode(plugin.plugin_object.name)] = \
                                                           plugin.plugin_object
                self.guessers.addItem(plugin.plugin_object.name)
        self.guesser = self.guesser_dict[unicode(self.guessers.currentText())]

    @QtCore.pyqtSlot("QString")
    def on_guessers_currentIndexChanged(self, text):
        self.guesser = self.guesser_dict[unicode(text)]

    @QtCore.pyqtSlot()
    def on_guessButton_clicked(self):
        # Try to guess based on the reliable data
        query = {'title': None,
                 'authors': None,
                 'isbn': None}
        # self.bookList.clear()
        if self.title.isChecked():
            query['title'] = unicode(self.titleText.text())
        if self.author.isChecked():
            query['authors'] = unicode(self.authorText.text())
        if self.isbn.isChecked():
            query['isbn'] = unicode(self.isbnText.text())

        if query['title'] is None and \
           query['authors'] is None and \
           query['isbn'] is None:
            QtGui.QMessageBox.warning(self,
                                      u'Select something to search',
                                      u'You need to select at least one '
                                       'field to search')
            return

        self._query = BookMetadata(title=query['title'],
                                   thumbnail=None,
                                   date=None,
                                   subjects=None,
                                   authors=query['authors'],
                                   identifiers=[query['isbn']],
                                   description=None)
        if self._query:
            try:
                print self.guesser, type(self.guesser)
                self.md = self.guesser.guess(self._query) or []
            except Exception, e:
                print "Guesser exception: %s" % str(e)
                QtGui.QMessageBox.warning(self,
                                          u'Failed to load data',
                                          str(e))
                return

            if self.md:

                tpl = u"""
<html>
<body>
${for i,candidate in enumerate(md):}$
${
    title = candidate.title
    thumb = candidate.thumbnail
    authors = candidate.authors
    if isinstance(authors, list):
        authors = u', '.join(authors)
    identifiers = candidate.identifiers

}$
<div style="min-height: 128px;
            border: solid 3px lightgrey;
            padding: 15px;
            border-radius: 15px;
            margin: 6px;
            -webkit-transition: all 500ms linear;"
     onmouseover="this.style.border='solid 3px lightgreen';
                  this.style.backgroundColor='lightgreen';
                  document.getElementById('submit-${i}$').style.opacity=1.0;"
     onmouseout="this.style.border='solid 3px lightgrey';
                 this.style.backgroundColor='white';
                 document.getElementById('submit-${i}$').style.opacity=0;">

    <img width="64px" style="float: left; margin-right: 4px;" src="${thumb}$">
    <div style="text-align: right; margin-top: 12px;">
    <b>${title}$</b><br>
    by ${authors}$<br>
    ${for identifier in identifiers:}$
        <small>${identifier[0]}$:${identifier[1]}$</small><br>
    ${:end-for}$
    <a href="/${i}$/" id="submit-${i}$" >Update</a>
    </form>
    </div>
</div>
${:end-for}$
"""
                self.template = Templite(tpl)
                t1 = time.time()
                html = self.template.render(md=self.md)
                print "Rendered in: %s seconds" % (time.time() - t1)
                self.candidates.page().mainFrame().setHtml(html)

            else:
                self.candidates.page().mainFrame().setHtml(
                    u"<h3>No matches found for the selected criteria</h3>")

    def updateWithCandidate(self, url):
        cId = int(url.path()[1:-1])
        self.currentMD = self.md[cId]
        self.accept()


class BookEditor(QtGui.QWidget):

    updateBook = QtCore.pyqtSignal(models.Book)

    def __init__(self, book_id=None, *args):
        QtGui.QWidget.__init__(self, *args)
        uifile = ui.path('book_editor.ui')
        uic.loadUi(uifile, self)
        self.ui = self
        # This flag will keep track of unsaved changes
        self.unsaved = False
        if book_id is not None:
            self.load_data(book_id)

    def load_data(self, book_id):
        self.book = models.Book.get_by(id=book_id)
        if not self.book:
            # Called with invalid book ID
            print "Wrong book ID"
        self.title.setText(self.book.title)
        self.authors.setText('|'.join([a.name for a in self.book.authors]))
        if self.book.comments:
            self.description.setPlainText(unicode(self.book.comments))
        else:
            self.description.setPlainText("")
        self.ids.clear()
        for i in self.book.identifiers:
            self.ids.addItem("%s: %s" % (i.key, i.value))

        self.fileList.clear()
        for f in self.book.files:
            self.fileList.addItem(f.file_name)

        self.tags.clear()
        for t in self.book.tags:
            self.tags.addItem(t.name)

        cname = self.book.cover()
        self.cover.setPixmap(
            QtGui.QPixmap(cname).scaledToHeight(200,
                                            QtCore.Qt.SmoothTransformation))
        # This is to make sure that loading data is not
        # considered a change (i.e., this happens with QPlainTextEdit)
        self.unsaved = False

    def is_saved(self, parent=None):
        if self.unsaved:
            print "There is unsaved data..."
            parent = parent if parent is not None else self
            msgBox = QtGui.QMessageBox(parent)
            msgBox.setWindowTitle('Save changes?')
            msgBox.setText('This book has been modified.')
            msgBox.setInformativeText('Do you want to save your changes?')
            msgBox.setStandardButtons(QtGui.QMessageBox.Save |
                                      QtGui.QMessageBox.Discard |
                                      QtGui.QMessageBox.Cancel)
            msgBox.setDefaultButton(QtGui.QMessageBox.Save)
            msgBox.setWindowModality(QtCore.Qt.ApplicationModal)
            msgBox.setFocus()
            reply = msgBox.exec_()
            if reply == QtGui.QMessageBox.Save:
                self.on_save_clicked()
            elif reply == QtGui.QMessageBox.Discard:
                self.on_cancel_clicked()
            else:
                return False
        else:
            print "No unsaved data. Accepting event..."
        return True

    def on_title_textEdited(self, string):
        self.unsaved = True

    def on_authors_textEdited(self, string):
        self.unsaved = True

    def on_description_textChanged(self):
        self.unsaved = True

    def on_cancel_clicked(self):
        # Discard unsaved changes if the user presses
        # the Cancel button
        self.unsaved = False

    @QtCore.pyqtSlot()
    def on_guess_clicked(self):

        # Display the Guess Dialog
        dlg = GuessDialog(self.book)
        r = dlg.exec_()
        if not r == dlg.Accepted:
            md = None
        elif dlg.currentMD:
            md = dlg.currentMD

        if md is None:
            return
        else:
            # A candidate was chosen, update data
            self.title.setText(md.title)
            self.authors.setText('|'.join(md.authors))
            # FIXME: maybe there are identifier conflicts?
            items = [unicode(self.ids.itemText(i))
                                for i in range(self.ids.count())]
            if md.identifiers is not None:
                for k, v in md.identifiers:
                    items.append("%s: %s" % (k, v))
            items = list(set(items))
            items.sort()
            self.ids.clear()
            self.ids.addItems(items)
            self.on_save_clicked()
            self.load_data(self.book.id)
            self.book.fetch_cover()
            self.load_data(self.book.id)

    @QtCore.pyqtSlot()
    def on_save_clicked(self):
        # Save the data first
        self.book.title = unicode(self.title.text())
        self.book.comments = unicode(self.description.toPlainText())

        self.book.authors = []
        authors = unicode(self.authors.text()).split('|')
        for a in authors:
            author = models.Author.get_by(name=a)
            if not author:
                print "Creating author:", a
                author = models.Author(name=a)
            self.book.authors.append(author)
        models.Author.sanitize()

        for ident in self.book.identifiers:
            ident.delete()
        for i in range(self.ids.count()):
            t = unicode(self.ids.itemText(i))
            k, v = t.split(': ', 1)
            i = models.Identifier(key=k, value=v, book=self.book)

        self.book.tags = []
        for tag_name in [unicode(self.tags.item(i).text())
                                    for i in range(self.tags.count())]:
            t = models.Tag.get_by(name=tag_name)
            if not t:
                t = models.Tag(name=tag_name, value=tag_name)
            self.book.tags.append(t)

        models.session.commit()
        self.unsaved = False
        self.updateBook.emit(self.book)

    @QtCore.pyqtSlot()
    def on_add_file_clicked(self):
        file_name = unicode(QtGui.QFileDialog.getOpenFileName(self,
                                                              'Add File'))
        if file_name and not self.fileList.findItems(file_name,
                                                     QtCore.Qt.MatchExactly):
            self.fileList.addItem(file_name)
            self.unsaved = True

    @QtCore.pyqtSlot()
    def on_remove_file_clicked(self):
        self.fileList.takeItem(self.fileList.currentRow())
        self.unsaved = True

    @QtCore.pyqtSlot()
    def on_add_id_clicked(self):
        dlg = IdentifierDialog('', '', self)
        r = dlg.exec_()
        if not r == dlg.Accepted:
            return
        self.ids.addItem("%s: %s" % (dlg.id_key.text(), dlg.id_value.text()))
        self.unsaved = True

    @QtCore.pyqtSlot()
    def on_remove_id_clicked(self):
        self.ids.removeItem(self.ids.currentIndex())
        self.unsaved = True

    @QtCore.pyqtSlot()
    def on_edit_id_clicked(self):
        k, v = self.ids.currentText().split(": ", 1)
        dlg = IdentifierDialog(k, v, self)
        r = dlg.exec_()
        if not r == dlg.Accepted:
            return
        self.ids.setItemText(self.ids.currentIndex(), "%s: %s" % (
            dlg.id_key.text(), dlg.id_value.text()))
        self.unsaved = True

    @QtCore.pyqtSlot()
    def on_add_tag_clicked(self):
        dlg = TagDialog('', self)
        r = dlg.exec_()
        if not r == dlg.Accepted:
            return
        self.tags.addItem(dlg.tag_name.currentText())
        self.unsaved = True

    @QtCore.pyqtSlot()
    def on_remove_tag_clicked(self):
        self.tags.takeItem(self.tags.currentRow())
        self.unsaved = True

    def findBook(self):
        """
        Busca un libro por ISBN en GoogleBooks y devuelve un dict
        con todos los datos o -1 si no valido el ISBN.
        """
        # FIXME: This "service" was here but I don't know where it came from
        service = None
        isbn = validate_ISBN(str(self.isbnEdit.text()))
        if isbn:
            result = service.search('ISBN' + isbn)
            if result.entry:
                return result.entry[0].to_dict()
        else:
            return -1

    def on_actionfindBook_triggered(self, checked=None):

        if checked is None:
            return

        datos = self.findBook()

        if datos == -1:
            QtGui.QMessageBox.critical(self,
                       self.trUtf8("Error"),
                       self.trUtf8("Por favor revise el ISBN, "
                                   "parece ser erróneo."),
                           QtGui.QMessageBox.StandardButtons(
                                           QtGui.QMessageBox.Ok))

        elif datos:

            # Vaciar imagen siempre
            thumb = QtGui.QPixmap(os.path.join(SCRIPTPATH, "nocover.png"))
            self.tapaLibro.setPixmap(thumb)

            identifiers = dict(datos['identifiers'])
            #print datos['identifiers']

            if 'title' in datos:
                self.txt_1.setText(datos['title'].decode('utf-8'))
            if 'date' in datos:
                self.dte_1.setDateTime(QtCore.QDateTime.fromString(
                                                datos['date'], 'yyyy-mm-dd'))
            if 'subjects' in datos:
                self.txt_2.setText(
                                ', '.join(datos['subjects']).decode('utf-8'))
            if 'authors' in datos:
                self.txt_3.setText(', '.join(datos['authors']).decode('utf-8'))
            if 'description' in datos:
                self.txp_1.appendPlainText(
                                        datos['description'].decode('utf-8'))

            #Merengue para bajar la thumbnail porque QPixmap
            #no levanta desde una url :(

            # TODO
            # Si no tenemos la tapa en covers.openlibrary,
            # deberia leerlo desde google.books.
            # El dato clave estaría en datos['thumbnail']

            thumbdata = urllib2.urlopen(
                            'http://covers.openlibrary.org/b/isbn/%s-M.jpg' %
                            identifiers['ISBN']).read()

            thumb = QtGui.QPixmap()
            # FIXME: en realidad habrí­a que guardarlo
            thumb.loadFromData(thumbdata)
            self.tapaLibro.setPixmap(thumb)

        else:
            # El ISBN es válido pero BookEditor no lo tiene, ej: 950-665-191-4
            self.txt_1.setText('')
            #self.fechaLibro.setText('')
            self.txt_2.setText('')
            self.txt_3.setText('')
            self.txp_1.appendPlainText('')
            QtGui.QMessageBox.critical(self,
                   self.trUtf8("Error"),
                   self.trUtf8("El ISBN parece ser válido, pero no se "
                               "encontró libro con el número indicado."),
                       QtGui.QMessageBox.StandardButtons(QtGui.QMessageBox.Ok))

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    models.initDB()
    if len(sys.argv) == 1:
        # use a default book
        ventana = BookEditor(models.Book.get_by().id)
    else:
        ventana = BookEditor(int(sys.argv[1]))
    ventana.show()
    sys.exit(app.exec_())
