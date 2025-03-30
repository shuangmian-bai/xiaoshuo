rmdir /s /q dist
pyinstaller --icon=.\\icon\\shuangmian.ico --console --distpath dist main.py
copy init.ini dist\main\
mkdir dist\main\Chrome
xcopy /E /I Chrome dist\main\Chrome