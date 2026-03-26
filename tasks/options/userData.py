import time
from selenium import webdriver
from selenium.webdriver.firefox.service import Service

#selenium setup 
# service = Service("/mnt/c/tools/geckodriver.exe")
# driver = webdriver.Firefox(service=service)

def userData(pan_id,pass_id):
    print(pan_id)
    print(pass_id)
    service = Service("/mnt/c/tools/geckodriver.exe")
    driver = webdriver.Firefox(service=service)
    driver.get("https://www.google.com")
    time.sleep(5)
    driver.quit()
    return True