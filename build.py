import os
import subprocess
from pathlib import Path
import nicegui

# 获取当前脚本所在目录
current_dir = Path(__file__).parent.absolute()

cmd = ['PyInstaller',
    'main.py',  # your main file with ui.run()
    '--name', 'kotonoha_toolkit',  # name of your app
    '--icon', 'aoi.ico',
    '--onedir',  # 使用 --onedir 而不是 --onefile
    '--windowed',
    '--clean',
    '--add-data', f'{Path(nicegui.__file__).parent}{os.pathsep}nicegui',
    '--add-data', f'{current_dir}/static{os.pathsep}static'  # 添加 static 目录
]

print(f'Adding nicegui: {Path(nicegui.__file__).parent}{os.pathsep}nicegui')
print(f'Adding static: {current_dir}/static{os.pathsep}static')

subprocess.call(cmd)