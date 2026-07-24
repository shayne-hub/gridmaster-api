import os
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict
import base64
import io
from PIL import Image
import httpx
import json
import random

app = FastAPI(title="GridMaster API", version="1.1")

KIMI_API_KEY = os.environ.get("KIMI_API_KEY", "sk-Znbzh14y3M0JqHi6gl5DfQaGb780fS0HYgVCaPiqRAviTkrz")
KIMI_BASE_URL = "https://api.moonshot.cn/v1"

# ═══════════════════════════════════════════════════════════════
# 6种风格规则
# ═══════════════════════════════════════════════════════════════

STYLE_RULES = {
    "清新自然风": """内容配比：人物4张 | 自然/细节3张 | 美食1张 | 宠物1张
色调：明亮、自然光、偏暖、高通透感
首图：人物+绿植/户外场景
C位（5）：人物全身或半身，光线最佳
收尾（9）：人物+地标/大场景，与首图闭环
节奏：人物→细节→人物→场景→人物→特写→互动→美食→大场景""",

    "暗调氛围风": """内容配比：人物4张 | 环境/氛围4张 | 诗意细节1张
色调：暗调、低饱和、暖黄灯光为主
首图：室内暖光或傍晚街道
C位（5）：人物坐姿/静态，姿态安静
收尾（9）：与首图呼应，形成闭环
节奏：暖光环境→傍晚场景→光影→人物亲密→人物安静→自拍→环境→诗意细节→环境对称""",

    "粉嫩少女风": """内容配比：人物4张 | 静物/细节4张 | 花束1张
色调：粉色系主导、暖调柔和、奶油感
首图：人物+粉色场景
C位（5）：花束或精致静物
收尾（9）：户外人物或自然光场景
节奏：人物→静物→人物对称→桌面细节→花束C位→户外桌面→车内俏皮→色彩对比→户外收尾""",

    "高级灰冷调风": """内容配比：人物5张 | 环境/美食3张 | 文化细节1张
色调：灰调、冷调、低饱和、暗光、高级质感
首图：餐具/桌面摆拍
C位（5）：人物核心图（常拼接或多图组合）
收尾（9）：窗边剪影或环境对称
节奏：极简摆拍→环境人物→文化细节→自拍→人物拼接→特效→美食→环境对称→剪影诗意""",

    "度假休闲风": """内容配比：人物5张 | 环境/大场景3张 | 度假细节1张
色调：明亮、自然光、蓝绿+白色主导
首图：运动场景，活力定调
C位（5）：身体局部特写+度假元素
收尾（9）：海边/户外人物背影
节奏：运动→日落大场景→人物→美食→身体特写→休闲餐桌→花园人物→泳池蓝调→海边收尾""",

    "温馨居家风": """内容配比：人物4张（3张自拍）| 宠物1张 | 美食1张 | 文艺细节3张
色调：暖黄、居家灯光、柔和、真实感
首图：人物大头/自然表情
C位（5）：宠物，柔软感核心
收尾（9）：电子屏幕/文字/暗调细节
节奏：真实人物→美食→对镜自拍→对镜换装→宠物C位→对镜第三套→手绘文字→可爱摆件→屏幕文字"""
}

GENERAL_RULES = """【九宫格通用铁律】
1. 人物≤5张
2. C位（第5张）50%概率放非人物
3. 首图=定调，收尾图=与首图呼应闭环
4. 一套九宫格色调高度统一
5. 至少1-2张非人物非场景细节
6. 第7-9张或第3-9张常形成对称/呼应
7. 同类内容不相邻超过1张
8. 暗调可用文字贴纸，明亮风格较少用"""

# ═══════════════════════════════════════════════════════════════
# 6种排版策略（换一组用）
# ═══════════════════════════════════════════════════════════════

LAYOUT_STRATEGIES = {
    "经典中心": {
        "name": "经典中心",
        "description": "C位放核心图，四周环绕",
        "rules": "1=establishing, 2=过渡, 3=呼应首图, 4=细节, 5=核心, 6=与4呼应, 7=环境, 8=人物第二状态, 9=收尾闭环"
    },
    "对角线叙事": {
        "name": "对角线叙事",
        "description": "从左上到右下形成视觉对角线",
        "rules": "1=强视觉起点, 2=过渡, 3=轻量细节, 4=过渡, 5=对角线中点静物, 6=过渡, 7=轻量细节, 8=过渡, 9=强视觉终点"
    },
    "边框框架": {
        "name": "边框框架",
        "description": "四角和四边形成框架，中心突出",
        "rules": "1=框架角环境, 2=框架边人物, 3=框架角环境, 4=框架边人物, 5=中心焦点, 6=框架边, 7=框架角, 8=框架边, 9=框架角闭环"
    },
    "Z字节奏": {
        "name": "Z字节奏",
        "description": "视觉按Z字形流动，有起承转合",
        "rules": "1=起点大场景, 2=Z横人物, 3=Z折特写, 4=Z竖环境, 5=Z中心情绪高点, 6=Z竖环境, 7=Z折细节, 8=Z横人物, 9=终点大场景"
    },
    "对称镜像": {
        "name": "对称镜像",
        "description": "左右或上下对称，稳定高级感",
        "rules": "1=对称左场景, 2=对称中左人物, 3=对称右场景, 4=对称左中人物, 5=绝对中心静物, 6=对称右中人物, 7=对称左下, 8=对称中下, 9=对称右下闭环"
    },
    "螺旋深入": {
        "name": "螺旋深入",
        "description": "从外到内螺旋聚焦，再扩散",
        "rules": "1=外环大场景, 2=外环人物远景, 3=外环环境细节, 4=中环人物中景, 5=核心特写, 6=中环呼应, 7=外环呼应, 8=外环人物, 9=外环大场景闭环"
    }
}

