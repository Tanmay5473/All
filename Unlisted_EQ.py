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

#Step 5: Click on Unlisted EQ tab
unlisted_EQ = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="pills-sp-tab"]')))
unlisted_EQ.click()
wait_for_loader_to_disappear(max_wait =60, poll_interval=1)

#Step 6: Select Security
security_sel = wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/app-root/app-place-order-cxodashboard/div[2]/div/div/div[1]/div/div[2]/form/div[2]/div/div[1]/div[1]/div[1]/mat-form-field/div[1]/div[2]/div/input')))
security_sel.send_keys("S")
wait_for_loader_to_disappear(max_wait =60, poll_interval=1)

#Step 7: Select Security
security_select = wait_scroll_click(By.XPATH, '/html/body/div/div/div/div/mat-option[1]/span')
security_select.click()
wait_for_loader_to_disappear(max_wait =60, poll_interval=1)

#Step 8: Enter Entity
Entity_Input = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="mat-input-4"]'))).click()
Entity_Sel = wait_scroll_click(By.XPATH,'//*[@id="mat-option-12"]/span').click()
wait_for_loader_to_disappear(max_wait =60, poll_interval=1)

#Step 9: Enter Quntity
Quantity = wait_scroll_click(By.XPATH, "/html/body/app-root/app-place-order-cxodashboard/div[2]/div/div/div[1]/div/div[2]/form/div[2]/div/div[1]/div[3]/div/div/div[1]/label/input")
Quantity.send_keys('1')
wait_for_loader_to_disappear(max_wait =60, poll_interval=1)

#Step 10: Enter Price
Pricing = wait_scroll_click(By.XPATH, "/html/body/app-root/app-place-order-cxodashboard/div[2]/div/div/div[1]/div/div[2]/form/div[2]/div/div[1]/div[3]/div/div/div[2]/label/input")
Pricing.send_keys("100")
wait_for_loader_to_disappear(max_wait =60, poll_interval=1)

#Step 11: Calculate Stamp Duty and Tax
Stamp_duty = wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/app-root/app-place-order-cxodashboard/div[2]/div/div/div[1]/div/div[2]/form/div[2]/div/div[1]/div[3]/div/div/div[4]/div/button')))
Stamp_duty.click()
wait_for_loader_to_disappear(max_wait =60, poll_interval=1)

#Step 12: Enter Margin
margin = wait_scroll_click(By.XPATH, '/html/body/app-root/app-place-order-cxodashboard/div[2]/div/div/div[1]/div/div[2]/form/div[2]/div/div[1]/div[4]/div[5]/label/input')
margin.send_keys("12")
wait_for_loader_to_disappear(max_wait =60, poll_interval=1)

#Step 13: Select Offline Consent
Offline_consent = wait_scroll_click(By.XPATH, '//*[@id="flexCheckDefault"]')
Offline_consent.click()
wait_for_loader_to_disappear(max_wait =60, poll_interval=1)

#Step 14: Upload Consent
Consent = wait.until(presence_of_element_located((By.XPATH, '/html/body/app-root/app-place-order-cxodashboard/div[2]/div/div/div[1]/div/div[2]/form/div[2]/div/div[1]/div[5]/div[2]/input')))
# driver.execute_script("arguments[0]scrollIntoView();", Consent)
file_input = r'C:\Users\TanmayRane\Downloads\Non-Individual (4)\NEO000006898-KRA-1.pdf'
Consent.send_keys(file_input)

#Step 15: Add to Cart
Add_Cart = wait_scroll_click(By.XPATH, '/html/body/app-root/app-place-order-cxodashboard/div[2]/div/div/div[1]/div/div[2]/form/div[2]/div/div[2]/button[1]')
Add_Cart.click()
wait_for_loader_to_disappear(max_wait =60, poll_interval=1)

#Click OK
OK_btn = wait_scroll_click(By.XPATH, '/html/body/app-root/app-place-order-cxodashboard/div[3]/div/button')
OK_btn.click()
wait_for_loader_to_disappear(max_wait =60, poll_interval=1)

#Step 16: View Cart
View_Cart = wait_scroll_click(By.XPATH, '/html/body/app-root/app-place-order-cxodashboard/div[2]/div/div/div[1]/div/div[2]/form/div[2]/div/div[2]/button[2]')
View_Cart.click()
wait_for_loader_to_disappear(max_wait =60, poll_interval=1)

#Step 17: Submit
Submit = wait_scroll_click(By.XPATH, '/html/body/app-root/app-place-order-cxodashboard/div[3]/div/div/div/div/div/button')
Submit.click()
wait_for_loader_to_disappear(max_wait =60, poll_interval=1)

# Step 15: Confirm Submit
Yes = wait_scroll_click(By.XPATH, '/html/body/app-root/app-place-order-cxodashboard/div[3]/div/div/div[2]/div/button[1]')
Yes.click()
sleep(2)

driver.quit()



