import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from selenium.webdriver.common.action_chains import ActionChains  # 用于模拟鼠标动作
from datetime import datetime  # 用于时间解析和计算
import timeSelect
import json  # 新增：导入json模块

with open('config.json', 'r') as f:
    config = json.load(f)

TARGET_URL = config["TARGET_URL"]
INPUT_DATA = config["INPUT_DATA"]
WAIT_TIME = config["WAIT_TIME"]



# ---------------------- 核心改造：使用undetected-chromedriver ----------------------
if __name__ == "__main__":
    # 1. 启动隐藏特征的Chrome浏览器（无需手动配置ChromeDriver，UCD会自动匹配版本）
    driver = uc.Chrome()
    driver.maximize_window()
    print("已启动隐藏自动化特征的浏览器，正在访问网站...")

    try:
        driver.get(TARGET_URL)
        # 等待继续按钮加载
        WebDriverWait(driver, WAIT_TIME).until(
            EC.presence_of_element_located((By.CLASS_NAME, "ui-button"))
        )

        # 3. 点击继续按钮、输入信息等操作（同之前脚本，无需修改）
        continue_btn = driver.find_element(By.CLASS_NAME, "ui-button")
        continue_btn.click()
        time.sleep(1)

        continue_btn = driver.find_element(By.CLASS_NAME, "ui-button")
        continue_btn.click()
        time.sleep(1)
        # 输入驾照编号
        dl_input = WebDriverWait(driver, WAIT_TIME).until(
            EC.presence_of_element_located((By.ID, "CleanBookingDEForm:dlNumber"))
        )
        dl_input.clear()
        dl_input.send_keys(INPUT_DATA["dlNumber"])
        print("已输入驾照编号")

        # 输入联系人姓名
        contact_input = driver.find_element(By.ID, "CleanBookingDEForm:contactName")
        contact_input.clear()
        contact_input.send_keys(INPUT_DATA["contactName"])
        print("已输入联系人姓名")

        contactPhone = driver.find_element(By.ID, "CleanBookingDEForm:contactPhone")
        contactPhone.clear()
        contactPhone.send_keys(INPUT_DATA["contactPhone"])
        print("已输入手机号")
        try:

            # 1. 点击下拉框按钮，展开选项列表
            dropdown_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "CleanBookingDEForm:productType"))
            )
            dropdown_button.click()
            time.sleep(1)  # 等待选项展开

            # 2. 定位目标选项（以"Class C/CA - Car"为例）
            target_option = WebDriverWait(driver, 10).until(
                # 确保选项可见且可交互
                EC.visibility_of_element_located((
                    By.XPATH,
                    f'//ul[@id="CleanBookingDEForm:productType_items"]/li[text()="{INPUT_DATA["Test type"]}"]'
                ))
            )

            # 3. 用ActionChains模拟鼠标移动并点击（关键步骤）
            actions = ActionChains(driver)
            actions.move_to_element(target_option).click().perform()  # 移动到选项并点击
            print("选项点击成功！")
            time.sleep(2)  # 观察效果
        except Exception as e:
            print(f"操作失败：{e}")

        continue_btn = driver.find_element(By.CLASS_NAME, "ui-button")
        continue_btn.click()
        time.sleep(2)
        continue_btn = driver.find_element(By.CLASS_NAME, "ui-button")
        continue_btn.click()
        time.sleep(2)

        try:

            # 1. 点击下拉框按钮，展开选项列表
            dropdown_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "BookingSearchForm:region_label"))
            )
            dropdown_button.click()
            time.sleep(1)  # 等待选项展开

            # 2. 定位目标选项（以"Class C/CA - Car"为例）
            target_option = WebDriverWait(driver, 10).until(
                # 确保选项可见且可交互
                EC.visibility_of_element_located((
                    By.XPATH,
                    f'//ul[@id="BookingSearchForm:region_items"]/li[text()="{INPUT_DATA["Region"]}"]'
                ))
            )

            # 3. 用ActionChains模拟鼠标移动并点击（关键步骤）
            actions = ActionChains(driver)
            actions.move_to_element(target_option).click().perform()  # 移动到选项并点击
            print("选项点击成功！")
            time.sleep(1)  # 观察效果
        except Exception as e:
            print(f"操作失败：{e}")
        try:

            # 1. 点击下拉框按钮，展开选项列表
            dropdown_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "BookingSearchForm:centre"))
            )
            dropdown_button.click()
            time.sleep(1)  # 等待选项展开

            target_option = WebDriverWait(driver, 10).until(
                # 确保选项可见且可交互
                EC.visibility_of_element_located((
                    By.XPATH,
                    f'//ul[@id="BookingSearchForm:centre_items"]/li[text()="{INPUT_DATA["Centre"]}"]'
                ))
            )

            # 3. 用ActionChains模拟鼠标移动并点击（关键步骤）
            actions = ActionChains(driver)
            actions.move_to_element(target_option).click().perform()  # 移动到选项并点击
            print("选项点击成功！")
            time.sleep(1)  # 观察效果
        except Exception as e:
            print(f"操作失败：{e}")

        continue_btn = driver.find_element(By.CLASS_NAME, "ui-button")
        continue_btn.click()
        time.sleep(2)

        # 5 Select time列表

        # 2. 等待预约表格页面加载（关键：确保进入时间选择页面）
        print("\n等待预约时间表格加载...")
        WebDriverWait(driver, WAIT_TIME).until(
            EC.visibility_of_element_located((By.ID, "slotSelectionForm:slotTable"))
        )
        time.sleep(2)

        # 3. 调用时间检测函数，点击最接近的时段
        target_datetime = datetime.strptime(INPUT_DATA["Target Time"], "%Y-%m-%d %H:%M")
        success = timeSelect.final_select_near_time(
            driver=driver,
            target_time=target_datetime,  # 传入datetime对象
            tolerance=INPUT_DATA["Time Tolerance"]
        )

        if not success:
            print(str(datetime.now()) + "未成功选择任何时段")

        #  成功选中进入下一页
        continue_btn = driver.find_element(By.CLASS_NAME, "ui-button")
        continue_btn.click()
        time.sleep(1)
        continue_btn = driver.find_element(By.CLASS_NAME, "ui-button")
        continue_btn.click()
        time.sleep(1)

        #进入Email填写界面
        contactEmail = driver.find_element(By.ID, "paymentOptionSelectionForm:paymentOptions:emailAddressField:emailAddress")
        contactEmail.clear()
        contactEmail.send_keys(INPUT_DATA["contactEmail"])
        print("已输入邮箱")
        continue_btn = driver.find_element(By.CLASS_NAME, "ui-button")
        continue_btn.click()
        time.sleep(3)
        #进入付款界面
        contactCard = driver.find_element(By.ID, "CardNumber")
        contactCard.clear()
        contactCard.send_keys(INPUT_DATA["CardNumber"])

        contactMonth = driver.find_element(By.ID, "ExpiryMonth")
        contactMonth.clear()
        contactMonth.send_keys(INPUT_DATA["ExpiryMonth"])

        contactYear = driver.find_element(By.ID, "ExpiryYear")
        contactYear.clear()
        contactYear.send_keys(INPUT_DATA["ExpiryYear"])

        contactCVN = driver.find_element(By.ID, "CVN")
        contactCVN.clear()
        contactCVN.send_keys(INPUT_DATA["CVN"])

        continue_btn = driver.find_element(By.ID, "btnReviewPayment")
        continue_btn.click()
        time.sleep(1)

    except Exception as e:
        print(f"脚本出错：{e}")
    finally:
        input("按回车键关闭浏览器...")
        driver.quit()
