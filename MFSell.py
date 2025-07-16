from time import sleep
from selenium import webdriver
from selenium.webdriver.common.bidi.storage import StorageKeyPartitionDescriptor
from selenium.webdriver.common.by import By
from selenium.webdriver.support.expected_conditions import presence_of_element_located
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from Create_Order import Create_Fixed_Income
import time
from selenium.common.exceptions import WebDriverException
from datetime import datetime

today_str = datetime.now().strftime('%d-%m-%Y')

LOADER_SELECTOR = 'div.loader-dialog'

def wait_for_loader_to_disappear(max_wait=30, poll_interval=0.5):
    """
    Poll every `poll_interval` seconds up to `max_wait` seconds
    until no loader elements are visible. If the loader is still
    around after max_wait, log a warning and return anyway.
    """
    end_time = time.time() + max_wait
    while time.time() < end_time:
        try:
            loaders = driver.find_elements(By.CSS_SELECTOR, LOADER_SELECTOR)
            # if none found, or all are hidden, we're done
            if not loaders or all(not l.is_displayed() for l in loaders):
                return
        except WebDriverException:
            # in case DOM changes mid-poll
            pass
        time.sleep(poll_interval)

    # fallback after timeout
    print(f"[⚠️] Loader still visible after {max_wait}s — proceeding anyway.")

# --- Helper function ---
def wait_scroll_click(by, value, timeout=15):
    elem = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((by, value)))
    driver.execute_script("arguments[0].scrollIntoView();", elem)
    return elem

# def wait_for_loader_to_disappear(max_wait =60, poll_interval=1)():
#     try:
#         WebDriverWait(driver, 10).until(EC.invisibility_of_element_located((By.CSS_SELECTOR, 'div.loader-dialog')))
#     except:
#         pass  # optional: log warning

# Step 0: Create driver
driver = webdriver.Chrome()

# Step 1: Create Order (includes login)
Create_Fixed_Income(driver)

# Step 2: Wait for OMS Dashboard
wait = WebDriverWait(driver, 15)
wait.until(EC.url_contains("oms_dashboard"))

# Step 3: Enter client code
client_code = wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/app-root/app-dashboard-oms/div[3]/div/div/ul/li/label/input')))
client_code.send_keys('100352')
wait_for_loader_to_disappear(max_wait =60, poll_interval=1)

# Step 4: Click on searched client
client = wait_scroll_click(By.CSS_SELECTOR, '#inProgress > div > div.divTable.dashBoardTable.dashBoardNewTable.divClientTableBody.ng-star-inserted')
client.click()
wait_for_loader_to_disappear(max_wait =60, poll_interval=1)

#Step 5: Click on Mutual Funds tab
MF = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#pills-nse-tab')))
MF.click()
wait_for_loader_to_disappear(max_wait =60, poll_interval=1)