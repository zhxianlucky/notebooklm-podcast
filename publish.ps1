# 设置控制台编码为 UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = "Continue"

Write-Host "[1/4] 正在运行 Python 脚本生成 MP3 和 RSS..." -ForegroundColor Cyan
python generate_rss.py

Write-Host "[2/4] 添加更改到 Git..." -ForegroundColor Cyan
git add .

Write-Host "[3/4] 提交更改（如果有）..." -ForegroundColor Cyan
git commit -m "auto: 更新播客内容" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "✅ 没有需要提交的更改，跳过 commit。" -ForegroundColor Green
}

Write-Host "[4/4] 推送到 GitHub..." -ForegroundColor Cyan
git push

Write-Host "`n✅ 发布成功！你可以刷新小宇宙查看新节目。" -ForegroundColor Green
Pause
