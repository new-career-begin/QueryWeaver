# Draw.io Skill 发布脚本
# 使用方法: .\publish.ps1 -GitHubUsername "your-username" -Email "your-email@example.com" -Name "Your Name"

param(
    [Parameter(Mandatory=$true)]
    [string]$GitHubUsername,
    
    [Parameter(Mandatory=$true)]
    [string]$Email,
    
    [Parameter(Mandatory=$true)]
    [string]$Name
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Draw.io Skill 发布脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 步骤 1: 配置 Git 用户信息
Write-Host "[1/5] 配置 Git 用户信息..." -ForegroundColor Yellow
git config user.email $Email
git config user.name $Name
Write-Host "✓ Git 用户信息已配置" -ForegroundColor Green
Write-Host ""

# 步骤 2: 检查是否有未提交的更改
Write-Host "[2/5] 检查文件状态..." -ForegroundColor Yellow
$status = git status --short
if ($status) {
    Write-Host "发现未提交的文件，正在添加..." -ForegroundColor Yellow
    git add -A
    Write-Host "✓ 文件已添加到暂存区" -ForegroundColor Green
} else {
    Write-Host "✓ 所有文件已提交" -ForegroundColor Green
}
Write-Host ""

# 步骤 3: 创建提交
Write-Host "[3/5] 创建 Git 提交..." -ForegroundColor Yellow
try {
    git commit -m "Initial commit: Add drawio skill for OpenSkills"
    Write-Host "✓ 提交已创建" -ForegroundColor Green
} catch {
    Write-Host "⚠ 提交可能已存在或失败，继续..." -ForegroundColor Yellow
}
Write-Host ""

# 步骤 4: 重命名分支为 main
Write-Host "[4/5] 重命名分支为 main..." -ForegroundColor Yellow
git branch -M main
Write-Host "✓ 分支已重命名为 main" -ForegroundColor Green
Write-Host ""

# 步骤 5: 添加远程仓库
Write-Host "[5/5] 配置远程仓库..." -ForegroundColor Yellow
$remoteUrl = "git@github.com:$GitHubUsername/drawio.git"
$httpsUrl = "https://github.com/$GitHubUsername/drawio.git"

# 检查是否已有远程仓库
$existingRemote = git remote get-url origin 2>$null
if ($existingRemote) {
    Write-Host "⚠ 远程仓库已存在: $existingRemote" -ForegroundColor Yellow
    Write-Host "是否要更新? (y/n)" -ForegroundColor Yellow
    $response = Read-Host
    if ($response -eq "y") {
        git remote set-url origin $remoteUrl
        Write-Host "✓ 远程仓库已更新" -ForegroundColor Green
    }
} else {
    Write-Host "选择远程仓库类型:" -ForegroundColor Yellow
    Write-Host "1. SSH (git@github.com) - 推荐" -ForegroundColor Cyan
    Write-Host "2. HTTPS (https://github.com)" -ForegroundColor Cyan
    $choice = Read-Host "请选择 (1/2)"
    
    if ($choice -eq "2") {
        git remote add origin $httpsUrl
        Write-Host "✓ 已添加 HTTPS 远程仓库" -ForegroundColor Green
    } else {
        git remote add origin $remoteUrl
        Write-Host "✓ 已添加 SSH 远程仓库" -ForegroundColor Green
    }
}
Write-Host ""

# 完成提示
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "准备完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "下一步操作:" -ForegroundColor Yellow
Write-Host "1. 在 GitHub 上创建仓库: https://github.com/new" -ForegroundColor White
Write-Host "   - 仓库名称: drawio" -ForegroundColor White
Write-Host "   - 不要初始化 README" -ForegroundColor White
Write-Host ""
Write-Host "2. 创建仓库后，运行以下命令推送代码:" -ForegroundColor Yellow
Write-Host "   git push -u origin main" -ForegroundColor Cyan
Write-Host ""
Write-Host "3. 发布后测试安装:" -ForegroundColor Yellow
Write-Host "   openskills install $GitHubUsername/drawio -y" -ForegroundColor Cyan
Write-Host "   openskills read drawio" -ForegroundColor Cyan
Write-Host ""
