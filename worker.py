from PyQt5.QtCore import QThread, pyqtSignal
from crawler import ContractCrawler

class CrawlThread(QThread):
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    finish_signal = pyqtSignal(list)

    def __init__(
            self,
            keyword,
            start_date,
            end_date,
            headless,
            browser_type):
        super().__init__()
        self.keyword = keyword
        self.start_date = start_date
        self.end_date = end_date
        self.headless = headless
        self.browser_type = browser_type
        self._stopped = False
        self.crawler = None

    def stop(self):
        self._stopped = True
        try:
            if self.crawler:
                self.crawler.stopped = True
        except Exception:
            pass

    def is_stopped(self):
        return self._stopped

    def send_log(self, msg):
        self.log_signal.emit(msg)

    def send_progress(self, value):
        self.progress_signal.emit(value)

    def run(self):
        try:
            self._stopped = False
            self.crawler = ContractCrawler()
            data = self.crawler.run(
                keyword=self.keyword,
                start_date=self.start_date,
                end_date=self.end_date,
                callback=self.log_signal.emit,
                progress_callback=self.progress_signal.emit,
                is_stopped=lambda: self._stopped,
                headless=self.headless,
                browser_type=self.browser_type
            )
            if data is None:
                data = []
            self.finish_signal.emit(data)
        except Exception as e:
            self.log_signal.emit(f"运行异常：{str(e)}")
            self.finish_signal.emit([])