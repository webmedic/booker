from PyQt4 import QtGui, uic
from pluginmgr import manager, isPluginEnabled
import config
import ui


class PluginSettings(QtGui.QDialog):

    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)

        uifile = ui.path('pluginconf.ui')
        uic.loadUi(uifile, self)
        self.ui = self
        self.plugin_widgets = []
        for category in manager.getCategories():
            w = QtGui.QScrollArea()
            w.setFrameStyle(w.NoFrame)
            w.setWidgetResizable(True)
            w._widget = QtGui.QWidget()
            w.setWidget(w._widget)
            self.toolBox.addItem(w, category)

            l = QtGui.QVBoxLayout()
            for plugin in manager.getPluginsOfCategory(category):
                pw = PluginWidget(plugin, isPluginEnabled(plugin.name))
                self.plugin_widgets.append(pw)
                l.addWidget(pw)
            l.addStretch(1)
            w._widget.setLayout(l)
        # FIXME: En vez de ocultar page1, sacarlo.
        self.page1.hide()
        self.toolBox.removeItem(0)

    def accept(self):
        enabled_plugins = []
        for pw in self.plugin_widgets:
            if pw.enabled.isChecked():
                enabled_plugins.append(pw.plugin.name)
        config.setValue("general", "enabledPlugins", enabled_plugins)
        return QtGui.QDialog.accept(self)


class PluginWidget(QtGui.QWidget):

    def __init__(self, plugin, enabled, parent=None):
        QtGui.QWidget.__init__(self, parent)

        uifile = ui.path('pluginwidget.ui')
        uic.loadUi(uifile, self)
        self.ui = self
        self.plugin = plugin
        self.enabled.setText(plugin.name)
        self.enabled.setChecked(enabled)
        if not plugin.plugin_object.configurable:
            self.configure.setVisible(False)
        if plugin.plugin_object.configurable:
            self.configure.clicked.connect(self.plugin.plugin_object.configure)
