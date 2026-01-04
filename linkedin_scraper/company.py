import requests
from lxml import html
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from .objects import Scraper
from .person import Person
import time
import os
import json

AD_BANNER_CLASSNAME = ('ad-banner-container', '__ad')

def getchildren(elem):
    return elem.find_elements(By.XPATH, ".//*")

class CompanySummary(object):
    linkedin_url = None
    name = None
    followers = None

    def __init__(self, linkedin_url = None, name = None, followers = None):
        self.linkedin_url = linkedin_url
        self.name = name
        self.followers = followers

    def __repr__(self):
        if self.followers == None:
            return """ {name} """.format(name = self.name)
        else:
            return """ {name} {followers} """.format(name = self.name, followers = self.followers)

class Company(Scraper):
    linkedin_url = None
    name = None
    about_us =None
    website = None
    phone = None
    headquarters = None
    founded = None
    industry = None
    company_type = None
    company_size = None
    specialties = None
    showcase_pages = []
    affiliated_companies = []
    employees = []
    headcount = None

    def __init__(self, linkedin_url = None, name = None, about_us =None, website = None, phone = None, headquarters = None, founded = None, industry = None, company_type = None, company_size = None, specialties = None, showcase_pages =[], affiliated_companies = [], driver = None, scrape = True, get_employees = True, close_on_complete = True):
        self.linkedin_url = linkedin_url
        self.name = name
        self.about_us = about_us
        self.website = website
        self.phone = phone
        self.headquarters = headquarters
        self.founded = founded
        self.industry = industry
        self.company_type = company_type
        self.company_size = company_size
        self.specialties = specialties
        self.showcase_pages = showcase_pages
        self.affiliated_companies = affiliated_companies

        if driver is None:
            try:
                if os.getenv("CHROMEDRIVER") == None:
                    driver_path = os.path.join(os.path.dirname(__file__), 'drivers/chromedriver')
                else:
                    driver_path = os.getenv("CHROMEDRIVER")

                driver = webdriver.Chrome(driver_path)
            except:
                driver = webdriver.Chrome()

        driver.get(linkedin_url)
        self.driver = driver

        if scrape:
            self.scrape(get_employees=get_employees, close_on_complete=close_on_complete)

    def __get_text_under_subtitle(self, elem):
        return "\n".join(elem.text.split("\n")[1:])

    def __get_text_under_subtitle_by_class(self, driver, class_name):
        return self.__get_text_under_subtitle(driver.find_element(By.CLASS_NAME, class_name))

    def scrape(self, get_employees=True, close_on_complete=True):
        if self.is_signed_in():
            self.scrape_logged_in(get_employees = get_employees, close_on_complete = close_on_complete)
        else:
            self.scrape_not_logged_in(get_employees = get_employees, close_on_complete = close_on_complete)

    def __parse_employee__(self, employee_raw):

        try:
            # print()
            employee_object = {}
            employee_object['name'] = (employee_raw.text.split("\n") or [""])[0].strip()
            employee_object['designation'] = (employee_raw.text.split("\n") or [""])[3].strip()
            employee_object['linkedin_url'] = employee_raw.find_element(By.TAG_NAME, "a").get_attribute("href")
            # print(employee_raw.text, employee_object)
            # _person = Person(
            #     # linkedin_url = employee_raw.find_element_by_tag_name("a").get_attribute("href"),
            #     linkedin_url = employee_raw.find_element_by_tag_name("a").get_attribute("href"),
            #     name = (employee_raw.text.split("\n") or [""])[0].strip(),
            #     driver = self.driver,
            #     get = True,
            #     scrape = False,
            #     designation = (employee_raw.text.split("\n") or [""])[3].strip()
            #     )
            # print(_person, employee_object)
            # return _person
            return employee_object
        except Exception as e:
            # print(e)
            return None

    def get_employees(self, wait_time=10):
        total = []
        list_css = "list-style-none"
        next_xpath = '//button[@aria-label="Next"]'
        driver = self.driver

        try:
            see_all_employees = driver.find_element(By.XPATH,'//a[@data-control-name="topcard_see_all_employees"]')
        except:
            pass
        driver.get(os.path.join(self.linkedin_url, "people"))

        # Wait for the people list to load - try multiple selectors for compatibility
        try:
            _ = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.XPATH, '//h2[contains(text(), "People you may know")]')))
        except:
            try:
                _ = WebDriverWait(driver, 3).until(EC.presence_of_all_elements_located((By.XPATH, '//span[@dir="ltr"]')))
            except:
                # If neither selector works, just wait a bit and continue
                time.sleep(2)

        driver.execute_script("window.scrollTo(0, Math.ceil(document.body.scrollHeight/2));")
        time.sleep(1)
        driver.execute_script("window.scrollTo(0, Math.ceil(document.body.scrollHeight*3/4));")
        time.sleep(1)

        results_list = driver.find_element(By.CLASS_NAME, list_css)
        results_li = results_list.find_elements(By.TAG_NAME, "li")
        for res in results_li:
            total.append(self.__parse_employee__(res))

        def is_loaded(previous_results):
          loop = 0
          driver.execute_script("window.scrollTo(0, Math.ceil(document.body.scrollHeight));")
          results_li = results_list.find_elements(By.TAG_NAME, "li")
          while len(results_li) == previous_results and loop <= 5:
            time.sleep(1)
            driver.execute_script("window.scrollTo(0, Math.ceil(document.body.scrollHeight));")
            results_li = results_list.find_elements(By.TAG_NAME, "li")
            loop += 1
          return loop <= 5

        def get_data(previous_results):
            results_li = results_list.find_elements(By.TAG_NAME, "li")
            for res in results_li[previous_results:]:
                total.append(self.__parse_employee__(res))

        results_li_len = len(results_li)
        while is_loaded(results_li_len):
            try:
                driver.find_element(By.XPATH,next_xpath).click()
            except:
                pass
            _ = WebDriverWait(driver, wait_time).until(EC.presence_of_element_located((By.CLASS_NAME, list_css)))

            driver.execute_script("window.scrollTo(0, Math.ceil(document.body.scrollHeight/2));")
            time.sleep(1)
            driver.execute_script("window.scrollTo(0, Math.ceil(document.body.scrollHeight*2/3));")
            time.sleep(1)
            driver.execute_script("window.scrollTo(0, Math.ceil(document.body.scrollHeight*3/4));")
            time.sleep(1)
            driver.execute_script("window.scrollTo(0, Math.ceil(document.body.scrollHeight));")
            time.sleep(1)

            get_data(results_li_len)
            results_li_len = len(total)
        return total



    def scrape_logged_in(self, get_employees = True, close_on_complete = True):
        driver = self.driver

        driver.get(self.linkedin_url)

        # Wait for page to load
        try:
            _ = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.TAG_NAME, 'main')))
        except:
            time.sleep(2)

        # Get company name from heading
        try:
            self.name = driver.find_element(By.XPATH, "//h1").text.strip()
        except:
            try:
                self.name = driver.find_element(By.CLASS_NAME,"org-top-card-summary__title").text.strip()
            except:
                pass

        # Navigate to about page
        driver.get(os.path.join(self.linkedin_url, "about"))

        try:
            _ = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.TAG_NAME, 'main')))
        except:
            time.sleep(2)
        time.sleep(2)

        # Get about/overview text
        try:
            overview_section = driver.find_element(By.XPATH, "//h2[contains(text(), 'Overview')]/following-sibling::p")
            self.about_us = overview_section.text.strip()
        except:
            try:
                descWrapper = driver.find_elements(By.TAG_NAME, "p")
                if len(descWrapper) > 0:
                    self.about_us = descWrapper[0].text.strip()
            except:
                pass

        # Get company details from dt/dd pairs
        try:
            labels = driver.find_elements(By.TAG_NAME, "dt")
            values = driver.find_elements(By.TAG_NAME, "dd")

            # Create a mapping of labels to values
            label_texts = [label.text.strip() for label in labels]

            for i, txt in enumerate(label_texts):
                if i >= len(values):
                    break
                value = values[i].text.strip()

                if txt == 'Website':
                    self.website = value
                elif txt == 'Phone':
                    self.phone = value
                elif txt == 'Industry':
                    self.industry = value
                elif txt == 'Company size':
                    self.company_size = value
                elif txt == 'Headquarters':
                    self.headquarters = value
                elif txt == 'Type':
                    self.company_type = value
                elif txt == 'Founded':
                    self.founded = value
                elif txt == 'Specialties':
                    self.specialties = "\n".join(value.split(", "))
        except:
            pass

        # Get headcount from associated members link
        try:
            members_link = driver.find_element(By.XPATH, "//a[contains(text(), 'associated members')]")
            txt = members_link.text.strip()
            # Extract number from text like "14,436 associated members"
            import re
            match = re.search(r'([\d,]+)\s*associated members', txt)
            if match:
                self.headcount = int(match.group(1).replace(',', ''))
        except:
            pass

        driver.execute_script("window.scrollTo(0, Math.ceil(document.body.scrollHeight/2));")


        try:
            _ = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.CLASS_NAME, 'company-list')))
            showcase, affiliated = driver.find_elements(By.CLASS_NAME, "company-list")
            driver.find_element(By.ID,"org-related-companies-module__show-more-btn").click()

            # get showcase
            for showcase_company in showcase.find_elements(By.CLASS_NAME, "org-company-card"):
                companySummary = CompanySummary(
                        linkedin_url = showcase_company.find_element(By.CLASS_NAME, "company-name-link").get_attribute("href"),
                        name = showcase_company.find_element(By.CLASS_NAME, "company-name-link").text.strip(),
                        followers = showcase_company.find_element(By.CLASS_NAME, "company-followers-count").text.strip()
                    )
                self.showcase_pages.append(companySummary)

            # affiliated company

            for affiliated_company in showcase.find_element(By.CLASS_NAME, "org-company-card"):
                companySummary = CompanySummary(
                         linkedin_url = affiliated_company.find_element(By.CLASS_NAME, "company-name-link").get_attribute("href"),
                        name = affiliated_company.find_element(By.CLASS_NAME, "company-name-link").text.strip(),
                        followers = affiliated_company.find_element(By.CLASS_NAME, "company-followers-count").text.strip()
                        )
                self.affiliated_companies.append(companySummary)

        except:
            pass

        if get_employees:
            self.employees = self.get_employees()

        driver.get(self.linkedin_url)

        if close_on_complete:
            driver.close()

    def scrape_not_logged_in(self, close_on_complete = True, retry_limit = 10, get_employees = True):
        driver = self.driver
        retry_times = 0
        while self.is_signed_in() and retry_times <= retry_limit:
            page = driver.get(self.linkedin_url)
            retry_times = retry_times + 1

        self.name = driver.find_element(By.CLASS_NAME, "name").text.strip()

        self.about_us = driver.find_element(By.CLASS_NAME, "basic-info-description").text.strip()
        self.specialties = self.__get_text_under_subtitle_by_class(driver, "specialties")
        self.website = self.__get_text_under_subtitle_by_class(driver, "website")
        self.phone = self.__get_text_under_subtitle_by_class(driver, "phone")
        self.headquarters = driver.find_element(By.CLASS_NAME, "adr").text.strip()
        self.industry = driver.find_element(By.CLASS_NAME, "industry").text.strip()
        self.company_size = driver.find_element(By.CLASS_NAME, "company-size").text.strip()
        self.company_type = self.__get_text_under_subtitle_by_class(driver, "type")
        self.founded = self.__get_text_under_subtitle_by_class(driver, "founded")

        # get showcase
        try:
            driver.find_element(By.ID,"view-other-showcase-pages-dialog").click()
            WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.ID, 'dialog')))

            showcase_pages = driver.find_elements(By.CLASS_NAME, "company-showcase-pages")[1]
            for showcase_company in showcase_pages.find_elements(By.TAG_NAME, "li"):
                name_elem = showcase_company.find_element(By.CLASS_NAME, "name")
                companySummary = CompanySummary(
                    linkedin_url = name_elem.find_element(By.TAG_NAME, "a").get_attribute("href"),
                    name = name_elem.text.strip(),
                    followers = showcase_company.text.strip().split("\n")[1]
                )
                self.showcase_pages.append(companySummary)
            driver.find_element(By.CLASS_NAME, "dialog-close").click()
        except:
            pass

        # affiliated company
        try:
            affiliated_pages = driver.find_element(By.CLASS_NAME, "affiliated-companies")
            for i, affiliated_page in enumerate(affiliated_pages.find_elements(By.CLASS_NAME, "affiliated-company-name")):
                if i % 3 == 0:
                    affiliated_pages.find_element(By.CLASS_NAME, "carousel-control-next").click()

                companySummary = CompanySummary(
                    linkedin_url = affiliated_page.find_element(By.TAG_NAME, "a").get_attribute("href"),
                    name = affiliated_page.text.strip()
                )
                self.affiliated_companies.append(companySummary)
        except:
            pass

        if get_employees:
            self.employees = self.get_employees()

        driver.get(self.linkedin_url)

        if close_on_complete:
            driver.close()

    def __repr__(self):
        _output = {}
        _output['name'] = self.name
        _output['about_us'] = self.about_us
        _output['specialties'] = self.specialties
        _output['website'] = self.website
        _output['phone'] = self.phone
        _output['industry'] = self.industry
        _output['company_type'] = self.name
        _output['headquarters'] = self.headquarters
        _output['company_size'] = self.company_size
        _output['founded'] = self.founded
        _output['affiliated_companies'] = self.affiliated_companies
        _output['employees'] = self.employees
        _output['headcount'] = self.headcount
        
        return json.dumps(_output).replace('\n', '')
