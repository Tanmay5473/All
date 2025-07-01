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

#Step 5: Click on AIF Tab
AIF = wait.until(EC.presence_of_element_located((By.TAG_NAME, 'AIF')))
AIF.click()
wait_for_loader_to_disappear(max_wait =60, poll_interval=1)

#Select Transaction Type

#Step 6: Trade Date
Trade_Date = wait_scroll_click(By.XPATH, '/html/body/app-root/app-mf-place-order/div[2]/div/div/div[1]/div/form/div[2]/div[1]/label/mat-form-field/div[1]/div[2]/div[1]/input')
Trade_Date.clear()
Trade_Date.send_keys(today_str)
wait_for_loader_to_disappear(max_wait=60, poll_interval=1)

#Step 7: Select Manufacturer
Manufacturer = wait_scroll_click(By.XPATH, '/html/body/app-root/app-aif-place-order/div[2]/div/div/div/div/div[2]/form/div/div[3]/div/div[1]/mat-form-field/div[1]/div[2]/div/input').click()
Select_Manufacturer = wait_scroll_click(By.XPATH, '/html/body/div[2]/div/div/div/mat-option[1]').click()
wait_for_loader_to_disappear(max_wait=60, poll_interval=1)

#Step 8: Select Scheme
Scheme = wait_scroll_click(By.XPATH, '/html/body/app-root/app-aif-place-order/div[2]/div/div/div/div/div[2]/form/div/div[4]/div/div[1]/mat-form-field/div[1]/div[2]/div/input').click()
Scheme_select = wait_scroll_click(By.XPATH, '/html/body/div[2]/div/div/div/mat-option[1]/span').click()
wait_for_loader_to_disappear(max_wait=60, poll_interval=1)

#Step 9: Enter Folio Number
Folio_no = wait_scroll_click(By.XPATH, '/html/body/app-root/app-aif-place-order/div[2]/div/div/div/div/div[2]/form/div/div[6]/label/input')
Folio_no.send_keys('1234455')
wait_for_loader_to_disappear(max_wait=60, poll_interval=1)

#Step 10: Enter Commitment Amount
Cmitmnt_AMT = wait_scroll_click(By.XPATH, '/html/body/app-root/app-aif-place-order/div[2]/div/div/div/div/div[2]/form/div/div[7]/label/input').send_keys('2,00,00,000')
wait_for_loader_to_disappear(max_wait=60, poll_interval=1)

#Step 11: Drawn AMT
Drawn_AMT = wait_scroll_click(By.XPATH, '/html/body/app-root/app-aif-place-order/div[2]/div/div/div/div/div[2]/form/div/div[8]/label/input').send_keys('1,00,00,000')
wait_for_loader_to_disappear(max_wait=60, poll_interval=1)

# step 12: Equalization amount
Equi_AMT = wait_scroll_click(By.XPATH, '/html/body/app-root/app-aif-place-order/div[2]/div/div/div/div/div[2]/form/div/div[9]/label/input').send_keys('1,00,00,000')
wait_for_loader_to_disappear(max_wait=60, poll_interval=1)

#Step 13: Click Consent
driver.execute_script("window.scrollBy(0, 500);")
clk_Cnst = wait_scroll_click(By.XPATH, '//*[@id="flexCheckDefault"]').click()
wait_for_loader_to_disappear(max_wait=60, poll_interval=1)

#Step 14: Upload DOcument
Docmnt = wait.until(presence_of_element_located((By.XPATH, '/html/body/app-root/app-mf-place-order/div[2]/div/div/div[1]/div/form/div[2]/div[14]/div[2]/input')))
# driver.execute_script("arguments[0]scrollIntoView();", Consent)
file_input = r'C:\Users\TanmayRane\Downloads\Non-Individual (4)\NEO000006898-KRA-1.pdf'
Docmnt.send_keys(file_input)

#Step 15: Add to cart
Adv_cart = wait_scroll_click(By.XPATH, '/html/body/app-root/app-mf-place-order/div[2]/div/div/div[1]/div/form/div[2]/div[15]/button[1]')
Adv_cart.click()
wait_for_loader_to_disappear(max_wait=60, poll_interval=1)
Oki = wait_scroll_click(By.XPATH, '/html/body/app-root/app-mf-place-order/div[2]/div/div/div[2]/div/button')
Oki.click()
wait_for_loader_to_disappear(max_wait=60, poll_interval=1)

#Step 16: View Cart
Vwe_Cart = wait_scroll_click(By.XPATH, '/html/body/app-root/app-mf-place-order/div[2]/div/div/div[1]/div/form/div[2]/div[15]/button[2]').click()
wait_for_loader_to_disappear(max_wait=60, poll_interval=1)

#Step 17: Submit
Subm = wait_scroll_click(By.XPATH, '/html/body/app-root/app-mf-place-order/div[3]/div/div/div/div/button').click()
wait_for_loader_to_disappear(max_wait=60, poll_interval=1)
Yesss = wait_scroll_click(By.XPATH, '/html/body/app-root/app-mf-place-order/div[3]/div/div/div/div[2]/div/button[1]').click()
wait_for_loader_to_disappear(max_wait=60, poll_interval=1)









