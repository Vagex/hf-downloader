Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "cmd /c cd /d """ & Replace(WScript.ScriptFullName, WScript.ScriptName, "") & """ && node server.js", 0, False
WshShell.Run "cmd /c start http://localhost:3000", 0, False
