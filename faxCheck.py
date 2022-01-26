import sys, pickle, os, stat
from PyQt5.QtWidgets import QMainWindow, QApplication, QSystemTrayIcon, QMessageBox, QAction, QMenu, QFileDialog, QLineEdit, QPushButton, QStatusBar
from PyQt5.QtCore import QTimer, QFileInfo, QUrl
from PyQt5.QtGui import QIcon, QDesktopServices
#from faxCheckGui import Ui_MainWindow
from PyQt5 import uic
import sys

class checkFax(QMainWindow):
    def __init__(self):
        super(checkFax, self).__init__()
        uic.loadUi("faxCheck.ui", self)
        
        self.numTimes = 1
        # Get QT objects from ui...
        self.ui = self.findChild(QMainWindow, "MainWindow")
        self.checkIntervalLineEdit = self.findChild(QLineEdit, "checkIntervalLineEdit")
        self.dirToMonitorLineEdit = self.findChild(QLineEdit, "dirToMonitorLineEdit")
        self.configFileLineEdit = self.findChild(QLineEdit, "configFileLineEdit")
        self.actionQuit = self.findChild(QAction, "actionQuit")
        self.updatePushButton = self.findChild(QPushButton, "updatePushButton")
        self.pickDirPushButton = self.findChild(QPushButton, "pickDirPushButton")
        self.statusbar = self.findChild(QStatusBar, "statusbar")
        
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
        self.trayIcon.setContextMenu(self.trayIconMenu)

        self.loadConfigFile()
        self.checkIntervalLineEdit.setText(str(int(self.configData['checkInterval'] / 1000)))
        self.dirToMonitorLineEdit.setText(self.configData['dirToMonitor'])
        self.configFileLineEdit.setText(self.configData['confFile'])
        self.actionQuit.triggered.connect(self.dropDead)

        self.updatePushButton.clicked.connect(self.update)
        self.pickDirPushButton.clicked.connect(self.pickDir)

        self.checkForFaxes()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.checkForFaxes)
        self.timer.start(self.configData['checkInterval'])
        self.minimizeAction.setEnabled(self.isVisible())
        self.restoreAction.setEnabled(not self.isVisible())

    def pickDir(self):
        dname = QFileDialog.getExistingDirectory(self, "Select Directory to Monitor", self.dirToMonitorLineEdit.text())
        if dname:
            self.dirToMonitorLineEdit.setText(dname)
    
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
            
        # set "new fax" icon as long as there are files in the directory...
        if len(listOfFiles) > 0:
            self.setWindowIcon(self.newFaxIcon)
            self.trayIcon.setIcon(self.newFaxIcon)
        # else set "no new fax" icon when the directory is empty...
        else:
            self.setWindowIcon(self.normFaxIcon)
            self.trayIcon.setIcon(self.normFaxIcon)
            listOfFiles = 'faxCheck -- monitor for new faxes'
        self.trayIcon.setToolTip(listOfFiles)
        self.statusbar.showMessage('checkForFaxes(' + str(self.numTimes) + ')')
        self.numTimes += 1

    def update(self):
        newCheckInterval = int(self.checkIntervalLineEdit.text()) * 1000
        newDirToMonitor = self.dirToMonitorLineEdit.text()

       # Make sure new values are valid:
        
        if newCheckInterval <= 999000 and newCheckInterval > 0:
            self.configData['checkInterval'] = newCheckInterval
        try:
            statinfo = os.stat(newDirToMonitor)
            if stat.S_ISDIR(statinfo.st_mode):
                self.configData['dirToMonitor'] = newDirToMonitor
        except FileNotFoundError:
            print ('[' + newDirToMonitor + '] does not exist')
            self.dropDead()
            
        # Update config file...
        with open(self.configData['confFile'], 'wb') as f:
            pickle.dump(self.configData, f, pickle.HIGHEST_PROTOCOL)
        self.checkIntervalLineEdit.setText(str(int(self.configData['checkInterval'] / 1000)))
        self.dirToMonitorLineEdit.setText(self.configData['dirToMonitor'])

    def loadConfigFile(self):
        self.configData = {
            'dirToMonitor': '//samba-jail.losh.lan/share/faxes'
            , 'checkInterval': int(5000)
            , 'confFile': os.path.expanduser('~') + os.sep + '.faxCheckrc'
        }
        try:
            statinfo = os.stat(self.configData['confFile'])
            with open(self.configData['confFile'], 'rb') as f:
                self.configData = pickle.load(f)
        except FileNotFoundError:
            with open(self.configData['confFile'], 'wb') as f:
                pickle.dump(self.configData, f, pickle.HIGHEST_PROTOCOL)

    def closeEvent(self, event):
        self.hide()
        event.ignore()

    def openFaxDir(self):
        QDesktopServices.openUrl(QUrl.fromLocalFile(self.configData['dirToMonitor']))

    def dropDead(self):
        self.timer.stop()
        self.trayIcon.hide()
        self.hide()
        QApplication.instance().quit()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    if not QSystemTrayIcon.isSystemTrayAvailable():
        QMessageBox.critical(None, "faxCheck", "System tray is not available on this system.")
        sys.exit(1)
    #QApplication.setQuitOnLastWindowClosed(False)
    gui = checkFax()
#    gui.show()
    retval = app.exec_()
    gui.timer.stop()
    gui.trayIcon.hide()
    gui.hide()
    sys.exit(retval)
