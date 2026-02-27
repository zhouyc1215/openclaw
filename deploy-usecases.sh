#!/bin/bash
# awesome-openclaw-usecases 自动部署脚本

set -e

CRON_FILE="/home/tsl/.openclaw/cron/jobs.json"
FEISHU_USER_ID="ou_b3afb7d2133e4d689be523fc48f3d2b3"

echo "🦞 OpenClaw Use Cases 部署工具"
echo "================================"
echo ""

# 检查 jq 是否安装
if ! command -v jq &> /dev/null; then
    echo "❌ 需要安装 jq 工具"
    echo "运行: sudo apt-get install jq"
    exit 1
fi

# 备份当前配置
echo "📦 备份当前配置..."
cp "$CRON_FILE" "${CRON_FILE}.backup.$(date +%Y%m%d_%H%M%S)"

echo ""
echo "可用的用例："
echo "1. 科技新闻摘要 (Tech News Digest)"
echo "2. Reddit 每日摘要 (Reddit Digest)"
echo "3. 自定义晨报 (Morning Brief)"
echo "4. 个人知识库 (Knowledge Base)"
echo "5. AI 财报追踪 (Earnings Tracker)"
echo "6. 全部部署"
echo "0. 退出"
echo ""

read -p "选择要部署的用例 (输入数字): " choice

case $choice in
    1)
        echo "📰 部署科技新闻摘要..."
        
        # 生成新任务 ID
        TASK_ID=$(uuidgen)
        CREATED_AT=$(date +%s)000
        
        # 添加任务到 cron jobs
        jq --arg id "$TASK_ID" \
           --arg created "$CREATED_AT" \
           --arg updated "$CREATED_AT" \
           --arg feishu_id "$FEISHU_USER_ID" \
           '.jobs += [{
              "id": $id,
              "agentId": "main",
              "name": "tech_news_digest",
              "enabled": true,
              "createdAtMs": ($created | tonumber),
              "updatedAtMs": ($updated | tonumber),
              "schedule": {
                "kind": "cron",
                "expr": "0 8 * * *",
                "tz": "Asia/Shanghai"
              },
              "sessionTarget": "isolated",
              "wakeMode": "now",
              "payload": {
                "kind": "agentTurn",
                "message": "生成过去 24 小时的科技新闻摘要。搜索 AI、开源项目、前沿技术相关的重要新闻。\n\n要求：\n1. 按重要性排序（优先 AI 和开源项目）\n2. 每条新闻包含：标题、来源、关键信息摘要、链接\n3. 去除重复和低质量内容\n4. 格式化为清晰的列表，使用 emoji 标记类别\n5. 总数控制在 10-15 条\n\n分类：\n🤖 AI/机器学习\n🔧 开源项目\n💡 技术创新\n📱 产品发布",
                "timeoutSeconds": 240
              },
              "delivery": {
                "mode": "announce",
                "channel": "feishu",
                "to": $feishu_id,
                "bestEffort": true
              }
            }]' "$CRON_FILE" > "${CRON_FILE}.tmp" && mv "${CRON_FILE}.tmp" "$CRON_FILE"
        
        echo "✅ 科技新闻摘要已添加（每天 8:00）"
        echo "📝 任务 ID: $TASK_ID"
        ;;
        
    2)
        echo "📱 部署 Reddit 每日摘要..."
        
        TASK_ID=$(uuidgen)
        CREATED_AT=$(date +%s)000
        
        jq --arg id "$TASK_ID" \
           --arg created "$CREATED_AT" \
           --arg updated "$CREATED_AT" \
           --arg feishu_id "$FEISHU_USER_ID" \
           '.jobs += [{
              "id": $id,
              "agentId": "main",
              "name": "reddit_daily_digest",
              "enabled": true,
              "createdAtMs": ($created | tonumber),
              "updatedAtMs": ($updated | tonumber),
              "schedule": {
                "kind": "cron",
                "expr": "0 18 * * *",
                "tz": "Asia/Shanghai"
              },
              "sessionTarget": "isolated",
              "wakeMode": "now",
              "payload": {
                "kind": "agentTurn",
                "message": "获取以下 subreddit 的热门帖子摘要：\n- r/MachineLearning\n- r/LocalLLaMA\n- r/OpenAI\n- r/programming\n- r/golang\n- r/rust\n\n要求：\n1. 每个 subreddit 选择 3-5 个最热门的帖子\n2. 过滤掉 meme 和低质量内容\n3. 包含：标题、简短摘要、评论数、链接\n4. 按 subreddit 分组\n5. 使用 emoji 标记类型（📊 数据/研究、💻 代码/项目、💡 讨论、📰 新闻）",
                "timeoutSeconds": 180
              },
              "delivery": {
                "mode": "announce",
                "channel": "feishu",
                "to": $feishu_id,
                "bestEffort": true
              }
            }]' "$CRON_FILE" > "${CRON_FILE}.tmp" && mv "${CRON_FILE}.tmp" "$CRON_FILE"
        
        echo "✅ Reddit 每日摘要已添加（每天 18:00）"
        echo "📝 任务 ID: $TASK_ID"
        echo "⚠️  需要安装 reddit-readonly skill: openclaw skills install reddit-readonly"
        ;;
        
    3)
        echo "☀️ 部署自定义晨报..."
        
        TASK_ID=$(uuidgen)
        CREATED_AT=$(date +%s)000
        
        jq --arg id "$TASK_ID" \
           --arg created "$CREATED_AT" \
           --arg updated "$CREATED_AT" \
           --arg feishu_id "$FEISHU_USER_ID" \
           '.jobs += [{
              "id": $id,
              "agentId": "main",
              "name": "custom_morning_brief",
              "enabled": true,
              "createdAtMs": ($created | tonumber),
              "updatedAtMs": ($updated | tonumber),
              "schedule": {
                "kind": "cron",
                "expr": "30 6 * * *",
                "tz": "Asia/Shanghai"
              },
              "sessionTarget": "isolated",
              "wakeMode": "now",
              "payload": {
                "kind": "agentTurn",
                "message": "生成今日晨报：\n\n1. 📅 今日概览\n   - 日期和星期\n   - 西安天气预报（调用天气 API）\n\n2. 📰 重要新闻（3-5 条）\n   - AI 和科技领域的重要动态\n   - 每条包含简短摘要和为什么重要\n\n3. 🚀 今日推荐\n   - 1-2 个值得关注的 AI 项目或工具\n   - 说明推荐理由和应用场景\n\n4. 💡 今日建议\n   - 2-3 个我可以帮你完成的任务\n   - 基于当前技术趋势的学习建议\n\n格式要求：\n- 使用 emoji 增强可读性\n- 简洁明了，总长度控制在 800 字以内\n- 重点突出，避免冗余信息",
                "timeoutSeconds": 240
              },
              "delivery": {
                "mode": "announce",
                "channel": "feishu",
                "to": $feishu_id,
                "bestEffort": true
              }
            }]' "$CRON_FILE" > "${CRON_FILE}.tmp" && mv "${CRON_FILE}.tmp" "$CRON_FILE"
        
        echo "✅ 自定义晨报已添加（每天 6:30）"
        echo "📝 任务 ID: $TASK_ID"
        ;;
        
    4)
        echo "📚 配置个人知识库..."
        echo ""
        echo "知识库功能需要通过对话配置，请在飞书发送以下消息给 clawdbot："
        echo ""
        echo "---"
        cat << 'EOF'
