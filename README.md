# GMGN 情报站

按时间线展示本 bot 收集到的 GMGN **功能 / 招聘 / 教程** 更新，最新在最上。

## 公网地址

| | |
|--|--|
| **GitHub Pages** | https://str-bin.github.io/gmgn-intel/ |
| **仓库** | https://github.com/str-bin/gmgn-intel |

站点为纯静态：`index.html` + `timeline.json`，由 GitHub Pages 从 `main` 分支根目录托管。

## 文件

| 文件 | 说明 |
|------|------|
| `index.html` | 单页时间线（已内嵌数据，可直接打开；有服务器时会再拉 `timeline.json`） |
| `timeline.json` | 权威情报数组（newest-first） |
| `build.py` | 从基线 + `updates/` 重新生成上述文件 |
| `updates/` | 追加新情报的 JSON（可选） |
| `build-meta.json` | 最近一次生成统计 |

基线文件在工作区上一级目录（不进本仓库）：

- `../gmgn-features-baseline.json`
- `../gmgn-careers-baseline.json`
- `../gmgn-tutorials-baseline.json`

## 例行更新流程（本地 → 公网）

1. 例行扫描发现新内容后：
   - 更新对应 baseline JSON，**或**
   - 在 `updates/` 下放一个 JSON 文件（单条对象、数组、或 `{"items":[...]}`），字段与 `timeline.json` 条目一致。
2. 运行：

```bash
python3 build.py
```

3. 脚本会写回工作区站点目录（并镜像到 store `site/`）。
4. **同步到 GitHub Pages**（在已 clone 本仓库的目录，或从工作区拷贝后）：

```bash
# 若工作副本在 /tmp/gmgn-intel-deploy 或任意 clone：
cp /workspace/gmgn-intel/index.html /workspace/gmgn-intel/timeline.json /workspace/gmgn-intel/build-meta.json .
# 如有新 updates/*.json 一并拷入 updates/
git add index.html timeline.json build-meta.json updates/
git commit -m "Update intel timeline"
git push origin main
```

约 1 分钟后公网页面会刷新。Pages 源：`main` / root。

条目需含：`id`, `date`, `datetime`, `category`（功能|招聘|教程）, `title`, `summary`, `source_url`, `source_label`, `collected_at`。

## 本地预览

```bash
cd /workspace/gmgn-intel
python3 -m http.server 8765
# 打开 http://127.0.0.1:8765/
```
