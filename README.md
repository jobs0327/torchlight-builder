# Torchlight Builder

这是一个基于 **Vue 3 + TypeScript（Vite）** 的前端项目，用于展示《Torchlight》相关的英雄与天赋/特性信息，并在“特性选择”与“英雄数值计算模块”之间建立联动。

---

## 快速开始（前端）

### 1. 安装依赖

```bash
npm install
```

### 2. 启动开发服务器

```bash
npm run dev
```

启动后服务默认运行在 `http://localhost:3000`（端口来自 `vite.config.ts`）。

### 3. 构建 / 预览

```bash
npm run build
npm run preview
```

补充：项目根目录提供了一个 `start-dev.sh`，用于在类 Unix 环境下启动并检查/占用 `3000` 端口（Windows 不是必须）。

---

## 英雄数据生成（Python）

英雄数据会从服务器抓取得到的原始数据（`data/` 目录）中解析并生成前端可用的 JSON：

- 输入：
  - `data/Hero.json`：英雄列表页的原始 HTML（用于抽取 hero 卡片：slug、portrait、displayName、shortDesc）
  - `data/<slug>.json`：英雄特性详情页（用于抽取每个特性：name、requiredLevel、effects、icon）
- 输出：
  - `torchlight-builder/src/data/heroes/heroes.json`

### 1. 生成英雄数据

在项目根目录执行：

```bash
python build_hero_data.py
```

脚本入口与关键路径（供排查）：

- `build_hero_data.py`：
  - `HERO_INDEX_FILE = data/Hero.json`
  - `OUT_FILE = torchlight-builder/src/data/heroes/heroes.json`

### 2. Python 依赖

```bash
pip install -r requirements.txt
```

---

## 前端页面与“特性 -> 联动数值”的机制

### 1. 选择逻辑（互斥）

在 `src/views/Hero.vue` 中，每个英雄的特性卡片都有：

- 一个“选中按钮”（对同一个 `requiredLevel` 只能选中其中一个特性）
- 展开/收起按钮（用于展示 effect 细节）

### 2. 数值模块如何接收选择结果

`Hero.vue` 会把当前左侧已选特性名传给英雄对应的 Summary 组件：

- 传参格式：`selectedTraits: string[]`
- 传参前会对字符串统一 `trim()`（避免首尾空格导致匹配失败）

Summary 组件通常在 `src/components/hero/` 下，以 `HeroSummary*.vue` 命名。

### 3. 新增/修复联动组件的维护要点

如果你要新增一个英雄数值计算模块或修复联动：

1. 在 `Hero.vue` 的 `heroSummaryMap` 里确保组件映射正确（hero.id -> 组件）
2. 在 `Hero.vue` 的 `heroSummaryProps` 白名单里把该 hero.id 加入（否则组件收不到 `selectedTraits`）
3. 在 Summary 组件里：
   - 声明 `selectedTraits?: string[]`
   - 依据 `selectedTraits` 做 `Set.has('特性名')` 判断
   - 对未勾选分支：要么不渲染输入/结果，要么贡献值按 0 处理

---

## 目录说明（快速定位）

- `torchlight-builder/src/views/`
  - `Hero.vue`：英雄详情页（左侧特性选择 + 右侧动态数值模块渲染）
- `torchlight-builder/src/components/hero/`
  - `HeroSummary*.vue`：各英雄的数值计算模块
- `torchlight-builder/src/data/`
  - `heroes/heroes.json`：英雄与特性结构化数据（由 Python 脚本生成）

---

## 备注

- 若你发现某个英雄“勾了但不计算”，优先检查：
  - `Hero.vue` 是否已把该英雄加入 `heroSummaryProps` 白名单
  - Summary 组件里 `selectedTraits` 的匹配字符串是否与 `heroes.json` 里的特性名完全一致
- `npm run build` 可能会受到本地 Node/Vue 工具链版本差异影响；如需要可单独在项目内排查。

