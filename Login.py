from time import sleep

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def perform_Login(driver):
    driver.get('https://startuat.theneoworld.com/')
    driver.delete_all_cookies()
    wait = WebDriverWait(driver, 15)

    # Enter email
    username_box = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@name='email']")))
    username_box.send_keys('Tanmay.Rane@Neo-world.com')
    sleep(3)

    # Click submit
    login_box = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Submit']")))
    login_box.click()
    sleep(3)

    # Enter OTP
    otp_box = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@name='otp']")))
    otp_box.send_keys('123456')  # Use real OTP here if required
    sleep(3)

    # Click Verify
    verify_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Verify & Login']")))
    verify_btn.click()
    sleep(5)
