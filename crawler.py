from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.edge.service import Service as EdgeService
# 自动驱动依赖
from webdriver_manager.microsoft import EdgeChromiumDriverManager
import pandas as pd
import time
import random
import os
import sys

# -------------------------- 无需手动配置驱动路径 --------------------------
# -------------------------- 核心配置项 --------------------------
LIST_URL = "https://ggj.chizhou.gov.cn/front/bidcontent/9005001006"
CSV_FILE_NAME = "contracts_all_pages.csv"
BASE_DELAY = 1
MAX_RETRY = 5
PAGE_LOAD_TIMEOUT = 120

# ===============================================================
def find_browser_path(browser_type):
    """常规路径检测浏览器本体（仅用于检查是否安装，不用于驱动）"""
    possible_paths = []
    if browser_type == "Edge":
        possible_paths = [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
        ]
    elif browser_type == "Chrome":
        possible_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
        ]
    else:
        return None

    for path in possible_paths:
        if os.path.exists(path):
            return path
    return None

def find_chromedriver():
    """
    查找项目内chromedriver
    """

    base_dir = os.path.dirname(
        os.path.abspath(__file__)
    )

    paths = [
        # 项目driver目录
        os.path.join(
            base_dir,
            "driver",
            "chromedriver.exe"
        ),

        # 当前目录
        os.path.join(
            base_dir,
            "chromedriver.exe"
        ),

        # 系统目录
        r"C:\Program Files\Google\Chrome\Application\chromedriver.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chromedriver.exe"
    ]


    for path in paths:
        if os.path.exists(path):
            print("找到ChromeDriver:", path)
            return path


    return None

def is_browser_installed(browser_type):
    """检测浏览器是否安装"""
    browser_path = find_browser_path(browser_type)
    return browser_path is not None

# ===============================================================
def init_browser(browser_type="Edge", headless=True):
    """
    自动获取匹配版本浏览器驱动，无需手动下载配置
    """
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    ]
    driver = None

    if browser_type == "Chrome":

        options = webdriver.ChromeOptions()

        if headless:
            options.add_argument("--headless=new")

        options.add_argument("--disable-gpu")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")

        options.add_argument(
            f"user-agent={random.choice(user_agents)}"
        )

        driver_path = find_chromedriver()

        if not driver_path:
            raise Exception(
                "未找到chromedriver.exe，请放到程序目录"
            )

        service = ChromeService(
            executable_path=driver_path
        )

        driver = webdriver.Chrome(
            service=service,
            options=options
        )

    elif browser_type == "Edge":
        from selenium.webdriver.edge.options import Options as EdgeOptions
        options = EdgeOptions()
        if headless:
            options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument(f"user-agent={random.choice(user_agents)}")
        # Edge自动适配驱动
        service = EdgeService(EdgeChromiumDriverManager().install())
        driver = webdriver.Edge(service=service, options=options)

    else:
        raise ValueError(f"不支持的浏览器类型：{browser_type}")

    if not driver:
        raise Exception("浏览器初始化失败")

    driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
    driver.set_script_timeout(PAGE_LOAD_TIMEOUT)
    driver.implicitly_wait(10)
    # 去除webdriver检测
    driver.execute_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")
    return driver

# -------------------------- 页面解析逻辑 --------------------------
def get_detail_links_from_current_page(driver):
    try:
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "a")))
        time.sleep(random.uniform(0.2, 0.5))
        all_links = driver.find_elements(By.TAG_NAME, "a")
        detail_links = []
        for link in all_links:
            try:
                href = link.get_attribute("href")
                if href and "front/bidcontent/" in href and len(href) > 60:
                    detail_links.append(href)
            except Exception:
                continue
        return detail_links
    except Exception as e:
        print(f"获取链接失败：{str(e)}")
        return []

def extract_contract_info(driver, url):
    for retry in range(MAX_RETRY):
        try:
            driver.get(url)
            WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.TAG_NAME, "table")))
            time.sleep(random.uniform(0.5, 1))
            contract_data = {}
            table_rows = driver.find_elements(By.TAG_NAME, "tr")
            for row in table_rows:
                cols = row.find_elements(By.TAG_NAME, "td")
                if len(cols) == 2:
                    key = cols[0].text.strip()
                    value = cols[1].text.strip()
                    contract_data[key] = value

            attachment_link = ""
            try:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
                attachment_elem = WebDriverWait(driver, 8).until(
                    EC.presence_of_element_located((By.XPATH,
                    '//a[contains(@href, "newShowFile") or contains(@title, "附件") or contains(text(), "附件")]'))
                )
                attachment_link = attachment_elem.get_attribute("href")
                if attachment_link and not attachment_link.startswith("http"):
                    attachment_link = "https://ggj.chizhou.gov.cn" + attachment_link
            except Exception:
                pass

            target_data = {
                "合同编号": contract_data.get("合同编号", ""),
                "合同名称": contract_data.get("合同名称", ""),
                "合同甲方名称": contract_data.get("合同甲方名称", ""),
                "合同乙方名称": contract_data.get("合同乙方名称", ""),
                "合同金额（元）": contract_data.get("合同金额（元）", ""),
                "合同签订日期": contract_data.get("合同签订日期", ""),
                "合同附件链接": attachment_link,
                "合同网页链接": url,
                "合同发布日期": contract_data.get("合同发布日期", "")
            }
            return target_data
        except Exception as e:
            if retry < MAX_RETRY - 1:
                driver.refresh()
                time.sleep(2)
                continue
            else:
                return None

