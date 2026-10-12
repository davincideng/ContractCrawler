# 池州市合同信息采集系统

基于 **PyQt5 + Selenium** 的合同信息采集工具，用于抓取[池州市公共资源交易网](https://ggj.chizhou.gov.cn/front/bidcontent/9005001006)的合同公告，并将结果导出为 CSV 文件。

## 功能特性

- 图形界面操作，支持按 **开始日期 / 结束日期** 筛选采集范围
- 支持 **前台运行** 与 **无头模式**（后台运行，不弹出浏览器）
- 支持 **开始 / 停止 / 清空日志**，实时进度条与运行日志
- 自动翻页采集全部列表页，逐条进入详情页提取合同字段
- 导出 UTF-8-BOM 编码的 CSV（Excel 直接打开不乱码）
- 兼容 Windows 7（自动降级为传统 headless 参数）

## 目录结构

```
ContractCrawler/
├── main.py            # 程序入口
├── ui.py              # PyQt5 界面
├── worker.py          # 采集线程（QThread 封装）
├── crawler.py         # 采集核心逻辑（Selenium）
├── requirements.txt   # 依赖清单
├── icon.ico           # 程序图标
├── contracts.csv      # CSV 表头示例
└── driver/            # 浏览器驱动目录（需自行放置，见下）
    └── chromedriver.exe
```

## 环境要求

- Python **3.8**
- Google Chrome 浏览器（已安装）
- 与本机 Chrome 版本匹配的 `chromedriver.exe`
  - 下载地址：<https://googlechromelabs.github.io/chrome-for-testing/>
  - 下载后放到项目 `driver/` 目录下，即 `driver/chromedriver.exe`
  - 打包后程序会从 exe 同级目录的 `driver/` 中查找驱动

## 安装依赖

```bash
cd ContractCrawler
python -m venv .venv
venv\Scripts\activate
pip install -r requirements.txt
```

## 运行指令

开发环境直接运行：

```bash
python main.py
```

### 使用步骤

1. 选择 **开始日期** 和 **结束日期**（默认近一个月）
2. 选择浏览器（当前为 Chrome），确认本机已安装对应浏览器
3. 按需勾选 **启用无头模式**（后台运行）
4. 设置 **保存路径**（默认保存到桌面，文件名按日期自动生成）
5. 点击 **开始采集**，等待进度完成，日志区会显示采集详情
6. 采集结束后自动生成 CSV 文件

> 也可单独调试采集逻辑（不启动界面）：
> ```bash
> python crawler.py
> ```

## 打包指令

使用 PyInstaller 打包为单文件窗口程序：

```bash
pip install pyinstaller
pyinstaller --noconfirm --clean --windowed --name main --icon icon.ico --add-data "driver;driver" main.py
```

或使用历史配置的 `main.spec`（该文件已被 `.gitignore` 忽略，可从 Git 历史恢复）：

```bash
pyinstaller main.spec
```

打包产物位于 `dist/` 目录：

- `dist/main.exe`
- 首次运行前请确认 `dist/driver/chromedriver.exe` 存在（`--add-data` 会一并打包）
- 如需自定义名称，可将 `main.exe` 重命名为 `信息采集系统.exe`

## 导出字段

CSV 输出的列如下：

| 字段 | 说明 |
| --- | --- |
| 合同编号 | 合同编号 |
| 合同名称 | 合同名称 |
| 合同甲方名称 | 甲方单位 |
| 合同乙方名称 | 乙方单位 |
| 合同金额（元） | 合同金额 |
| 合同签订日期 | 签订日期 |
| 合同附件链接 | 附件下载地址 |
| 合同网页链接 | 详情页地址 |
| 合同发布日期 | 公告发布/筛选日期 |

## 常见问题

- **提示"未找到 chromedriver.exe"**：请下载与 Chrome 版本匹配的驱动并放入 `driver/` 目录。
- **提示浏览器未安装**：程序通过常规安装路径检测浏览器，请安装到默认位置。
- **Win7 采集异常**：Win7 最高支持 Chrome/Edge 109，请使用对应版本的浏览器与驱动；无头模式会自动使用传统 `--headless` 参数。
- **采集无数据**：查看运行日志排查，可能是日期范围无数据或网络加载超时（脚本内置自动重试）。

## 分支说明

- `dev_win7`：Windows 7 适配分支
- `dev_win10`：Windows 10 适配分支
- `master`：主分支
