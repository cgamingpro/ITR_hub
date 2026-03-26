import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys



def demo(pan_id,pass_id):
    options = Options()
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

    # ---------- open site ----------
    driver.get("https://eportal.incometax.gov.in/iec/foservices/#/login")
    time.sleep(5)

    # ---------- username ----------
    driver.find_element(By.XPATH, "//input[@id='panAdhaarUserId']").send_keys(pan_id)

    driver.find_element(By.XPATH, "//span[contains(text(),' Continue ')]").click()
    time.sleep(2)

    # ---------- password mode ----------
    driver.find_element(By.XPATH, "//input[@id='passwordCheckBox-input']").click()
    time.sleep(3)

    # ---------- password typing ----------
    pwd = pass_id
    pw = driver.find_element(By.ID, "loginPasswordField")

    for c in pwd:
        pw.send_keys(c)
        time.sleep(0.15)

    time.sleep(2)
    pw.send_keys(Keys.ENTER)

    time.sleep(3)

    # ---------- login here popup ----------
    notices = driver.find_elements(By.XPATH, "//button[contains(text(),'Login Here')]")
    if len(notices) > 0:
        notices[0].click()
        time.sleep(2)

    # ---------- navigation ----------
    time.sleep(2)

    driver.find_element(By.XPATH, "//span[contains(text(),' Services')]").click()
    driver.find_element(By.XPATH, "//span[contains(text(),' Refund Status')]").click()

    time.sleep(2)

    driver.find_element(By.XPATH, "//mat-select[@formcontrolname]").click()

    driver.find_element(
        By.XPATH,
        "//span[@class='mdc-list-item__primary-text' and contains(text(),'2023-24')]"
    ).click()

    driver.find_element(
        By.XPATH,
        "//button[contains(text(),'Submit') and @class='large-button-primary']"
    ).click()

    time.sleep(2)

    status = driver.find_element(
        By.XPATH,
        "(//th[text()=' Status ']/parent::tr/following-sibling::tr//td)[1]"
    ).text

    print("Refund status:", status)
    

    return True
    
    