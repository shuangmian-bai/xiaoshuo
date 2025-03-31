rmdir /s /q dist
pyinstaller --icon=.\\icon\\shuangmian.ico --console --distpath dist main.py
copy init.ini dist\main\