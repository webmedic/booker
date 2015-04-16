# -*- coding: utf-8 -*-
from PyQt4 import QtCore, QtGui, uic
import config
import ui
"""
Network configuration

To get the current configuration 
call get_config()

If it returns None, then no proxy is needed.
If there's a proxy set up you'll get a 
dictionary, like this:
{'host': 'some.hostname',
 'port': 8080,
 'username': 'someuser',
 'password': 'somepassword'}

If the 'username' and 'password' fields are 
present is because the proxy requires 
authentication.
"""

def get_config():
    """Retrieves the current network configuration"""
    return config.getValue('network', 'proxy', None)

def save_config(proxy_data=None):
    """Saves the network configuration"""
    config.setValue('network', 'proxy', proxy_data)

class NetworkSettings(QtGui.QDialog):
    """Dialog to define network settings (proxy)"""
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        uifile = ui.path('networkconf.ui')
        uic.loadUi(uifile, self)
        self.ui = self
        self.load_form()

    def load_form(self):
        """Loads the configuration and fills
           the form"""
        data = get_config()
        if data is None:
            self.direct.click()
            self.host.setText('')
            self.host.setDisabled(True)
            self.port.setValue(8080)
            self.port.setDisabled(True)
            self.auth.setChecked(False)
            self.auth.setDisabled(True)
            self.username.setText('')
            self.username.setDisabled(True)
            self.password.setText('')
            self.password.setDisabled(True)
        else:
            if 'host' in data:
                self.proxy.click()
                self.host.setText(data['host'])
            if 'port' in data:
                self.port.setValue(int(data['port']))
            if 'username' in data and 'password' in data:
                self.auth.setChecked(True)
                self.username.setText(data['username'])
                self.username.setDisabled(False)
                self.password.setDisabled(False)
            else:
                self.auth.setChecked(False)
                self.username.setDisabled(True)
                self.password.setDisabled(True)

    def _toggle_fields(self, disable):
        """Enables/disables form fields"""
        self.host.setDisabled(disable)
        self.port.setDisabled(disable)
        self.auth.setDisabled(disable)
        if disable:
            self.username.setDisabled(True)
            self.password.setDisabled(True)
        else:
            status = not self.auth.isChecked()
            self.username.setDisabled(status)
            self.password.setDisabled(status)

    def on_auth_released(self):
        """Callback called when the
           'Use authentication' checkbox is
            clicked"""
        disable = not self.auth.isChecked()
        self.username.setDisabled(disable)
        self.password.setDisabled(disable)

    def on_direct_clicked(self, checked=False):
        """Disables the proxy settings fields"""
        if checked:
            self._toggle_fields(True)

    def on_proxy_clicked(self, checked=False):
        """Enabled the proxy settings fields"""
        if checked:
            self._toggle_fields(False)

    def _show_error(self, msg):
        QtGui.QMessageBox.critical(self,
                                   self.trUtf8("Error"),
                                   msg,
                                   QtGui.QMessageBox.StandardButtons(QtGui.QMessageBox.Ok)
                                   )

    def _check_form(self):
        if self.proxy.isChecked():
            host = unicode(self.host.text())
            if host == '':
                self._show_error(u'You need to set a proxy host')
                self.host.setFocus()
                return False
            if self.auth.isChecked():
                user = unicode(self.username.text())
                passwd = unicode(self.password.text())
                if user == '':
                    self._show_error(u'You need to set a username to enable proxy authentication')
                    self.username.setFocus()
                    return False
                if passwd == '':
                    self._show_error(u'You need to set a password to enable proxy authentication')
                    self.password.setFocus()
                    return False
        return True

    def accept(self):
        if self.direct.isChecked():
            data = None
        else:
            if not self._check_form():
                return False
            data = { \
                'host': unicode(self.host.text()), \
                'port': int(self.port.value())
            }
            if self.auth.isChecked():
                data['username'] = unicode(self.username.text())
                data['password'] = unicode(self.password.text())
        save_config(data)
        self.done(0)
