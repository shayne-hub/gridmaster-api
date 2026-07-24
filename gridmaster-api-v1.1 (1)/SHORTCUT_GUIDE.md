# iOS 快捷指令配置（含"换一组"）

## 图片数量要求
- **最少 9 张**：少于9张无法组成九宫格，会提示"图片数量不足"
- **最多 16 张**：超过16张会提示"图片数量过多，建议控制在9-16张"
- **最佳范围**：10-12张，给AI足够的选择空间

## 主指令：AI九宫格

1. 创建快捷指令，开启"在共享表单中显示"，类型"图像"
2. 添加操作：

### 操作1：获取变量
- 选择 "快捷指令输入"

### 操作2：计数（检查图片数量）
- 选择 "计数" → 输入：快捷指令输入
- 存入变量：ImageCount

### 操作3：如果（图片数量 < 9）
- 条件：ImageCount < 9
- 则：显示提醒 "图片数量不足，请至少选择9张图"
- 停止快捷指令

### 操作4：如果（图片数量 > 16）
- 条件：ImageCount > 16
- 则：显示提醒 "图片数量过多，建议控制在9-16张，方便AI精选"
- 停止快捷指令

### 操作5：Base64编码
- 选择 "Base64编码"
- 输入：快捷指令输入
- 行：每行一个

### 操作6：文本（构建JSON）
```
{"images": [编码结果], "style_hint": "", "strategy": "经典中心"}
```

### 操作7：获取URL内容（调用API）
- 方法：POST
- URL：https://your-api-url/analyze
- 请求体：文件（选择上面的文本）
- Content-Type：application/json

### 操作8：如果（API返回错误）
- 条件：URL结果包含 "error"
- 则：显示提醒 "[错误] 图片数量需在9-16张之间"
- 停止快捷指令

### 操作9：获取词典值
- 获取键：layout_suggestion
- 存入变量：CurrentLayout

### 操作10：获取词典值
- 获取键：style_detected
- 存入变量：CurrentStyle

### 操作11：获取词典值
- 获取键：recommended_indices
- 存入变量：SelectedIndices

### 操作12：获取词典值
- 获取键：available_strategies
- 存入变量：AvailableStrategies

### 操作13：显示结果
- 选择 "显示结果"
- 内容：排版建议文字

### 操作14：生成预览图
- 文本：`{"images": [编码结果], "layout": [CurrentLayout], "background": "dark"}`
- 获取URL内容 → POST到 /generate-preview
- 获取词典值 → preview_image
- Base64解码 → 显示图像

### 操作15：询问用户
- 问题："保存预览图还是换一组？"
- 选项："保存", "换一组"

### 操作16：如果（选择"保存"）
- 存储当前预览图到相簿
- 显示提醒 "已保存到相册！去朋友圈按顺序选图发布吧"

### 操作17：如果（选择"换一组"）
- 运行快捷指令 "九宫格换一组"
  - 传入：CurrentLayout, CurrentStyle, 编码结果, ["经典中心"]

## 子指令：九宫格换一组

1. 创建快捷指令，名称："九宫格换一组"
2. 接收输入：layout, style, images, used_strategies

### 操作1：文本（构建JSON）
```
{"images": [images], "current_layout": [layout], "style": [style], "used_strategies": [used_strategies]}
```

### 操作2：获取URL内容
- 方法：POST
- URL：https://your-api-url/shuffle
- 请求体：文件

### 操作3：获取词典值
- 获取键：new_layout
- 更新变量：CurrentLayout

### 操作4：获取词典值
- 获取键：strategy_name
- 显示提醒 "已切换至 [strategy_name] 策略"

### 操作5：获取词典值
- 获取键：changes_made
- 显示 "变动说明"

### 操作6：生成新预览图
- 文本：`{"images": [images], "layout": [CurrentLayout], "background": "dark"}`
- 获取URL内容 → POST到 /generate-preview
- Base64解码 → 显示图像

### 操作7：更新已用策略列表
- 将 strategy_name 添加到 used_strategies

### 操作8：再次询问
- 问题："保存还是再换一组？"
- 选项："保存", "再换一组"
- 如果选择"再换一组"，重复操作1-8

## 注意事项

- 首次运行需允许"不受信任的快捷指令"
- 图片数量严格限制：9 ≤ 张数 ≤ 16
- "换一组"会记录已用策略，6种用完后自动重置
- 预览图保存后，去朋友圈按1-9顺序选图即可
