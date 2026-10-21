# GMGN 情报站

按时间线展示本 bot 收集到的 GMGN **功能 / 招聘 / 教程** 更新，最新在最上。左侧为正在盯着的账号与网站，右侧为时间线。

## 公网地址

| | |
|--|--|
| **Cloudflare Pages（主公网）** | https://gmgn-intel.pages.dev/ |
| GitHub Pages（次要/可选） | https://str-bin.github.io/gmgn-intel/ |
| 源码仓库（非公网入口） | https://github.com/str-bin/gmgn-intel |

日常请用 **Cloudflare Pages** 链接分享；它不暴露 GitHub 用户名。GitHub Pages 仅作备份/可选同步。

站点为纯静态：`index.html` + `timeline.json`。Cloudflare 项目名：`gmgn-intel`（Direct Upload，无 Git 连接）。

## 文件

| 文件 | 说明 |
|------|------|
| `index.html` | 单页时间线（已内嵌数据，可直接打开；有服务器时会再拉 `timeline.json`） |
| `timeline.json` | 权威情报数组（newest-first） |
| `build.py` | 从基线 + `updates/` 重新生成上述文件；支持 `--no-new` / `--has-new` / `--new-count` 写入扫描结果 |
| `updates/` | 追加新情报的 JSON（可选） |
| `build-meta.json` | 最近一次生成统计（含 last_checked / scan_result） |
| `scan-status.json` | 最近一次扫描时间与结果（有新增 / 无新增）；例行扫描即使无新增也要更新并部署 |

基线文件在工作区上一级目录（不进本仓库）：

- `../gmgn-features-baseline.json`
- `../gmgn-careers-baseline.json`
- `../gmgn-tutorials-baseline.json`

## 例行更新流程（本地 → Cloudflare 公网）

1. 例行扫描结束后（无论有无新增）：更新 baseline 的 `last_checked`；有新内容则写 baseline / `updates/`。
2. 运行：`python3 build.py --no-new` 或 `python3 build.py --has-new --new-count N`（会写入 `scan-status.json` 并刷新页头「最近扫描 / 本次」）。
3. **即使无新增也要部署**到 Cloudflare Pages，让公网站点时间及时。
4. **部署到 Cloudflare Pages**（Direct Upload，推荐）：

```bash
# 需要 Cloudflare API Token（Pages Edit）或通过已授权的 user-Cloudflare MCP：
# 1) GET upload-token for project gmgn-intel
# 2) BLAKE3-hash assets (base64(content)+ext without dot, first 32 hex)
# 3) POST /pages/assets/check-missing + upload + upsert-hashes (Bearer upload JWT)
# 4) POST /accounts/{account_id}/pages/projects/gmgn-intel/deployments with multipart manifest

# 或若本机有 CLOUDFLARE_API_TOKEN：
CLOUDFLARE_ACCOUNT_ID=647f8d4a9431e60660aa60270bf00127 \
  npx wrangler pages deploy /workspace/gmgn-intel \
  --project-name=gmgn-intel \
  --commit-dirty=true
```

可选：继续 `git push` 到 GitHub Pages 作次要镜像（会暴露仓库所有者名，一般不必）。

条目需含：`id`, `date`, `datetime`, `category`（功能|招聘|教程）, `title`, `summary`, `source_url`, `source_label`, `collected_at`。

## 本地预览

```bash
cd /workspace/gmgn-intel
python3 -m http.server 8765
# 打开 http://127.0.0.1:8765/
```

## Direct Upload 注意（2026-10-20）

资产上传与 deployment manifest 都必须用 **bare blake3 hash（32 hex）** 作为 key。
若上传写成 `hash.ext`、部署却用 bare hash，公网会出现 HTTP 500。
脚本：`pages-direct-upload.py`（写入 `/tmp/gmgn-pages-manifest.json`），再经 Cloudflare MCP 创建 deployment。
