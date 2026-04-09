import os
import time
import shutil
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

# --- NEW IMPORTS FOR SMART WAITS ---
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from db import getdb
from rediscon import redis_conn

# returns the whole reult , it's not parsed in any way or another , that will be handled based on the job Type whiel retrvign datat to create a excel 
#fiel output for the user 
def demo(pan_id, pass_id, job_id, request_id):
    #postgress db connection
    conn = getdb()
    cursor = conn.cursor()
    
    erro_info = None
    driver = None 
    
    #selenium base Setup , repeats for each Job
    try:
        options = Options()
        rail = os.getenv("ENV")
        
        if rail is not None and rail == "RAILWAY":
            options.binary_location = "/usr/bin/chromium"
            
            prefs = {
                "credentials_enable_service": False,
                "profile.password_manager_enabled": False,
                "profile.password_manager_leak_detection": False
            }
            options.add_experimental_option("prefs", prefs)
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option("useAutomationExtension", False)

            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--start-maximized")
            options.add_argument("--disable-infobars")

            # Headless setup
            options.add_argument("--headless=new")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--window-size=1920,1080")

            service = Service(executable_path="/usr/bin/chromedriver")
            driver = webdriver.Chrome(service=service, options=options)
            
        else:
            options.binary_location = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
            prefs = {
                "credentials_enable_service": False,
                "profile.password_manager_enabled": False,
                "profile.password_manager_leak_detection": False
            }
            options.add_experimental_option("prefs", prefs)
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option("useAutomationExtension", False)

            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--start-maximized")
            options.add_argument("--disable-infobars")

            # Headless setup
            options.add_argument("--headless=new")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--window-size=1920,1080")

            service = Service(
                executable_path="/mnt/f/wg/chrome/chromedriver-win64/chromedriver-win64/chromedriver.exe"
            )
            driver = webdriver.Chrome(service=service, options=options)
            
        driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        ## ---------- base setup ends ----------

        # Create a Wait object (Wait up to 20 seconds for elements to appear)
        wait = WebDriverWait(driver, 20)

        # ---------- open site ----------
        driver.get("https://eportal.incometax.gov.in/iec/foservices/#/login")

        # ---------- username ----------
        pan_input = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@id='panAdhaarUserId']")))
        pan_input.send_keys(pan_id)

        continue_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(),' Continue ')]")))
        driver.execute_script("arguments[0].click();", continue_btn)

        # ---------- password mode ----------
        pwd_checkbox = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@id='passwordCheckBox-input']")))
        driver.execute_script("arguments[0].click();", pwd_checkbox)

        # Wait just to make sure the password field is actually visible before the loop starts
        pw = wait.until(EC.visibility_of_element_located((By.ID, "loginPasswordField")))

        # ---------- password typing (UNTOUCHED) ----------
        pwd = pass_id
        for c in pwd:
            pw.send_keys(c)
            time.sleep(0.15)

        time.sleep(2)
        pw.send_keys(Keys.ENTER)
        # ------------------------------------------------

        # ---------- login here popup ----------
        # Wrapped in a try/except because this popup doesn't always appear. 
        # Waits max 5 seconds for it. If it doesn't show up, it just moves on smoothly.
        try:
            short_wait = WebDriverWait(driver, 5)
            login_here_btn = short_wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Login Here')]")))
            driver.execute_script("arguments[0].click();", login_here_btn)
        except TimeoutException:
            pass # Popup didn't appear, continue as normal

        # ---------- navigation ----------
        services_tab = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(),' Services')]")))
        driver.execute_script("arguments[0].click();", services_tab)

        refund_status_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(),' Refund Status')]")))
        driver.execute_script("arguments[0].click();", refund_status_btn)

        # ---------- dropdown & submit ----------
        dropdown = wait.until(EC.element_to_be_clickable((By.XPATH, "//mat-select[@formcontrolname]")))
        driver.execute_script("arguments[0].click();", dropdown)

        year_option = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[@class='mdc-list-item__primary-text' and contains(text(),'2023-24')]")))
        driver.execute_script("arguments[0].click();", year_option)

        submit_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Submit') and @class='large-button-primary']")))
        driver.execute_script("arguments[0].click();", submit_btn)

        # ---------- extract status ----------
        status_td = wait.until(EC.visibility_of_element_located((By.XPATH, "(//th[text()=' Status ']/parent::tr/following-sibling::tr//td)[1]")))
        status = status_td.text

        print("Refund status:", status)
    
    except Exception as e:
        erro_info = str(e)
    
    finally: 
        if driver is not None:
            driver.quit()
        
    ## end =-== seleniunmm 
    
    if erro_info is not None:
        insert_query = """INSERT INTO job_results (job_id, success, error , output)
                    VALUES (%s::uuid, %s, %s, %s)
                    RETURNING id;"""
        cursor.execute(insert_query, (job_id, False, erro_info, None))
        conn.commit()
        sucess =  False
    else:
        insert_query = """INSERT INTO job_results (job_id, success, error , output)
                        VALUES (%s::uuid, %s, %s, %s)
                        RETURNING id;"""
        cursor.execute(insert_query, (job_id, True, None, status))
        conn.commit()
        sucess =  True
    
    remaining = redis_conn.decr(f"batch:{request_id}:remaining")

    if remaining <= 0:
        redis_conn.publish("batch_complete", request_id)
        
    return sucess