import time
from datetime import datetime
import math
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

WAIT_TIME = 20  # 延长等待时间到20秒，确保元素加载


def final_select_near_time(driver, target_time, tolerance):
    try:
        # 1. 获取所有行数据并筛选最优时段
        rows = WebDriverWait(driver, WAIT_TIME).until(
            EC.presence_of_all_elements_located((By.XPATH, '//tbody[@id="slotSelectionForm:slotTable_data"]/tr'))
        )
        valid_slots = []
        for row in rows:
            # 提取时间文本（确保元素可见）
            time_label = WebDriverWait(row, WAIT_TIME).until(
                EC.visibility_of_element_located((By.XPATH, './td[2]/label'))
            )
            time_text = time_label.text.strip()

            # 解析时间并计算差值
            try:
                slot_time = datetime.strptime(time_text, "%A, %d %B %Y %I:%M %p")
                diff = math.fabs((slot_time - target_time).total_seconds() / 60)
                if diff <= tolerance:
                    valid_slots.append((diff, time_text, row))
            except Exception as e:
                print(f"时间解析失败（{time_text}）：{e}")
                continue

        if not valid_slots:
            print("无符合条件时段")
            return False

        # 2. 确定最优时段并获取其行索引（data-ri）
        best_diff, best_text, best_row = sorted(valid_slots, key=lambda x: x[0])[0]
        data_ri = best_row.get_attribute("data-ri")
        print(f"\n最优时段：{best_text}（差{int(best_diff)}分钟），对应data-ri={data_ri}")

        # 3. 强制通过data-ri定位单选框（最稳定的方式）
        radio_xpath = f'//tbody[@id="slotSelectionForm:slotTable_data"]/tr[@data-ri="{data_ri}"]//div[@class="ui-radiobutton-box"]'
        print(f"定位路径：{radio_xpath}")  # 打印路径用于调试

        # 1. 定位目标行（先激活行）
        row_xpath = f'//tbody[@id="slotSelectionForm:slotTable_data"]/tr[@data-ri="{data_ri}"]'
        target_row = WebDriverWait(driver, WAIT_TIME).until(
            EC.element_to_be_clickable((By.XPATH, row_xpath))
        )

        # 2. 点击行激活（用户通常会先点行再点单选框）
        driver.execute_script("arguments[0].click();", target_row)
        time.sleep(0.5)  # 等待行激活状态更新

        # 1. 获取最优行的data-rk属性（这是表单提交的关键值）
        data_rk = best_row.get_attribute("data-rk")
        print(f"目标行的data-rk值：{data_rk}")

        # 2. 定位表单隐藏字段（用于记录选中状态）
        hidden_input = WebDriverWait(driver, WAIT_TIME).until(
            EC.presence_of_element_located((By.ID, "slotSelectionForm:slotTable_selection"))
        )

        # 3. 直接修改隐藏字段的值（模拟选中）
        driver.execute_script(f"arguments[0].value = '{data_rk}';", hidden_input)
        # 4. 触发表单变更事件，让页面识别选中状态
        driver.execute_script("""
            var event = new Event('change', {bubbles: true});
            arguments[0].dispatchEvent(event);
        """, hidden_input)

        print(f"已直接修改表单值为：{data_rk}（无需点击UI）")
        return True

    except Exception as e:
        print(f"详细错误：{str(e)}")
        return False