SYSTEM_PROMPT = """你是一位资深朋友圈九宫格视觉排版顾问。用户会上传多张图片，你需要：

1. 【分析每张图】：内容类型（人物/风景/建筑/美食/细节/宠物/静物/自拍）、色调（暖/冷/中性/高饱和/低饱和/明亮/暗调）、质量（清晰/模糊/过曝/欠曝）、构图特点
2. 【判断风格】：从以下6种选择最匹配：清新自然风、暗调氛围风、粉嫩少女风、高级灰冷调风、度假休闲风、温馨居家风
3. 【筛选9张】：色调协调、内容有节奏、视觉有层次、质量优先
4. 【排版建议】：给出9张图在九宫格中的位置（1-9），并说明理由
5. 【优化建议】：对被淘汰的图，简要说明为什么没选

输出JSON格式：
{
  "style_detected": "风格名称",
  "recommended_indices": [原图索引号0-8],
  "layout_suggestion": {"1": {"index": x, "reason": "...", "content_type": "..."}, ...},
  "discarded": [{"index": x, "reason": "..."}],
  "style_analysis": "...",
  "color_harmony": "...",
  "pacing_notes": "..."
}"""

# ═══════════════════════════════════════════════════════════════
# Models
# ═══════════════════════════════════════════════════════════════

class AnalyzeRequest(BaseModel):
    images: List[str]
    style_hint: Optional[str] = None
    strategy: Optional[str] = "经典中心"

class ShuffleRequest(BaseModel):
    images: List[str]
    current_layout: dict
    style: str
    used_strategies: List[str] = []

# ═══════════════════════════════════════════════════════════════
# Helper Functions
# ═══════════════════════════════════════════════════════════════

def build_system_message(style_hint: Optional[str] = None, strategy: str = "经典中心") -> str:
    style_rule = STYLE_RULES.get(style_hint, "请根据图片自动判断最适合的风格")
    strategy_info = LAYOUT_STRATEGIES.get(strategy, LAYOUT_STRATEGIES["经典中心"])
    return f"""{SYSTEM_PROMPT}

当前风格偏好：{style_hint or "自动判断"}
当前排版策略：{strategy_info['name']} - {strategy_info['description']}
策略规则：{strategy_info['rules']}

风格规则：
{style_rule}

通用铁律：
{GENERAL_RULES}"""

def build_shuffle_prompt(images: List[str], current_layout: dict, style: str, used: List[str]) -> tuple:
    available = [k for k in LAYOUT_STRATEGIES.keys() if k not in used]
    if not available:
        available = list(LAYOUT_STRATEGIES.keys())
    new_strategy = random.choice(available)
    info = LAYOUT_STRATEGIES[new_strategy]

    prompt = f"""你是九宫格排版顾问。用户已选定9张图，风格"{style}"。

当前排版：{json.dumps(current_layout, ensure_ascii=False)}

请使用新策略："{new_strategy}" - {info['description']}
策略规则：{info['rules']}

要求：
1. 保持同样的9张图（索引不变），只改变位置
2. 严格遵循新策略的位置规则
3. 确保同类内容不相邻超过1张
4. 色调相邻协调
5. 给出每个位置换图的理由

输出JSON：
{{
  "new_layout": {{"1": {{"index": x, "reason": "..."}}, ...}},
  "strategy_name": "{new_strategy}",
  "strategy_description": "{info['description']}",
  "changes_made": [{{"position": "1", "from_index": x, "to_index": y, "reason": "..."}}],
  "reasoning": "整体换组思路"
}}"""
    return prompt, new_strategy

# ═══════════════════════════════════════════════════════════════
# Routes
# ═══════════════════════════════════════════════════════════════

