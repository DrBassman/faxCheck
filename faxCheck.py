import sys, pickle, os, stat
from PyQt5.QtWidgets import QMainWindow, QApplication, QSystemTrayIcon, QMessageBox, QAction, QMenu
from PyQt5.QtCore import QTimer, QFileInfo
from PyQt5.QtGui import QIcon
from faxCheckGui import Ui_MainWindow

class checkFax(QMainWindow):
    def __init__(self):
        super(checkFax, self).__init__()
        self.numTimes = 1
        self.ui = Ui_MainWindow()
        self.normFaxIcon = QIcon('fax.png')
        self.newFaxIcon = QIcon('new_fax.png')
        self.trayIcon = QSystemTrayIcon(self.normFaxIcon, self)
        self.setWindowIcon(self.normFaxIcon)
        self.trayIcon.show()
        self.trayIcon.activated.connect(self.trayIconActivated)
        self.minimizeAction = QAction("Mi&nimize", self, triggered=self.hide)
        self.restoreAction = QAction("&Restore", self, triggered=self.showNormal)
        self.quitAction = QAction("&Quit", self, triggered=self.dropDead)
        self.trayIconMenu = QMenu(self)
        self.trayIconMenu.addAction(self.minimizeAction)
        self.trayIconMenu.addAction(self.restoreAction)
        self.trayIconMenu.addSeparator()
        self.trayIconMenu.addAction(self.quitAction)
        self.trayIcon.setContextMenu(self.trayIconMenu)
        self.ui.setupUi(self)

        self.loadConfigFile()
        self.ui.checkIntervalLineEdit.setText(str(int(self.configData['checkInterval'] / 1000)))
        self.ui.dirToMonitorLineEdit.setText(self.configData['dirToMonitor'])
        self.ui.lastMTimeLineEdit.setText(str(self.configData['lastMtime']))
        self.ui.configFileLineEdit.setText(self.configData['confFile'])

        self.ui.updatePushButton.clicked.connect(self.update)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.checkForFaxes)
        self.timer.start(self.configData['checkInterval'])

    def checkForFaxes(self):
        print ("checkForFaxes()")
        statinfo = None
        try:
            statinfo = os.stat(self.configData['dirToMonitor'])
        except FileNotFoundError:
            self.timer.stop()
            QApplication.instance().quit()
        if self.configData['lastMtime'] != statinfo.st_mtime:
            self.configData['lastMtime'] = statinfo.st_mtime
            self.update()
            self.setWindowIcon(self.newFaxIcon)
            self.trayIcon.setIcon(self.newFaxIcon)
        self.ui.statusbar.showMessage('checkForFaxes(' + str(self.numTimes) + ')')
        self.numTimes += 1

    def update(self):
        newCheckInterval = int(self.ui.checkIntervalLineEdit.text()) * 1000
        newDirToMonitor = self.ui.dirToMonitorLineEdit.text()

       # Make sure new values are valid:
        
        if newCheckInterval <= 999000 and newCheckInterval > 0:
            self.configData['checkInterval'] = newCheckInterval
        else:
            print ('[' + str(newCheckInterval) + '] is not valid interval')
        try:
            statinfo = os.stat(newDirToMonitor)
            if stat.S_ISDIR(statinfo.st_mode):
                self.configData['dirToMonitor'] = newDirToMonitor
            else:
                print ('[' + newDirToMonitor + '] is not a directory')
        except FileNotFoundError:
            print ('[' + newDirToMonitor + '] does not exist')
            
        # Update config file...
        with open(self.configData['confFile'], 'wb') as f:
            pickle.dump(self.configData, f, pickle.HIGHEST_PROTOCOL)
        self.ui.checkIntervalLineEdit.setText(str(int(self.configData['checkInterval'] / 1000)))
        self.ui.dirToMonitorLineEdit.setText(self.configData['dirToMonitor'])
        self.ui.lastMTimeLineEdit.setText(str(self.configData['lastMtime']))

    def loadConfigFile(self):
        self.configData = {
            'lastMtime': float(0.0)
            , 'dirToMonitor': 'S:\\Faxes'
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

    def trayIconActivated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            print ("DoubleClick")
            self.showNormal()
        elif reason == QSystemTrayIcon.Trigger:
            print ("Trigger")
            self.setWindowIcon(self.normFaxIcon)
            self.trayIcon.setIcon(self.normFaxIcon)

    def dropDead(self):
        print ("dropDead()")
        self.timer.stop()
        self.update()
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
    gui.show()
    retval = app.exec_()
    gui.timer.stop()
    gui.trayIcon.hide()
    gui.hide()
    sys.exit(retval)
