' to run this, use wscript path\to\script.vbs.
' for example this can be used in windows task scheduler to periodically run a python script in a hidden way, 
' see https://serverfault.com/questions/9038/run-a-bat-file-in-a-scheduled-task-without-a-window
Dim WinScriptHost
Set WinScriptHost = CreateObject("WScript.Shell")
WinScriptHost.run "cmd /K call C:\Users\hensen\anaconda3\Scripts\activate.bat hensenlab & call python P:\My_Documents\scripts\team-repo\other_tools\check_new_arxiv_posts.py",0
Set WinScriptHost = Nothing