@app.post("/analyze")
async def analyze_grid(request: AnalyzeRequest):
    # 图片数量校验
    img_count = len(request.images)
    if img_count < 9:
        return JSONResponse(
            status_code=400,
            content={
                "error": "图片数量不足",
                "message": f"当前上传了 {img_count} 张图，至少需要 9 张才能组成九宫格",
                "current_count": img_count,
                "min_required": 9,
                "max_allowed": 16
            }
        )
    if img_count > 16:
        return JSONResponse(
            status_code=400,
            content={
                "error": "图片数量过多",
                "message": f"当前上传了 {img_count} 张图，建议控制在 9-16 张之间，方便AI精选最佳九宫格",
                "current_count": img_count,
                "min_required": 9,
                "max_allowed": 16
            }
        )

    system_msg = build_system_message(request.style_hint, request.strategy)

    user_content = [{"type": "text", "text": f"请分析这{len(request.images)}张图片，使用策略：{request.strategy}"}]
    for img in request.images:
        user_content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img}"}})

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{KIMI_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {KIMI_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": "moonshot-v1-8k",
                "messages": [
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_content}
                ],
                "temperature": 0.3,
                "response_format": {"type": "json_object"}
            },
            timeout=60.0
        )

    result = response.json()
    analysis_text = result["choices"][0]["message"]["content"]

    try:
        analysis = json.loads(analysis_text)
    except:
        analysis = {
            "style_detected": "解析失败",
            "recommended_indices": list(range(min(9, len(request.images)))),
            "layout_suggestion": {},
            "discarded": [],
            "style_analysis": analysis_text,
            "color_harmony": "",
            "pacing_notes": ""
        }

    analysis["available_strategies"] = [{"name": k, "description": v["description"]} for k, v in LAYOUT_STRATEGIES.items()]
    analysis["strategy_used"] = request.strategy
    return analysis

@app.post("/shuffle")
async def shuffle_layout(request: ShuffleRequest):
    prompt, new_strategy = build_shuffle_prompt(request.images, request.current_layout, request.style, request.used_strategies)

    user_content = [{"type": "text", "text": prompt}]
    for img in request.images:
        user_content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img}"}})

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{KIMI_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {KIMI_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": "moonshot-v1-8k",
                "messages": [
                    {"role": "system", "content": "你是一位九宫格排版顾问，只输出JSON格式结果。"},
                    {"role": "user", "content": user_content}
                ],
                "temperature": 0.4,
                "response_format": {"type": "json_object"}
            },
            timeout=60.0
        )

    result = response.json()
    shuffle_text = result["choices"][0]["message"]["content"]

    try:
        shuffle_result = json.loads(shuffle_text)
    except:
        # Fallback: random shuffle
        indices = [v["index"] for v in request.current_layout.values()]
        random.shuffle(indices)
        new_layout = {str(i+1): {"index": indices[i], "reason": f"基于{new_strategy}策略重排"} for i in range(9)}
        shuffle_result = {
            "new_layout": new_layout,
            "strategy_name": new_strategy,
            "strategy_description": LAYOUT_STRATEGIES[new_strategy]["description"],
            "changes_made": [{"position": "all", "from_index": "-", "to_index": "-", "reason": "策略切换"}],
            "reasoning": f"切换到{new_strategy}策略"
        }

    return shuffle_result

@app.post("/generate-preview")
async def generate_preview(images: List[str] = Form(...), layout: str = Form(...), background: str = Form("dark")):
    layout_data = json.loads(layout)
    bg_color = (30, 30, 30) if background == "dark" else (245, 245, 245)
    gap = 4
    target_size = 400

    loaded = {}
    for idx_str, item in layout_data.items():
        img_idx = item["index"]
        img_data = base64.b64decode(images[img_idx])
        img = Image.open(io.BytesIO(img_data)).convert("RGB")
        loaded[idx_str] = img

    canvas_size = target_size * 3 + gap * 2
    canvas = Image.new("RGB", (canvas_size, canvas_size), bg_color)

    positions = {
        "1": (0, 0), "2": (target_size + gap, 0), "3": (target_size * 2 + gap * 2, 0),
        "4": (0, target_size + gap), "5": (target_size + gap, target_size + gap), "6": (target_size * 2 + gap * 2, target_size + gap),
        "7": (0, target_size * 2 + gap * 2), "8": (target_size + gap, target_size * 2 + gap * 2), "9": (target_size * 2 + gap * 2, target_size * 2 + gap * 2)
    }

    for idx_str, img in loaded.items():
        img_resized = img.resize((target_size, target_size), Image.Resampling.LANCZOS)
        canvas.paste(img_resized, positions[idx_str])

    buffer = io.BytesIO()
    canvas.save(buffer, format="JPEG", quality=90)
    img_base64 = base64.b64encode(buffer.getvalue()).decode()

    return {"preview_image": f"data:image/jpeg;base64,{img_base64}", "width": canvas_size, "height": canvas_size, "background": background}

@app.get("/styles")
async def list_styles():
    return {
        "styles": list(STYLE_RULES.keys()),
        "strategies": {k: v["description"] for k, v in LAYOUT_STRATEGIES.items()},
        "rules": STYLE_RULES,
        "general_rules": GENERAL_RULES
    }

@app.get("/strategies")
async def list_strategies():
    return {"strategies": LAYOUT_STRATEGIES}

@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "1.1"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
