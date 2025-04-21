# 获取当前脚本所在的目录
$DIR = Split-Path -Parent $MyInvocation.MyCommand.Definition

# 将目录添加到 PYTHONPATH
$env:PYTHONPATH = "$env:PYTHONPATH;$DIR"

# 输出确认信息
Write-Output "Current directory '$DIR' has been added to PYTHONPATH"

