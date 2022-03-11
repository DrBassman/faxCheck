# define the name of the installer
Name "faxCheck setup"
#SetCompressor /SOLID zlib|bzip2|lzma
SetCompressor /SOLID lzma
Outfile "faxCheck_install.exe"
InstallDir $PROGRAMFILES64\faxCheck
DirText "Install faxCheck on your computer" "" "Browse" "Select directory into which to install faxCheck"

# default section
Section
     # define the output path for this file
    SetOutPath $INSTDIR
    SetShellVarContext all
    # define what to install and place it in the output path
    File /r dist\faxCheck\*
    CreateShortCut $SMPROGRAMS\faxCheck.lnk $INSTDIR\faxCheck.exe parameters $INSTDIR\fax.ico
    CreateShortCut $SMSTARTUP\faxCheck.lnk $INSTDIR\faxCheck.exe parameters $INSTDIR\fax.ico
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\faxCheck" "DisplayName" "faxCheck - a Python QT6 app to monitor directory for new files"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\faxCheck" "Publisher" "Ryan Losh"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\faxCheck" "UninstallString" "$\"$INSTDIR\Uninstall.exe$\""
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\faxCheck" "QuietUninstallString" "$\"$INSTDIR\Uninstall.exe$\" /S"
    WriteUninstaller $INSTDIR\Uninstall.exe
SectionEnd


Section "Uninstall"
    MessageBox MB_OKCANCEL "Uninstall faxCheck..." IDOK rm IDCANCEL can
    can:
        goto next
    rm:
        SetShellVarContext all
        Delete $INSTDIR\Uninstall.exe
        Delete $SMPROGRAMS\faxCheck.lnk
        Delete $SMSTARTUP\faxCheck.lnk
        RMDir /r /REBOOTOK $INSTDIR
        DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\faxCheck"
    next:
SectionEnd