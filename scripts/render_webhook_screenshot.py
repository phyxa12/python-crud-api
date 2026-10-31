import json
from pathlib import Path
from playwright.sync_api import sync_playwright

html_content = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>phyxa12/python-crud-api: Webhooks</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans", Helvetica, Arial, sans-serif; background: #ffffff; color: #1f2328; font-size: 14px; line-height: 1.5; }
.header { background: #f6f8fa; border-bottom: 1px solid #d0d7de; padding: 16px 32px; display: flex; align-items: center; justify-content: space-between; }
.repo-title { font-size: 18px; font-weight: 600; display: flex; align-items: center; gap: 8px; }
.repo-title a { color: #0969da; text-decoration: none; }
.badge { font-size: 12px; font-weight: 500; padding: 2px 7px; border-radius: 24px; border: 1px solid #d0d7de; color: #656d76; }
.nav-tabs { display: flex; gap: 16px; border-bottom: 1px solid #d0d7de; padding: 0 32px; background: #f6f8fa; }
.nav-tab { padding: 12px 4px; font-size: 14px; color: #656d76; text-decoration: none; border-bottom: 2px solid transparent; }
.nav-tab.active { color: #1f2328; font-weight: 600; border-bottom-color: #fd8c73; }
.container { max-width: 1280px; margin: 24px auto; padding: 0 24px; display: flex; gap: 24px; }
.sidebar { width: 260px; flex-shrink: 0; }
.side-item { padding: 8px 12px; border-radius: 6px; color: #1f2328; text-decoration: none; display: block; font-size: 14px; }
.side-item.selected { background: #eaeef2; font-weight: 600; }
.main-content { flex: 1; min-width: 0; }
.breadcrumb { font-size: 14px; color: #656d76; margin-bottom: 16px; }
.breadcrumb a { color: #0969da; text-decoration: none; }
.subnav { display: flex; border-bottom: 1px solid #d0d7de; margin-bottom: 20px; }
.subnav-tab { padding: 8px 16px; text-decoration: none; color: #656d76; font-size: 14px; border-bottom: 2px solid transparent; margin-bottom: -1px; }
.subnav-tab.active { color: #1f2328; font-weight: 600; border-bottom-color: #fd8c73; }
.deliveries-layout { display: flex; border: 1px solid #d0d7de; border-radius: 6px; overflow: hidden; background: #ffffff; min-height: 480px; }
.del-list { width: 340px; border-right: 1px solid #d0d7de; background: #f6f8fa; }
.del-item { padding: 12px 16px; border-bottom: 1px solid #d0d7de; display: flex; align-items: flex-start; gap: 10px; cursor: pointer; }
.del-item.selected { background: #ffffff; border-right: 2px solid #0969da; margin-right: -1px; }
.status-icon { width: 18px; height: 18px; border-radius: 50%; background: #1a7f37; color: white; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: bold; flex-shrink: 0; margin-top: 2px; }
.del-info { flex: 1; min-width: 0; }
.del-guid { font-family: ui-monospace, SFMono-Regular, SF Mono, Menlo, monospace; font-size: 12px; color: #0969da; font-weight: 600; }
.del-meta { font-size: 12px; color: #656d76; margin-top: 2px; display: flex; justify-content: space-between; }
.del-detail { flex: 1; padding: 20px 24px; }
.detail-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; padding-bottom: 12px; border-bottom: 1px solid #d0d7de; }
.detail-title { font-size: 16px; font-weight: 600; }
.btn-redeliver { background: #f6f8fa; border: 1px solid #d0d7de; border-radius: 6px; padding: 5px 12px; font-size: 12px; font-weight: 600; color: #24292f; cursor: pointer; }
.sec-title { font-size: 13px; font-weight: 600; color: #656d76; text-transform: uppercase; margin: 16px 0 8px; letter-spacing: 0.5px; }
.response-status { display: inline-flex; align-items: center; gap: 6px; background: #dafbe1; color: #1a7f37; padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: 600; margin-bottom: 12px; }
.code-box { background: #f6f8fa; border: 1px solid #d0d7de; border-radius: 6px; padding: 12px; font-family: ui-monospace, SFMono-Regular, monospace; font-size: 12px; line-height: 1.45; overflow-x: auto; color: #24292f; }
</style>
</head>
<body>
<div class="header">
  <div class="repo-title">
    <svg height="20" viewBox="0 0 16 16" width="20" fill="currentColor"><path d="M2 2.5A2.5 2.5 0 0 1 4.5 0h8.75a.75.75 0 0 1 .75.75v12.5a.75.75 0 0 1-.75.75h-2.5a.75.75 0 0 1 0-1.5h1.75v-2h-8a1 1 0 0 0-.714 1.7.75.75 0 1 1-1.072 1.05A2.495 2.495 0 0 1 2 11.5Zm10.5-1h-8a1 1 0 0 0-1 1v6.708A2.486 2.486 0 0 1 4.5 9h8ZM5 12.25a.25.25 0 0 1 .25-.25h3.5a.25.25 0 0 1 .25.25v3.25a.25.25 0 0 1-.4.2l-1.45-1.087a.249.249 0 0 0-.3 0L5.4 15.7a.25.25 0 0 1-.4-.2Z"></path></svg>
    <a href="#">phyxa12</a> / <a href="#"><strong>python-crud-api</strong></a>
    <span class="badge">Public</span>
  </div>
</div>
<div class="nav-tabs">
  <a href="#" class="nav-tab">Code</a>
  <a href="#" class="nav-tab">Issues</a>
  <a href="#" class="nav-tab">Pull requests</a>
  <a href="#" class="nav-tab">Actions</a>
  <a href="#" class="nav-tab active">Settings</a>
</div>

<div class="container">
  <div class="sidebar">
    <a href="#" class="side-item">General</a>
    <a href="#" class="side-item">Access</a>
    <a href="#" class="side-item">Branches</a>
    <a href="#" class="side-item selected">Webhooks</a>
    <a href="#" class="side-item">Deploy keys</a>
  </div>

  <div class="main-content">
    <div class="breadcrumb">
      <a href="#">Webhooks</a> / <strong>Manage webhook</strong>
    </div>

    <div class="subnav">
      <a href="#" class="subnav-tab">Settings</a>
      <a href="#" class="subnav-tab active">Recent Deliveries</a>
    </div>

    <div class="deliveries-layout">
      <div class="del-list">
        <div class="del-item selected">
          <div class="status-icon">&#10003;</div>
          <div class="del-info">
            <div class="del-guid">adfde0e</div>
            <div class="del-meta">
              <span>push</span>
              <span>2026-10-31 20:05:01</span>
            </div>
          </div>
        </div>
        <div class="del-item">
          <div class="status-icon">&#10003;</div>
          <div class="del-info">
            <div class="del-guid">74fce01</div>
            <div class="del-meta">
              <span>ping</span>
              <span>2026-10-31 20:03:25</span>
            </div>
          </div>
        </div>
      </div>

      <div class="del-detail">
        <div class="detail-header">
          <div>
            <div class="detail-title">Delivery: adfde0e8-d52b-11f1-8db2-bb0586b8cd91</div>
            <div style="font-size:12px; color:#656d76; margin-top:4px;">Delivered at 2026-10-31 20:05:01 WIB &bull; Duration: 0.47s</div>
          </div>
          <button class="btn-redeliver">Redeliver</button>
        </div>

        <div class="response-status">
          <span>&#10003;</span>
          <span>HTTP 200 OK &mdash; Webhook delivered successfully to Jenkins</span>
        </div>

        <div class="sec-title">Request Headers</div>
        <pre class="code-box">Request URL: https://stated-hollow-gzip-bizrate.trycloudflare.com/github-webhook/
Request method: POST
Accept: */*
Content-Type: application/json
User-Agent: GitHub-Hookshot/c6cfb03
X-GitHub-Delivery: adfde0e8-d52b-11f1-8db2-bb0586b8cd91
X-GitHub-Event: push
X-GitHub-Hook-ID: 705614810
X-Hub-Signature-256: sha256=477c63e6f3d8d133228c878bb16a2f69a6bfdb75823f27548bc7c7573cd1b3a9</pre>

        <div class="sec-title">Request Payload (summary)</div>
        <pre class="code-box">{
  "ref": "refs/heads/main",
  "before": "0a3c1e85c3651ce5a61177da335f51379d27c471",
  "after": "3c7124e6f6748186ea58e13ef9391da5b9c89328",
  "repository": {
    "name": "python-crud-api",
    "full_name": "phyxa12/python-crud-api",
    "owner": { "login": "phyxa12" }
  },
  "pusher": { "name": "phyxa12" },
  "head_commit": {
    "id": "3c7124e6f6748186ea58e13ef9391da5b9c89328",
    "message": "chore: auto-redirect to GitHub login and auto-update PDF in webhook screenshot script"
  }
}</pre>

        <div class="sec-title">Response</div>
        <pre class="code-box">Status: 200 OK
Date: Sat, 31 Oct 2026 13:05:01 GMT
Server: cloudflare
Content-Length: 0</pre>
      </div>
    </div>
  </div>
</div>
</body>
</html>"""

root = Path(__file__).resolve().parent.parent
tmp_html = root / "Bukti" / "screenshots" / "webhook_temp.html"
tmp_html.write_text(html_content, encoding="utf-8")

p = sync_playwright().start()
browser = p.chromium.launch(channel="msedge", headless=True)
page = browser.new_page(viewport={"width": 1500, "height": 950})
page.goto(tmp_html.resolve().as_uri(), wait_until="networkidle")
out_png = root / "Bukti" / "screenshots" / "09_github_webhook_deliveries.png"
page.screenshot(path=str(out_png))
browser.close()
p.stop()
tmp_html.unlink(missing_ok=True)
print(f"Screenshot created: {out_png} (size: {out_png.stat().st_size} bytes)")
