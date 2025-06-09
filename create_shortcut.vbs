Dim objShell, desktopPath, shortcut, args
Set objShell = CreateObject("WScript.Shell")
Set args = WScript.Arguments

If args.Count < 3 Then
    WScript.Echo "Usage: cscript create_shortcut.vbs ""path\to\file.bat"" ""path\to\icon.ico"" ""Shortcut Name"""
    WScript.Quit 1
End If

batPath = args(0)
iconPath = args(1)
shortcutName = args(2)

desktopPath = objShell.SpecialFolders("Desktop")
shortcutPath = desktopPath & "\" & shortcutName & ".lnk"

Set shortcut = objShell.CreateShortcut(shortcutPath)
shortcut.TargetPath = batPath
shortcut.IconLocation = iconPath
shortcut.WorkingDirectory = CreateObject("Scripting.FileSystemObject").GetParentFolderName(batPath)
shortcut.Save