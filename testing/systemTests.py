import unittest
import multiprocessing
import os
import time

from Explorate import create_app
from Explorate.config import TestingConfig
from Explorate.models import db, User, Adventure, UserSelection, Recommendations, Ratings
from werkzeug.security import generate_password_hash

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions

localHost = "http://127.0.0.1:5000/"

def run_flask_app():
    app = create_app(TestingConfig)
    app.run(use_reloader=False)

class SystemTests(unittest.TestCase):
    def setUp(self):
        self.app_ctx = create_app(TestingConfig).app_context()
        self.app_ctx.push()
        db.create_all()
        
        self.server_thread = multiprocessing.Process(target=run_flask_app)
        self.server_thread.start()
        
        time.sleep(2)
        
        # select browser
        browser_type = os.getenv("BROWSER", "edge").lower()
        
        if browser_type == "chrome":
            options = webdriver.ChromeOptions()
            self.driver = webdriver.Chrome(options=options)
        elif browser_type == "firefox":
            options = webdriver.FirefoxOptions()
            self.driver = webdriver.Firefox(options=options)
        elif browser_type == "edge":
            options = webdriver.EdgeOptions()
            self.driver = webdriver.Edge(options=options)
        else:
            raise ValueError(f"Unsupported browser: {browser_type}")
        
        self.driver.implicitly_wait(10)
        return super().setUp()
    
    def addUser(self, username, password):
        user = User(
            Username=username,
            email=f'{username}@example.com',
            password=generate_password_hash(password),
            country='Australia',
            dateofbirth='2000-1-1'
        )
        db.session.add(user)
        db.session.commit()
        return user
    
    def test_1_homepage_to_login(self): 
        self.driver.get(localHost)

        find_adventure_button = WebDriverWait(self.driver, 10).until(
            expected_conditions.element_to_be_clickable((By.ID, "loginPage"))
        )
        find_adventure_button.click()
        
        # Now confirm redirect to login (optional)
        WebDriverWait(self.driver, 10).until(
            expected_conditions.url_contains("/login")
        )
        
        time.sleep(3)
        self.assertIn("/login", self.driver.current_url)
        
    def test_2_loginSuccess(self):
        
        # add user
        user = self.addUser('testUser', 'testPassword')
        
        self.test_1_homepage_to_login()
        
        # find elements
        user_id_field = self.driver.find_element(By.ID, "Username")
        password_field = self.driver.find_element(By.ID, "password3")
        login_btn = self.driver.find_element(By.ID, "login-btn")
        
        # send key
        user_id_field.send_keys("testUser")
        password_field.send_keys("testPassword")
        
        login_btn.click()
        
        time.sleep(3)
        self.assertIn("/FindAdv", self.driver.current_url)
        
    def test_3_loginWrongPassword(self):
        # add user
        user = self.addUser('testUser', 'testPassword')
        
        self.test_1_homepage_to_login()
        
        # find elements
        user_id_field = self.driver.find_element(By.ID, "Username")
        password_field = self.driver.find_element(By.ID, "password3")
        login_btn = self.driver.find_element(By.ID, "login-btn")
        
        # send key
        user_id_field.send_keys("testUser")
        password_field.send_keys("wrongPassword")
        
        login_btn.click()
        
        time.sleep(3)
        # Assert we are still on the login page (failed login)
        self.assertIn("/login", self.driver.current_url)
        
        # Optional: assert that an error message is displayed on the page
        body_text = self.driver.find_element(By.TAG_NAME, "body").text
        self.assertIn("Incorrect password, try again.", body_text)
        
    def test_4_loginWrongUsername(self):
        # add user
        user = self.addUser('testUser', 'testPassword')
        
        self.test_1_homepage_to_login()
        
        # find elements
        user_id_field = self.driver.find_element(By.ID, "Username")
        password_field = self.driver.find_element(By.ID, "password3")
        login_btn = self.driver.find_element(By.ID, "login-btn")
        
        # send key
        user_id_field.send_keys("wrongUser")
        password_field.send_keys("testPassword")
        
        login_btn.click()
        
        time.sleep(3)
        # Assert we are still on the login page (failed login)
        self.assertIn("/login", self.driver.current_url)
        
        # Optional: assert that an error message is displayed on the page
        body_text = self.driver.find_element(By.TAG_NAME, "body").text
        self.assertIn('Username does not exist.', body_text)
        
    def test_5_signupSuccess(self):
        self.driver.get('http://127.0.0.1:5000/login?form=signup')
        
        try:
            #print all available element ids
            elements_with_id = self.driver.find_elements(By.XPATH, "//*[@id]")
            print(f"found {len(elements_with_id)} with element IDs:")
            for element in elements_with_id:
                print(f"Element with ID: {element.get_attribute('id')}")
        except Exception:
            pass
        
        # find elements
        newUser = self.driver.find_element(By.ID, 'createUsername')
        newEmail = self.driver.find_element(By.ID, 'email')
        newPassword = self.driver.find_element(By.ID, 'password')
        confirmPass = self.driver.find_element(By.ID, 'confirmPassword')
        bday = self.driver.find_element(By.ID, 'birthdate')
        signupbtn = self.driver.find_element(By.ID, 'signUpSubmit')
        
        #send key
        newUser.send_keys("testUsername")
        newEmail.send_keys("testemail@example.com")
        newPassword.send_keys("1234567890")
        confirmPass.send_keys("1234567890")
        bday.send_keys("20-01-2000")
        
        # Replace with the actual locator of the button
        self.driver.execute_script("arguments[0].scrollIntoView(true);", signupbtn)
        time.sleep(0.5)  # allow any animation to complete
        signupbtn = WebDriverWait(self.driver, 10).until(
            expected_conditions.element_to_be_clickable((By.ID, "signUpSubmit"))  # or (By.XPATH, "..."), etc.
        )
        signupbtn.click()
        
        self.assertIn("/login", self.driver.current_url)
    
    def tearDown(self):
        self.driver.quit()
        self.server_thread.terminate()
        db.session.remove()
        db.drop_all()
        self.app_ctx.pop()
        return super().tearDown()