def save_to_csv(data_list, filename):
    if not data_list:
        print("❌ 无数据")
        return
    df = pd.DataFrame(data_list)
    df.to_csv(filename, index=False, encoding="utf-8-sig")

def click_next_page(driver):
    try:
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CLASS_NAME, "laypage_main")))
        next_btn = driver.find_element(By.CSS_SELECTOR, "a.laypage_next")
        if "laypage_disabled" in next_btn.get_attribute("class"):
            return False
        driver.execute_script("arguments[0].scrollIntoView(true);", next_btn)
        time.sleep(0.5)
        next_btn.click()
        time.sleep(random.uniform(1, 1.5))
        return True
    except Exception:
        return False

# -------------------------- 采集主类 --------------------------
class ContractCrawler:
    def __init__(self):
        self.stopped = False
        self.browser = None

    def run(
            self,
            keyword="",
            start_date="",
            end_date="",
            callback=None,
            progress_callback=None,
            is_stopped=None,
            headless=True,
            browser_type="Edge"):
        self.browser = None
        try:
            if callback:
                callback("正在初始化浏览器...")
            self.browser = init_browser(browser_type, headless)
            browser = self.browser

            all_detail_links = []
            current_page = 1
            if callback:
                callback("正在打开网站...")
            browser.get(LIST_URL)
            time.sleep(3)

            if start_date and end_date:
                if callback:
                    callback(f"设置查询日期：{start_date} ~ {end_date}")
                browser.execute_script("""
                    $('#startTime').datebox('setValue', arguments[0]);
                    $('#endTime').datebox('setValue', arguments[1]);
                """, start_date, end_date)
                time.sleep(1)
            try:
                search_btn = browser.find_element(By.XPATH, "//*[contains(text(),'搜索')]")
                search_btn.click()
                if callback:
                    callback("执行搜索")
                time.sleep(5)
            except Exception as e:
                if callback:
                    callback(f"搜索按钮点击失败: {e}")

            while True:
                if is_stopped and is_stopped():
                    if callback:
                        callback("任务已停止")
                    return []
                page_links = get_detail_links_from_current_page(browser)
                all_detail_links.extend(page_links)
                if callback:
                    callback(f"第 {current_page} 页获取到 {len(page_links)} 条")
                if not click_next_page(browser):
                    break
                current_page += 1

            total = len(all_detail_links)
            if callback:
                callback(f"共发现 {total} 个合同链接")
            all_contract_data = []
            for idx, link in enumerate(all_detail_links, start=1):
                if is_stopped and is_stopped():
                    if callback:
                        callback("任务已停止")
                    return all_contract_data
                if callback:
                    callback(f"[{idx}/{total}] 正在采集...")
                info = extract_contract_info(browser, link)
                if info:
                    publish_date = info.get("合同发布日期", "")
                    if start_date and publish_date and publish_date < start_date:
                        continue
                    if end_date and publish_date and publish_date > end_date:
                        continue
                    if keyword:
                        text = info.get("合同名称", "") + info.get("合同甲方名称", "") + info.get("合同乙方名称", "")
                        if keyword not in text:
                            continue
                    all_contract_data.append(info)
                if progress_callback:
                    progress = int(idx * 100 / total)
                    progress_callback(progress)
                time.sleep(random.uniform(0.5, 1))

            if callback:
                callback(f"采集完成，共{len(all_contract_data)}条")
            return all_contract_data

        except Exception as e:
            err_msg = str(e)
            if callback:
                callback(f"程序异常: {err_msg}")
            return []
        finally:
            if self.browser:
                try:
                    self.browser.quit()
                except Exception:
                    pass

# -------------------------- 测试入口 --------------------------
if __name__ == "__main__":
    # 测试运行
    crawler = ContractCrawler()
    data = crawler.run(
        start_date="2026-07-06",
        end_date="2026-08-06",
        headless=True,          # False弹出浏览器窗口调试
        browser_type="Chrome",  # 可选 Chrome / Edge
        callback=print,
        progress_callback=lambda p: print(f"进度: {p}%")
    )
    if data:
        save_to_csv(data, "test_output.csv")
        print(f"已保存 {len(data)} 条数据")
