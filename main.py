#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ITUB(Itaú Unibanco, NYSE) 行情追踪
数据源：腾讯财经 qt.gtimg.cn（无需 API Key，全球可访问）
功能：抓最新价 → 追加进 data/itub.csv → 判断阈值 → 可选推送
"""
import csv, os, re, sys, json, urllib.request
from datetime import datetime, timezone, timedelta

SYMBOL   = os.environ.get("SYMBOL", "usITUB")          # 腾讯接口代码
ALERT_PCT = float(os.environ.get("ALERT_PCT", "3"))     # 日涨跌超 ±3% 报警
PRICE_UP  = float(os.environ.get("PRICE_UP", "0"))      # 突破该价报警，0=关闭
PRICE_DN  = float(os.environ.get("PRICE_DN", "0"))      # 跌破该价报警，0=关闭
WEBHOOK   = os.environ.get("WEBHOOK", "")               # 可选：钉钉/企微/Server酱等 webhook
CSV_PATH  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "itub.csv")
BJ = timezone(timedelta(hours=8))


def fetch(url, retries=3):
    last = None
    for _ in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as r:
                return r.read()
        except Exception as e:      # noqa
            last = e
    raise last


def parse(raw: bytes):
    text = raw.decode("gbk", errors="ignore")
    m = re.search(r'"([^"]*)"', text)
    if not m:
        raise ValueError("返回格式异常: " + text[:120])
    f = m.group(1).split("~")
    return {
        "name":    f[1],
        "code":    f[2],
        "price":   float(f[3]),
        "prev":    float(f[4]),
        "open":    f[5],
        "volume":  f[6],
        "high":    f[33] if len(f) > 33 else "",
        "low":     f[34] if len(f) > 34 else "",
        "chg_amt": float(f[31]) if len(f) > 31 and f[31] else 0.0,
        "chg_pct": float(f[32]) if len(f) > 32 and f[32] else 0.0,
        "time":    f[30] if len(f) > 30 else "",
    }


def main():
    q = parse(fetch(f"https://qt.gtimg.cn/q={SYMBOL}"))
    now = datetime.now(BJ).strftime("%Y-%m-%d %H:%M:%S")
    pct = q["chg_pct"] if q["chg_pct"] else (
        (q["price"] - q["prev"]) / q["prev"] * 100 if q["prev"] else 0.0)

    print(f"[{now}] {q['code']} {q['price']:.2f} USD  "
          f"{pct:+.2f}%  昨收 {q['prev']:.2f}  高 {q['high']} 低 {q['low']}")

    os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
    new = not os.path.exists(CSV_PATH)
    with open(CSV_PATH, "a", newline="", encoding="utf-8") as fp:
        w = csv.writer(fp)
        if new:
            w.writerow(["抓取时间(北京)", "代码", "最新价", "昨收", "涨跌幅%", "最高", "最低", "成交量"])
        w.writerow([now, q["code"], q["price"], q["prev"], round(pct, 4),
                    q["high"], q["low"], q["volume"]])

    msgs = []
    if abs(pct) >= ALERT_PCT:
        msgs.append(f"日波动触发：{pct:+.2f}%（阈值 ±{ALERT_PCT}%）")
    if PRICE_UP and q["price"] >= PRICE_UP:
        msgs.append(f"突破 {PRICE_UP} 美元：现价 {q['price']}")
    if PRICE_DN and q["price"] <= PRICE_DN:
        msgs.append(f"跌破 {PRICE_DN} 美元：现价 {q['price']}")

    if msgs:
        text = f"ITUB 提醒\n" + "\n".join(msgs) + f"\n现价 {q['price']} 美元（{pct:+.2f}%）"
        print("ALERT:", text.replace("\n", " | "))
        if WEBHOOK:
            body = json.dumps({"msgtype": "text", "text": {"content": text}}).encode()
            req = urllib.request.Request(WEBHOOK, data=body,
                                         headers={"Content-Type": "application/json"})
            urllib.request.urlopen(req, timeout=15)
            print("已推送 webhook")
    else:
        print("未触发阈值，仅记录")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("抓取失败：", e, file=sys.stderr)
        sys.exit(1)
