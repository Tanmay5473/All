from time import sleep

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from Login import perform_Login

def Create_Fixed_Income(driver):
    # Step 1: Login
    perform_Login(driver)

    # Step 2: Wait for dashboard
    wait = WebDriverWait(driver, 15)
    wait.until(EC.url_contains("/landing-page"))

    # Step 3: Click Create Order
    create_order_element = wait.until(EC.element_to_be_clickable((
        By.XPATH, "/html/body/app-root/app-landing-component/body/div[1]/div/div/ul/li[1]/ul/li[4]/div"
    )))
    create_order_element.click()
    sleep(5)