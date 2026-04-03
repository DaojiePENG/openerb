#!/bin/bash
# OpenERB 代码提交脚本

set -e

echo "🚀 OpenERB 代码提交工具"
echo "========================"

# 检查是否有未提交的更改
if [ -z "$(git status --porcelain)" ]; then
    echo "✅ 工作区是干净的，没有需要提交的更改"
    exit 0
fi

# 显示当前状态
echo "📊 当前 Git 状态:"
git status --short

echo ""
echo "🔍 更改详情:"
git diff --stat

# 运行测试
echo ""
echo "🧪 运行测试..."
if python -m pytest tests/ -x --tb=short -q; then
    echo "✅ 所有测试通过"
else
    echo "❌ 测试失败，请修复后再提交"
    exit 1
fi

# 获取提交信息
echo ""
read -p "📝 请输入提交信息: " commit_message

if [ -z "$commit_message" ]; then
    echo "❌ 提交信息不能为空"
    exit 1
fi

# 添加所有更改
echo ""
echo "📦 添加文件到暂存区..."
git add .

# 提交更改
echo "💾 提交更改..."
git commit -m "$commit_message"

# 显示提交结果
echo ""
echo "✅ 提交成功!"
echo "📋 提交详情:"
git log --oneline -1

# 可选: 推送到远程
read -p "🔄 是否推送到远程仓库? (y/N): " push_choice
if [[ $push_choice =~ ^[Yy]$ ]]; then
    echo "📤 推送中..."
    git push
    echo "✅ 推送成功!"
fi

echo ""
echo "🎉 完成! 你的更改已成功提交。"