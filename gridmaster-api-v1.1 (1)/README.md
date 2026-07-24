# GridMaster API v1.1

朋友圈九宫格AI排版后端服务（支持"换一组"功能）

## 快速开始

```bash
pip install -r requirements.txt
# 编辑 app/main.py 里的 KIMI_API_KEY
uvicorn app.main:app --reload
```

## API 接口

### POST /analyze
分析图片并返回排版建议

```json
{
  "images": ["base64encoded1", ...],
  "style_hint": "清新自然风",
  "strategy": "经典中心"
}
```

strategy 可选：经典中心、对角线叙事、边框框架、Z字节奏、对称镜像、螺旋深入

### POST /shuffle
换一组：同一9张图，换不同排版策略

```json
{
  "images": ["base64encoded1", ...],
  "current_layout": {"1": {"index": 0}, ...},
  "style": "清新自然风",
  "used_strategies": ["经典中心"]
}
```

### POST /generate-preview
生成九宫格预览图（dark/light背景）

### GET /styles
获取所有风格和策略

### GET /strategies
获取策略详情

## "换一组"功能

- 6种排版策略循环使用
- 自动记录已用策略，避免重复
- 用完后自动重置
- 每次换组都给出变动说明

## 部署

### Vercel
```bash
npm i -g vercel
vercel --prod
```

### Render
推送到 GitHub，创建 Web Service，设置 KIMI_API_KEY