设置知识库功能：

当我在飞书发送 URL 链接时：
1. 自动抓取内容（文章、推文、YouTube 字幕、PDF）
2. 将内容存入知识库，包含元数据（标题、URL、日期、类型）
3. 回复确认：已存入什么内容

当我提问"搜索知识库：<关键词>"时：
1. 在知识库中进行语义搜索
2. 返回最相关的结果，包含来源和摘录
3. 如果没有匹配结果，告诉我

知识库存储在 ~/.openclaw/knowledge-base/ 目录，使用 markdown 格式。
每个条目包含：标题、URL、保存日期、内容摘要、完整内容。
EOF
        echo "---"
        echo ""
        echo "⚠️  可能需要安装 knowledge-base skill"
        ;;
        
    5)
        echo "💰 部署 AI 财报追踪..."
        
        TASK_ID=$(uuidgen)
        CREATED_AT=$(date +%s)000
        
        jq --arg id "$TASK_ID" \
           --arg created "$CREATED_AT" \
           --arg updated "$CREATED_AT" \
           --arg feishu_id "$FEISHU_USER_ID" \
           '.jobs += [{
              "id": $id,
              "agentId": "main",
              "name": "earnings_tracker_weekly",
              "enabled": true,
              "createdAtMs": ($created | tonumber),
              "updatedAtMs": ($updated | tonumber),
              "schedule": {
                "kind": "cron",
                "expr": "0 20 * * 0",
                "tz": "Asia/Shanghai"
              },
              "sessionTarget": "isolated",
              "wakeMode": "now",
              "payload": {
                "kind": "agentTurn",
                "message": "搜索下周的科技公司财报日程：\n\n关注公司：\n- NVIDIA (NVDA)\n- Microsoft (MSFT)\n- Google (GOOGL)\n- Meta (META)\n- Amazon (AMZN)\n- Tesla (TSLA)\n- AMD\n- Apple (AAPL)\n\n输出格式：\n📅 下周财报日程\n\n[日期] [公司名称] ([股票代码])\n- 预计发布时间：盘前/盘后\n- 分析师预期：EPS $X.XX, 营收 $XXB\n- 关注点：[AI 相关业务、关键指标等]\n\n如果下周没有财报，说明最近的财报日期。",
                "timeoutSeconds": 180
              },
              "delivery": {
                "mode": "announce",
                "channel": "feishu",
                "to": $feishu_id,
                "bestEffort": true
              }
            }]' "$CRON_FILE" > "${CRON_FILE}.tmp" && mv "${CRON_FILE}.tmp" "$CRON_FILE"
        
        echo "✅ AI 财报追踪已添加（每周日 20:00）"
        echo "📝 任务 ID: $TASK_ID"
        ;;
        
    6)
        echo "🚀 部署所有用例..."
        bash "$0" <<< "1"
        bash "$0" <<< "2"
        bash "$0" <<< "3"
        bash "$0" <<< "5"
        echo ""
        echo "✅ 所有用例部署完成！"
        echo "📝 知识库功能需要手动配置（选项 4）"
        ;;
        
    0)
        echo "👋 退出"
        exit 0
        ;;
        
    *)
        echo "❌ 无效选择"
        exit 1
        ;;
esac

echo ""
echo "📊 当前定时任务总数："
jq '.jobs | length' "$CRON_FILE"

echo ""
echo "🔄 重启 Gateway 以应用更改..."
echo "运行: openclaw gateway restart"
echo ""
echo "✅ 部署完成！"
