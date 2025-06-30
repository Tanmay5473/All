from time import sleep
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from Create_Order import Create_Fixed_Income

# --- Helper function ---
def wait_scroll_click(by, value, timeout=15):
    elem = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((by, value)))
    driver.execute_script("arguments[0].scrollIntoView();", elem)
    return elem

def wait_for_loader_to_disappear():
    try:
        WebDriverWait(driver, 10).until(EC.invisibility_of_element_located((By.CSS_SELECTOR, 'div.loader-dialog')))
    except:
        pass  # optional: log warning

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
sleep(1)

# Step 4: Click on searched client
client = wait_scroll_click(By.CSS_SELECTOR, '#inProgress > div > div.divTable.dashBoardTable.dashBoardNewTable.divClientTableBody.ng-star-inserted')
client.click()
wait_for_loader_to_disappear()

# Step 5: Click Fixed Income tab
Fixed_Income = wait_scroll_click(By.XPATH, '//*[@id="pills-bond-tab"]')
Fixed_Income.click()
wait_for_loader_to_disappear()

# Step 6: Enter Security Name
security_name = wait_scroll_click(By.XPATH, '/html/body/app-root/app-place-order-cxodashboard/div[2]/div/div/div[1]/div/div[2]/form/div[2]/div/div[1]/div[1]/div[1]/mat-form-field/div[1]/div[2]/div/input')
security_name.send_keys('2')

security_selection = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div/div/div/mat-option[1]')))
security_selection.click()
wait_for_loader_to_disappear()

# Step 7: Quantity
quantity = wait_scroll_click(By.XPATH, '//*[@id=" "]/div[1]/div[3]/div/div/div[1]/label/input')
quantity.send_keys('10')

# Step 8: Total Consideration
total_consideration = wait_scroll_click(By.XPATH, '//*[@id=" "]/div[1]/div[3]/div[1]/div/div[2]/label/input')
total_consideration.send_keys('10')

# Step 9: Offline Consent Checkbox
offline_consent_check = wait_scroll_click(By.XPATH, '//*[@id="flexCheckDefault"]')
offline_consent_check.click()

# Step 10: Upload Consent PDF
consent_upload = wait.until(EC.presence_of_element_located((By.XPATH,'//*[@id="documentFile"]')))
driver.execute_script("arguments[0].scrollIntoView();", consent_upload)
file_input = r'C:\Users\TanmayRane\Downloads\Non-Individual (4)\NEO000006898-KRA-1.pdf'
consent_upload.send_keys(file_input)

# Step 11: Add to cart
addtocart = wait_scroll_click(By.XPATH, '//*[@id="filterSubmit"]')
addtocart.click()
wait_for_loader_to_disappear()

# Step 12: Click OK
click_ok = wait_scroll_click(By.XPATH, '/html/body/app-root/app-place-order-cxodashboard/div[3]/div/button')
click_ok.click()
wait_for_loader_to_disappear()

# Step 13: View Cart
view_cart = wait_scroll_click(By.XPATH, '//*[@id=" "]/div[2]/button[2]')
view_cart.click()
wait_for_loader_to_disappear()

# Step 14: Submit Cart
Submit = wait_scroll_click(By.XPATH, '//*[@id="filterSubmit"]')
Submit.click()
wait_for_loader_to_disappear()

# Step 15: Confirm Submit
Yes = wait_scroll_click(By.XPATH, '/html/body/app-root/app-place-order-cxodashboard/div[3]/div/div/div[2]/div/button[1]')
Yes.click()
sleep(2)

driver.quit()
