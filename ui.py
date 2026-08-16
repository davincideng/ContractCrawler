import webbrowser
import pandas
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtWidgets import (
    QWidget, QLabel, QPushButton, QTextEdit, QLineEdit,
    QFileDialog, QVBoxLayout, QHBoxLayout, QProgressBar,
    QDateEdit, QMessageBox, QCheckBox, QFrame, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QIcon
import os
from worker import CrawlThread
# 修复：正确导入浏览器检测函数、保存csv函数
from crawler import is_browser_installed, save_to_csv

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.browserCombo = QComboBox()
        self.browserCombo.addItems([
            # "Edge",
            "Chrome"
        ])
        self.browserCombo.setFixedHeight(32)

        self.setWindowTitle("池州市合同信息采集系统V1.0")
        self.setWindowIcon(QIcon("icon.ico"))
        self.setFixedSize(1200, 780)

        self.EXPIRE_DATE = QDate(2099, 1, 1)
        self.is_expired = False

        # 日期控件
        self.startDateEdit = QDateEdit()
        self.startDateEdit.setCalendarPopup(True)
        self.startDateEdit.setDate(QDate.currentDate().addMonths(-1))
        self.startDateEdit.setFixedHeight(32)

        self.endDateEdit = QDateEdit()
        self.endDateEdit.setCalendarPopup(True)
        self.endDateEdit.setDate(QDate.currentDate())
        self.endDateEdit.setFixedHeight(32)

        # 无头模式：默认不勾选（前台运行）
        self.headlessCheck = QCheckBox("启用无头模式（后台运行，不显示浏览器）")
        self.headlessCheck.setChecked(False)
        self.headlessCheck.stateChanged.connect(self.update_mode_text)

        # 保存路径
        self.fileEdit = QLineEdit()
        self.fileEdit.setFixedHeight(32)
        self.selectBtn = QPushButton("浏览")
        self.selectBtn.setFixedHeight(32)
        self.selectBtn.setFixedWidth(80)

        # 按钮
        self.startBtn = QPushButton("开始采集")
        self.startBtn.setFixedHeight(32)
        self.startBtn.setFixedWidth(100)

        self.stopBtn = QPushButton("停止采集")
        self.stopBtn.setFixedHeight(32)
        self.stopBtn.setFixedWidth(100)
        self.stopBtn.setEnabled(False)

        self.clearLogBtn = QPushButton("清空日志")
        self.clearLogBtn.setFixedHeight(32)
        self.clearLogBtn.setFixedWidth(100)

        # 进度条、日志
        self.progressBar = QProgressBar()
        self.progressBar.setFixedHeight(22)
        self.logText = QTextEdit()
        self.logText.setReadOnly(True)

        # 布局
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        left_panel = QFrame()
        left_panel.setFixedWidth(220)
        left_panel.setObjectName("LeftPanel")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(16, 24, 16, 24)
        left_layout.setSpacing(12)

        left_title = QLabel("合同采集系统WIN7")
        left_title.setObjectName("LeftTitle")
        left_title.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(left_title)
        left_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed))

        self.status_label = QLabel("状态：已激活")
        self.status_label.setObjectName("StatusLabel")
        self.expire_label = QLabel(f"到期时间：{self.EXPIRE_DATE.toString('yyyy-MM-dd')}")
        self.expire_label.setObjectName("InfoLabel")
        self.ip_label = QLabel("")
        self.ip_label.setObjectName("InfoLabel")
        self.browser_label = QLabel("浏览器：Chrome")
        self.browser_label.setObjectName("InfoLabel")
        mode_label = QLabel("保存格式：CSV")
        mode_label.setObjectName("InfoLabel")

        left_layout.addWidget(self.status_label)
        left_layout.addWidget(self.expire_label)
        left_layout.addWidget(self.ip_label)
        left_layout.addWidget(self.browser_label)
        left_layout.addWidget(mode_label)

        # 新增：浏览器下载区域
        left_layout.addSpacing(20)
        # tip_label = QLabel("浏览器未安装？点击下载：")
        # tip_label.setObjectName("InfoLabel")
        # left_layout.addWidget(tip_label)

        # self.download_edge_btn = QPushButton("下载Edge浏览器")
        # self.download_edge_btn.setFixedHeight(30)
        # self.download_edge_btn.clicked.connect(self.download_edge)
        # left_layout.addWidget(self.download_edge_btn)

        # self.download_chrome_btn = QPushButton("下载 Chrome 浏览器")
        # self.download_chrome_btn.setFixedHeight(30)
        # 修复：正确绑定按钮事件
        # self.download_chrome_btn.clicked.connect(self.download_chrome)
        # left_layout.addWidget(self.download_chrome_btn)

        left_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        main_layout.addWidget(left_panel)

        right_panel = QFrame()
        right_panel.setObjectName("RightPanel")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(16, 16, 16, 16)
        right_layout.setSpacing(10)

        config_card = QFrame()
        config_card.setObjectName("Card")
        config_layout = QVBoxLayout(config_card)
        config_layout.setContentsMargins(16, 16, 16, 16)
        config_layout.setSpacing(10)
        config_title = QLabel("采集配置")
        config_title.setObjectName("CardTitle")
        config_layout.addWidget(config_title)

        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("开始日期"))
        date_layout.addWidget(self.startDateEdit)
        date_layout.addSpacing(15)
        date_layout.addWidget(QLabel("结束日期"))
        date_layout.addWidget(self.endDateEdit)
        config_layout.addLayout(date_layout)

        browser_layout = QHBoxLayout()
        browser_layout.addWidget(QLabel("浏览器"))
        browser_layout.addWidget(self.browserCombo)
        config_layout.addLayout(browser_layout)
        config_layout.addWidget(self.headlessCheck)

        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("保存路径"))
        path_layout.addWidget(self.fileEdit)
        path_layout.addWidget(self.selectBtn)
        config_layout.addLayout(path_layout)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.startBtn)
        btn_layout.addWidget(self.stopBtn)
        btn_layout.addWidget(self.clearLogBtn)
        btn_layout.addStretch()
        config_layout.addLayout(btn_layout)
        right_layout.addWidget(config_card)

        status_card = QFrame()
        status_card.setObjectName("Card")
        status_layout = QVBoxLayout(status_card)
        status_layout.setContentsMargins(16, 16, 16, 16)
        status_layout.setSpacing(8)
        status_title = QLabel("采集进度")
        status_title.setObjectName("CardTitle")
        status_layout.addWidget(status_title)
        status_layout.addWidget(self.progressBar)
        right_layout.addWidget(status_card)

        log_card = QFrame()
        log_card.setObjectName("Card")
        log_layout = QVBoxLayout(log_card)
        log_layout.setContentsMargins(16, 16, 16, 16)
        log_layout.setSpacing(8)
        log_title = QLabel("运行日志")
        log_title.setObjectName("CardTitle")
        log_layout.addWidget(log_title)
        log_layout.addWidget(self.logText, stretch=1)
        right_layout.addWidget(log_card)
        main_layout.addWidget(right_panel)

        self.setStyleSheet("""
        QWidget {
            font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
            font-size: 16px;
            color: #333;
        }
        #LeftPanel {
            background-color: #2B4D77;
        }
        #LeftTitle {
            color: white;
            font-size: 18px;
            font-weight: bold;
        }
        #StatusLabel, #InfoLabel {
            color: #E0E8F0;
        }
        #RightPanel {
            background-color: #F5F7FA;
        }
        #Card {
            background-color: white;
            border-radius: 8px;
            border: 1px solid #E0E5ED;
        }
        #CardTitle {
            font-size: 20px;
            font-weight: bold;
            color: #2B4D77;
            margin-bottom: 4px;
        }
        QLineEdit, QDateEdit {
            background-color: white;
            border: 1px solid #D0D7E3;
            border-radius: 6px;
            padding: 6px 10px;
        }
        QLineEdit:focus, QDateEdit:focus {
            border: 1px solid #4080E0;
        }
        QPushButton {
            background-color: #4080E0;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 6px 12px;
            font-weight: 500;
        }
        QPushButton:hover {
            background-color: #5292F7;
        }
        QPushButton:pressed {
            background-color: #3070D0;
        }
        QPushButton:disabled {
            background-color: #C0C4CC;
            color: #F0F2F5;
        }
        QProgressBar {
            border: none;
            background-color: #E8EDF5;
            border-radius: 12px;
            text-align: center;
            color: #333;
        }
        QProgressBar::chunk {
            background-color: #67C23A;
            border-radius: 12px;
        }
        QTextEdit {
            background-color: white;
            border: 1px solid #D0D7E3;
            border-radius: 6px;
            padding: 8px;
        }
        QCheckBox {
            color: #333;
            spacing: 8px;
        }
        QCheckBox::indicator {
            width: 16px;
            height: 16px;
            border-radius: 3px;
            border: 1px solid #D0D7E3;
        }
        QCheckBox::indicator:checked {
            background-color: #4080E0;
            border: 1px solid #4080E0;
        }
        """)

        # 信号绑定
        self.startDateEdit.dateChanged.connect(self.update_default_filename)
        self.endDateEdit.dateChanged.connect(self.update_default_filename)
        self.selectBtn.clicked.connect(self.select_file)
        self.startBtn.clicked.connect(self.start_crawl)
        self.stopBtn.clicked.connect(self.stop_crawl)
        self.clearLogBtn.clicked.connect(self.clear_log)
        self.browserCombo.currentTextChanged.connect(
            lambda text: self.browser_label.setText(f"浏览器：{text}")
        )

        self.update_mode_text()
        self.update_default_filename()
        self.check_expire()

    # 浏览器下载跳转
    def download_edge(self):
        webbrowser.open("https://www.microsoft.com/zh-cn/edge/download")

    def download_chrome(self):
        webbrowser.open("https://www.google.cn/intl/zh-CN/chrome/")

    def update_default_filename(self):
        """根据日期自动生成完整桌面路径+文件名"""
        start_date = self.startDateEdit.date()
        end_date = self.endDateEdit.date()

        start_year = str(start_date.year())[2:]
        start_month = start_date.month()
        end_year = str(end_date.year())
        end_month = end_date.month()
        end_year_short = str(end_year)[2:]

        if start_date.year() == end_date.year and start_month == end_month:
            filename = f"{start_year}年{start_month}月合同信息.csv"
        elif start_date.year() == end_date.year:
            filename = f"{start_year}年{start_month}月-{end_month}月合同信息.csv"
        else:
            filename = f"{start_year}年{start_month}月-{end_year_short}年{end_month}月合同信息.csv"

        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        full_path = os.path.join(desktop, filename)
        self.fileEdit.setText(full_path)

    def update_mode_text(self):
        if self.headlessCheck.isChecked():
            self.ip_label.setText("采集模式：无头模式")
        else:
            self.ip_label.setText("前台运行")

    def check_expire(self):
        today = QDate.currentDate()
        if today > self.EXPIRE_DATE:
            self.is_expired = True
            self.startBtn.setEnabled(False)
            self.startBtn.setText("已过期")
            self.status_label.setText("状态：已过期")
            QMessageBox.critical(self, "已过期", "软件使用期限已截止\n请联系管理员续费！")
        else:
            self.is_expired = False
            self.startBtn.setEnabled(True)
            self.status_label.setText("状态：已激活")

    def clear_log(self):
        reply = QMessageBox.question(self, "确认", "确定清空所有运行日志吗？",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.logText.clear()

    def select_file(self):
        current_path = self.fileEdit.text()
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "保存文件",
            current_path,
            "CSV Files (*.csv)"
        )
        if filename:
            self.fileEdit.setText(filename)

    # 开始采集
    def start_crawl(self):
        if self.is_expired or QDate.currentDate() > self.EXPIRE_DATE:
            QMessageBox.critical(self, "已过期", "软件已过期，无法采集！")
            return

        start_date_obj = self.startDateEdit.date()
        end_date_obj = self.endDateEdit.date()
        if start_date_obj > end_date_obj:
            QMessageBox.warning(self, "日期错误", "开始日期不能晚于结束日期！")
            return

        save_path = self.fileEdit.text()
        if not save_path:
            QMessageBox.warning(self, "提示", "请选择保存路径")
            return

        browser_type = self.browserCombo.currentText()
        if not is_browser_installed(browser_type):
            QMessageBox.critical(self, "浏览器未安装", f"当前选择的【{browser_type}】浏览器未安装，请先安装对应浏览器！")
            return

        start_date = self.startDateEdit.date().toString("yyyy-MM-dd")
        end_date = self.endDateEdit.date().toString("yyyy-MM-dd")
        headless = self.headlessCheck.isChecked()

        self.progressBar.setValue(0)
        self.startBtn.setEnabled(False)
        self.stopBtn.setEnabled(True)
        self.logText.append(f"开始采集... 浏览器：{browser_type}")

        self.thread = CrawlThread(
            "",
            start_date,
            end_date,
            headless,
            browser_type
        )
        self.thread.log_signal.connect(self.write_log)
        self.thread.progress_signal.connect(self.progressBar.setValue)
        self.thread.finish_signal.connect(self.crawl_finished)
        self.thread.start()

    def stop_crawl(self):
        if hasattr(self, "thread"):
            self.logText.append("正在停止采集...")
            self.thread.stop()
        self.logText.append("用户停止采集")
        self.startBtn.setEnabled(True)
        self.stopBtn.setEnabled(False)

    def crawl_finished(self, data):
        """线程结束回调：增加空数据判断，空数据跳过保存文件"""
        self.startBtn.setEnabled(True)
        self.stopBtn.setEnabled(False)

        # 空数据：异常/初始化失败/任务停止，直接结束，不保存csv
        if not data:
            self.logText.append("任务结束，无有效数据，跳过保存文件")
            QMessageBox.warning(self, "任务结束", "采集未获取有效数据，请查看日志排查问题！")
            return

        save_path = self.fileEdit.text()
        # 调用crawler内部保存函数，统一处理
        save_to_csv(data, save_path)

        self.progressBar.setValue(100)
        self.logText.append(f"文件已保存：{save_path}")
        self.logText.append("采集完成")
        QMessageBox.information(self, "完成", "数据采集完成")

    def write_log(self, msg):
        self.logText.append(msg)
        self.logText.ensureCursorVisible()
