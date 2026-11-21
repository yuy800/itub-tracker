# ITUB 行情追踪（GitHub 免费跑）

跟踪 **ITUB**（Itaú Unibanco，NYSE ADR）每个交易日收盘后的价格，自动记录成 CSV，
涨跌幅超过阈值时推送到你的群机器人。

## 先说清楚：GitHub 上那台"免费电脑"是什么

| | GitHub Codespaces | GitHub Actions |
|---|---|---|
| 本质 | 云端 VS Code + 一台 Linux 开发机（2 核 / 8 G / 30 G） | 临时容器，跑完即销毁 |
| 免费额度 | GitHub Free：**120 核小时/月、15 GB 存储** | **公开仓库标准 runner 不计分钟** |
| 会一直开着吗 | ❌ 空闲 **30 分钟**自动停；单次最长 12 小时 | ❌ 每次任务跑完就结束，单 job 上限 6 小时 |
| 适合 | 你坐下来写代码、调试 | **定时任务、爬数据、跑脚本** |
| 不用了会怎样 | 停止后 **30 天**不访问自动删除 | 无状态，下次照跑 |

结论：**Codespaces 是"给你用的电脑"，不是"替你 7×24 干活的服务器"。**
追股票这种每天抓一次的事，用 Actions，才是真正零成本、永久免费。

## 三步上线

1. **注册 GitHub**（只要邮箱，不需要信用卡、不需要实名）。
2. **新建仓库**：Repository name 填 `itub-tracker`，可见性选 **Public**
   （公开仓库的 Actions 才不计分钟）。
3. **上传文件**：把本目录里的这些原样传上去，目录结构必须保持：

```
itub-tracker/
├── main.py
├── .github/
│   └── workflows/
│       └── itub.yml
└── data/            # 会自动生成 itub.csv，不用先建
```

上传完点仓库顶部 **Actions** 标签 → 左侧 `itub-tracker` → 右侧 **Run workflow** 手动跑一次，
成功后会看到日志里打印 `ITUB.N 6.52 USD -2.54%`，同时 `data/itub.csv` 多出一行。

## 改阈值（不用改代码）

在仓库 **Settings → Secrets and variables → Actions → Variables** 里加：

| 变量名 | 含义 | 例子 |
|---|---|---|
| `ALERT_PCT` | 日涨跌超过多少百分比就报警 | `3` |
| `PRICE_UP` | 突破这个价报警，0 表示关闭 | `7.2` |
| `PRICE_DN` | 跌破这个价报警，0 表示关闭 | `6.0` |

## 想收到手机通知（可选）

1. 在钉钉/企业微信群里加一个**群机器人**，拿到 Webhook 地址。
2. 仓库 **Settings → Secrets → Actions → New repository secret**，
   名字填 `WEBHOOK`，值粘那个地址。
3. 触发阈值时，脚本会把消息 POST 过去。没配就只写 CSV，不推送。

## 时间与数据源说明

- **cron 是 UTC**。`30 22 * * 1-5` = 北京时间次日 06:30，美股收盘后，冬夏令时都覆盖。
  GitHub 的定时是"尽量准时"，高峰期可能延迟几分钟到几十分钟，做收盘复盘足够。
- 数据源用的是**腾讯财经 `qt.gtimg.cn`**，无需 API Key，字段与交易所一致。
  Yahoo 和 stooq 现在分别有请求拦截和 JS 验证，脚本里已避开。
- 脚本只用 Python 标准库，`requirements.txt` 都不用。

## 风险与注意

- 公开仓库意味着**代码和 CSV 都是公开的**。别往里写密钥、别提交私人数据；
  敏感配置一律放在 Secrets。
- 公开仓库的定时任务若 **60 天**没有任何提交活动，schedule 会被自动停用。
  想保活，就让脚本顺手提交一行数据（本模板已经在做）。
- 这不是投资建议，只是一台记录价格和提醒的工具。
