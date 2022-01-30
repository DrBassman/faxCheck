import sys, os, stat
from PyQt6.QtWidgets import QMainWindow, QApplication, QSystemTrayIcon, QMessageBox, QMenu, QFileDialog
from PyQt6.QtCore import QTimer, QUrl, QCoreApplication, QSettings
from PyQt6.QtGui import QIcon, QDesktopServices, QAction, QCursor
from PyQt6 import uic

QCoreApplication.setApplicationName("faxCheck")
QCoreApplication.setOrganizationDomain("losh.com")
QCoreApplication.setOrganizationName("Losh Optometry")

class checkFax(QMainWindow):
    def __init__(self):
        super(checkFax, self).__init__()
        self.ui = uic.loadUi("faxCheck.ui", self)
        self.settings = QSettings()
        self.configData = {}

        # Keep track of window last position between runs...
        if self.settings.contains("geometry"):
            self.restoreGeometry(self.settings.value("geometry"))

        # Set up default configuration if it doesn't exist...
        if not self.settings.contains("Installed"):
            d = QFileDialog.getExistingDirectory(self, "Select Directory to Monitor", "")
            while not d:
                d = QFileDialog.getExistingDirectory(self, "Select Directory to Monitor", "")
            self.settings.setValue("config/dirToMonitor", d)
            self.settings.setValue("config/checkInterval", 5000)
            self.settings.setValue("Installed", True)

        # Load configuration.
        self.configData['dirToMonitor'] = self.settings.value("config/dirToMonitor")
        self.configData['checkInterval'] = int(self.settings.value("config/checkInterval"))

        self.numTimes = 1
        
        self.normFaxIcon = QIcon('fax.png')
        self.newFaxIcon = QIcon('new_fax.png')
        self.trayIcon = QSystemTrayIcon(self.normFaxIcon, self)
        self.setWindowIcon(self.normFaxIcon)
        self.trayIcon.show()
        self.minimizeAction = QAction("Mi&nimize", self, triggered=self.hide)
        self.restoreAction = QAction("&Restore", self, triggered=self.showNormal)
        self.openFaxDirAction = QAction("&Open fax directory", self, triggered=self.openFaxDir)
        self.quitAction = QAction("&Quit", self, triggered=self.dropDead)
        self.trayIconMenu = QMenu(self)
        self.trayIconMenu.addAction(self.minimizeAction)
        self.trayIconMenu.addAction(self.restoreAction)
        self.trayIconMenu.addAction(self.openFaxDirAction)
        self.trayIconMenu.addSeparator()
        self.trayIconMenu.addAction(self.quitAction)

        self.ui.checkIntervalSpinBox.setValue(self.configData['checkInterval'] // 1000)
        self.ui.dirToMonitorLineEdit.setText(self.configData['dirToMonitor'])
        self.ui.actionQuit.triggered.connect(self.dropDead)
        self.ui.checkIntervalSpinBox.valueChanged.connect(self.checkIntervalChanged)

        self.ui.pickDirPushButton.clicked.connect(self.pickDir)
        self.trayIcon.activated.connect(self.trayActivated)

        self.checkForFaxes()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.checkForFaxes)
        self.timer.start(self.configData['checkInterval'])
        self.minimizeAction.setEnabled(self.isVisible())
        self.restoreAction.setEnabled(not self.isVisible())

    def trayActivated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Context:
            self.trayIconMenu.exec(QCursor.pos())
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.openFaxDir()
        if reason == QSystemTrayIcon.ActivationReason.MiddleClick:
            self.showNormal()

    def hide(self):
        super(checkFax, self).hide()
        self.minimizeAction.setEnabled(self.isVisible())
        self.restoreAction.setEnabled(not self.isVisible())

    def showNormal(self):
        super(checkFax, self).showNormal()
        self.minimizeAction.setEnabled(self.isVisible())
        self.restoreAction.setEnabled(not self.isVisible())

    def checkForFaxes(self):
        listOfFiles = ''
        numFiles = 0
        statinfo = None
        try:
            statinfo = os.stat(self.configData['dirToMonitor'])
        except FileNotFoundError:
            self.timer.stop()
            QApplication.instance().quit()
            
        for f in os.listdir(self.configData['dirToMonitor']):
            # ignore "hidden" files that start with .
            if f[0] != '.':
                pathname = os.path.join(self.configData['dirToMonitor'], f)
                if listOfFiles != '':
                    listOfFiles += '\n'
                listOfFiles += pathname
                numFiles += 1
            
        # set "new fax" icon as long as there are files in the directory...
        if len(listOfFiles) > 0:
            self.setWindowIcon(self.newFaxIcon)
            self.trayIcon.setIcon(self.newFaxIcon)
        # else set "no new fax" icon when the directory is empty...
        else:
            self.setWindowIcon(self.normFaxIcon)
            self.trayIcon.setIcon(self.normFaxIcon)
            listOfFiles = 'faxCheck -- monitor for new faxes'
        listOfFiles = f"\n{str(numFiles)} Faxes waiting\n "
        self.trayIcon.setToolTip(listOfFiles)
        self.ui.statusbar.showMessage('checkForFaxes(' + str(self.numTimes) + ')')
        self.numTimes += 1

    def closeEvent(self, event):
        self.hide()
        event.ignore()

    def openFaxDir(self):
        QDesktopServices.openUrl(QUrl.fromLocalFile(self.configData['dirToMonitor']))

    def dropDead(self):
        self.timer.stop()
        self.trayIcon.hide()
        # keep track of window position between runs...
        self.settings.setValue("geometry", self.saveGeometry())
        self.hide()
        QApplication.instance().quit()

    def pickDir(self):
        dname = QFileDialog.getExistingDirectory(self, "Select Directory to Monitor", self.ui.dirToMonitorLineEdit.text())
        if dname:
            print(f"Updated path [{dname}]")
            self.configData['dirToMonitor'] = dname
            self.settings.setValue("config/dirToMonitor", dname)
            self.ui.dirToMonitorLineEdit.setText(dname)
            self.timer.stop()
            self.timer.start(self.configData['checkInterval'])
    
    def checkIntervalChanged(self, updated_val):
        updated_val_ms = updated_val * 1000
        self.configData['checkInterval'] = updated_val_ms
        self.settings.setValue("config/checkInterval", updated_val_ms)
        self.timer.stop()
        self.timer.start(self.configData['checkInterval'])


if __name__ == '__main__':
    app = QApplication(sys.argv)
    if not QSystemTrayIcon.isSystemTrayAvailable():
        QMessageBox.critical(None, "faxCheck", "System tray is not available on this system.")
        sys.exit(1)
    #QApplication.setQuitOnLastWindowClosed(False)
    gui = checkFax()
#    gui.show()
    retval = app.exec()
    gui.timer.stop()
    gui.trayIcon.hide()
    gui.hide()
    sys.exit(retval)