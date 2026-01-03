import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from .objects import Experience, Education, Scraper, Interest, Accomplishment, Contact, Skill, Language, Certification, HonorAward
import os
from linkedin_scraper import selectors


class Person(Scraper):

    __TOP_CARD = "main"
    __WAIT_FOR_ELEMENT_TIMEOUT = 5

    def __init__(
        self,
        linkedin_url=None,
        name=None,
        about=None,
        experiences=None,
        educations=None,
        interests=None,
        accomplishments=None,
        company=None,
        job_title=None,
        contacts=None,
        skills=None,
        languages=None,
        certifications=None,
        honors_awards=None,
        driver=None,
        get=True,
        scrape=True,
        close_on_complete=True,
        time_to_wait_after_login=0,
    ):
        self.linkedin_url = linkedin_url
        self.name = name
        self.about = about or []
        self.experiences = experiences or []
        self.educations = educations or []
        self.interests = interests or []
        self.accomplishments = accomplishments or []
        self.also_viewed_urls = []
        self.contacts = contacts or []
        self.skills = skills or []
        self.languages = languages or []
        self.certifications = certifications or []
        self.honors_awards = honors_awards or []

        if driver is None:
            try:
                if os.getenv("CHROMEDRIVER") == None:
                    driver_path = os.path.join(
                        os.path.dirname(__file__), "drivers/chromedriver"
                    )
                else:
                    driver_path = os.getenv("CHROMEDRIVER")

                driver = webdriver.Chrome(driver_path)
            except:
                driver = webdriver.Chrome()

        if get:
            driver.get(linkedin_url)

        self.driver = driver

        if scrape:
            self.scrape(close_on_complete)

    def add_about(self, about):
        self.about.append(about)

    def add_experience(self, experience):
        self.experiences.append(experience)

    def add_education(self, education):
        self.educations.append(education)

    def add_interest(self, interest):
        self.interests.append(interest)

    def add_accomplishment(self, accomplishment):
        self.accomplishments.append(accomplishment)

    def add_location(self, location):
        self.location = location

    def add_contact(self, contact):
        self.contacts.append(contact)

    def add_skill(self, skill):
        self.skills.append(skill)

    def add_language(self, language):
        self.languages.append(language)

    def add_certification(self, certification):
        self.certifications.append(certification)

    def add_honor_award(self, honor_award):
        self.honors_awards.append(honor_award)

    def scrape(self, close_on_complete=True):
        if self.is_signed_in():
            self.scrape_logged_in(close_on_complete=close_on_complete)
        else:
            print("you are not logged in!")

    def _click_see_more_by_class_name(self, class_name):
        try:
            _ = WebDriverWait(self.driver, self.__WAIT_FOR_ELEMENT_TIMEOUT).until(
                EC.presence_of_element_located((By.CLASS_NAME, class_name))
            )
            div = self.driver.find_element(By.CLASS_NAME, class_name)
            div.find_element(By.TAG_NAME, "button").click()
        except Exception as e:
            pass

    def is_open_to_work(self):
        try:
            return "#OPEN_TO_WORK" in self.driver.find_element(By.CLASS_NAME,"pv-top-card-profile-picture").find_element(By.TAG_NAME,"img").get_attribute("title")
        except:
            return False

    def get_experiences(self):
        url = os.path.join(self.linkedin_url, "details/experience")
        self.driver.get(url)
        self.focus()
        main = self.wait_for_element_to_load(by=By.TAG_NAME, name="main")
        self.scroll_to_half()
        self.scroll_to_bottom()
        main_list = self.wait_for_element_to_load(name="pvs-list__container", base=main)
        for position in main_list.find_elements(By.CLASS_NAME, "pvs-list__paged-list-item"):
            position = position.find_element(By.CSS_SELECTOR, "div[data-view-name='profile-component-entity']")
            
            # Fix: Handle case where more than 2 elements are returned
            elements = position.find_elements(By.XPATH, "*")
            if len(elements) < 2:
                continue  # Skip if we don't have enough elements
                
            company_logo_elem = elements[0]
            position_details = elements[1]

            # company elem
            try:
                company_linkedin_url = company_logo_elem.find_element(By.XPATH,"*").get_attribute("href")
                if not company_linkedin_url:
                    continue
            except NoSuchElementException:
                continue

            # position details
            position_details_list = position_details.find_elements(By.XPATH,"*")
            position_summary_details = position_details_list[0] if len(position_details_list) > 0 else None
            position_summary_text = position_details_list[1] if len(position_details_list) > 1 else None
            
            if not position_summary_details:
                continue
                
            outer_positions = position_summary_details.find_element(By.XPATH,"*").find_elements(By.XPATH,"*")

            if len(outer_positions) == 4:
                position_title = outer_positions[0].find_element(By.TAG_NAME,"span").text
                company = outer_positions[1].find_element(By.TAG_NAME,"span").text
                work_times = outer_positions[2].find_element(By.TAG_NAME,"span").text
                location = outer_positions[3].find_element(By.TAG_NAME,"span").text
            elif len(outer_positions) == 3:
                if "·" in outer_positions[2].text:
                    position_title = outer_positions[0].find_element(By.TAG_NAME,"span").text
                    company = outer_positions[1].find_element(By.TAG_NAME,"span").text
                    work_times = outer_positions[2].find_element(By.TAG_NAME,"span").text
                    location = ""
                else:
                    position_title = ""
                    company = outer_positions[0].find_element(By.TAG_NAME,"span").text
                    work_times = outer_positions[1].find_element(By.TAG_NAME,"span").text
                    location = outer_positions[2].find_element(By.TAG_NAME,"span").text
            else:
                position_title = ""
                company = outer_positions[0].find_element(By.TAG_NAME,"span").text if outer_positions else ""
                work_times = outer_positions[1].find_element(By.TAG_NAME,"span").text if len(outer_positions) > 1 else ""
                location = ""

            # Safely extract times and duration
            if work_times:
                parts = work_times.split("·")
                times = parts[0].strip() if parts else ""
                duration = parts[1].strip() if len(parts) > 1 else None
            else:
                times = ""
                duration = None

            from_date = " ".join(times.split(" ")[:2]) if times else ""
            to_date = " ".join(times.split(" ")[3:]) if times and len(times.split(" ")) > 3 else ""
            
            if position_summary_text and any(element.get_attribute("class") == "pvs-list__container" for element in position_summary_text.find_elements(By.XPATH, "*")):
                try:
                    inner_positions = (position_summary_text.find_element(By.CLASS_NAME,"pvs-list__container")
                                    .find_element(By.XPATH,"*").find_element(By.XPATH,"*").find_element(By.XPATH,"*")
                                    .find_elements(By.CLASS_NAME,"pvs-list__paged-list-item"))
                except NoSuchElementException:
                    inner_positions = []
            else:
                inner_positions = []
            
            if len(inner_positions) > 1:
                descriptions = inner_positions
                for description in descriptions:
                    try:
                        res = description.find_element(By.TAG_NAME,"a").find_elements(By.XPATH,"*")
                        position_title_elem = res[0] if len(res) > 0 else None
                        work_times_elem = res[1] if len(res) > 1 else None
                        location_elem = res[2] if len(res) > 2 else None

                        location = location_elem.find_element(By.XPATH,"*").text if location_elem else None
                        position_title = position_title_elem.find_element(By.XPATH,"*").find_element(By.TAG_NAME,"*").text if position_title_elem else ""
                        work_times = work_times_elem.find_element(By.XPATH,"*").text if work_times_elem else ""
                        
                        # Safely extract times and duration
                        if work_times:
                            parts = work_times.split("·")
                            times = parts[0].strip() if parts else ""
                            duration = parts[1].strip() if len(parts) > 1 else None
                        else:
                            times = ""
                            duration = None
                            
                        from_date = " ".join(times.split(" ")[:2]) if times else ""
                        to_date = " ".join(times.split(" ")[3:]) if times and len(times.split(" ")) > 3 else ""

                        experience = Experience(
                            position_title=position_title,
                            from_date=from_date,
                            to_date=to_date,
                            duration=duration,
                            location=location,
                            description=description,
                            institution_name=company,
                            linkedin_url=company_linkedin_url
                        )
                        self.add_experience(experience)
                    except (NoSuchElementException, IndexError) as e:
                        # Skip this description if elements are missing
                        continue
            else:
                description = position_summary_text.text if position_summary_text else ""

                experience = Experience(
                    position_title=position_title,
                    from_date=from_date,
                    to_date=to_date,
                    duration=duration,
                    location=location,
                    description=description,
                    institution_name=company,
                    linkedin_url=company_linkedin_url
                )
                self.add_experience(experience)

    def get_educations(self):
        url = os.path.join(self.linkedin_url, "details/education")
        self.driver.get(url)
        self.focus()
        main = self.wait_for_element_to_load(by=By.TAG_NAME, name="main")
        self.scroll_to_half()
        self.scroll_to_bottom()
        main_list = self.wait_for_element_to_load(name="pvs-list__container", base=main)
        for position in main_list.find_elements(By.CLASS_NAME,"pvs-list__paged-list-item"):
            try:
                position = position.find_element(By.CSS_SELECTOR, "div[data-view-name='profile-component-entity']")
                
                # Fix: Handle case where more than 2 elements are returned
                elements = position.find_elements(By.XPATH,"*")
                if len(elements) < 2:
                    continue  # Skip if we don't have enough elements
                    
                institution_logo_elem = elements[0]
                position_details = elements[1]

                # institution elem
                try:
                    institution_linkedin_url = institution_logo_elem.find_element(By.XPATH,"*").get_attribute("href")
                except NoSuchElementException:
                    institution_linkedin_url = None

                # position details
                position_details_list = position_details.find_elements(By.XPATH,"*")
                position_summary_details = position_details_list[0] if len(position_details_list) > 0 else None
                position_summary_text = position_details_list[1] if len(position_details_list) > 1 else None
                
                if not position_summary_details:
                    continue
                    
                outer_positions = position_summary_details.find_element(By.XPATH,"*").find_elements(By.XPATH,"*")

                institution_name = outer_positions[0].find_element(By.TAG_NAME,"span").text if outer_positions else ""
                degree = outer_positions[1].find_element(By.TAG_NAME,"span").text if len(outer_positions) > 1 else None

                from_date = None
                to_date = None
                
                if len(outer_positions) > 2:
                    try:
                        times = outer_positions[2].find_element(By.TAG_NAME,"span").text

                        if times and "-" in times:
                            split_times = times.split(" ")
                            dash_index = split_times.index("-") if "-" in split_times else -1
                            
                            if dash_index > 0:
                                from_date = split_times[dash_index-1]
                            if dash_index < len(split_times) - 1:
                                to_date = split_times[-1]
                    except (NoSuchElementException, ValueError):
                        from_date = None
                        to_date = None

                description = position_summary_text.text if position_summary_text else ""

                education = Education(
                    from_date=from_date,
                    to_date=to_date,
                    description=description,
                    degree=degree,
                    institution_name=institution_name,
                    linkedin_url=institution_linkedin_url
                )
                self.add_education(education)
            except (NoSuchElementException, IndexError) as e:
                # Skip this education entry if elements are missing
                continue

    def get_name_and_location(self):
        top_panel = self.driver.find_element(By.XPATH, "//*[@class='mt2 relative']")
        self.name = top_panel.find_element(By.TAG_NAME, "h1").text
        self.location = top_panel.find_element(By.XPATH, "//*[@class='text-body-small inline t-black--light break-words']").text

    def get_about(self):
        try:
            about = self.driver.find_element(By.ID,"about").find_element(By.XPATH,"..").find_element(By.CLASS_NAME,"display-flex").text
        except NoSuchElementException :
            about=None
        self.about = about

    def get_skills(self):
        url = os.path.join(self.linkedin_url, "details/skills")
        self.driver.get(url)
        self.focus()
        main = self.wait_for_element_to_load(by=By.TAG_NAME, name="main")
        self.scroll_to_half()
        self.scroll_to_bottom()

        try:
            main_list = self.wait_for_element_to_load(name="pvs-list__container", base=main)
            for item in main_list.find_elements(By.CLASS_NAME, "pvs-list__paged-list-item"):
                try:
                    # Get skill name from the link element
                    skill_name = ""
                    endorsements = 0

                    # Try to find skill name in link
                    try:
                        skill_link = item.find_element(By.CSS_SELECTOR, "a[href*='keywords=']")
                        skill_name_elem = skill_link.find_element(By.XPATH, ".//span[@aria-hidden='true']")
                        skill_name = skill_name_elem.text.strip()
                    except NoSuchElementException:
                        continue

                    # Try to get endorsements count
                    try:
                        endorsement_link = item.find_element(By.CSS_SELECTOR, "a[href*='endorsers']")
                        endorsement_text = endorsement_link.find_element(By.XPATH, ".//span[@aria-hidden='true']").text
                        # Extract number from text like "4 endorsements"
                        endorsement_parts = endorsement_text.split()
                        if endorsement_parts:
                            endorsements = int(endorsement_parts[0])
                    except (NoSuchElementException, ValueError):
                        endorsements = 0

                    # Skip placeholder text for empty sections
                    if skill_name and not self._is_empty_section_placeholder(skill_name):
                        skill = Skill(
                            name=skill_name,
                            endorsements=endorsements
                        )
                        self.add_skill(skill)
                except (NoSuchElementException, IndexError):
                    continue
        except Exception:
            pass

    def _is_empty_section_placeholder(self, text):
        """Check if text is a LinkedIn placeholder for empty sections."""
        placeholder_patterns = [
            "Nothing to see for now",
            "will appear here",
            "No skills have been",
            "hasn't added",
            "not added any",
        ]
        text_lower = text.lower()
        return any(pattern.lower() in text_lower for pattern in placeholder_patterns)

    def get_languages(self):
        url = os.path.join(self.linkedin_url, "details/languages")
        self.driver.get(url)
        self.focus()
        main = self.wait_for_element_to_load(by=By.TAG_NAME, name="main")
        self.scroll_to_half()
        self.scroll_to_bottom()

        try:
            main_list = main.find_element(By.TAG_NAME, "ul")
            for item in main_list.find_elements(By.TAG_NAME, "li"):
                try:
                    # Get all spans with aria-hidden="true"
                    spans = item.find_elements(By.XPATH, ".//span[@aria-hidden='true']")

                    language_name = ""
                    proficiency = ""

                    if len(spans) >= 1:
                        language_name = spans[0].text.strip()
                    if len(spans) >= 2:
                        proficiency = spans[1].text.strip()

                    # Skip placeholder text for empty sections
                    if language_name and not self._is_empty_section_placeholder(language_name):
                        language = Language(
                            name=language_name,
                            proficiency=proficiency
                        )
                        self.add_language(language)
                except (NoSuchElementException, IndexError):
                    continue
        except Exception:
            pass

    def get_certifications(self):
        url = os.path.join(self.linkedin_url, "details/certifications")
        self.driver.get(url)
        self.focus()
        main = self.wait_for_element_to_load(by=By.TAG_NAME, name="main")
        self.scroll_to_half()
        self.scroll_to_bottom()

        try:
            main_list = main.find_element(By.TAG_NAME, "ul")
            for item in main_list.find_elements(By.TAG_NAME, "li"):
                try:
                    cert_name = ""
                    organization = ""
                    issue_date = ""
                    credential_id = ""
                    credential_url = ""

                    # Get all spans with aria-hidden="true"
                    spans = item.find_elements(By.XPATH, ".//span[@aria-hidden='true']")

                    if len(spans) >= 1:
                        cert_name = spans[0].text.strip()
                    if len(spans) >= 2:
                        organization = spans[1].text.strip()
                    if len(spans) >= 3:
                        issue_date = spans[2].text.strip()
                        # Remove "Issued " prefix if present
                        if issue_date.startswith("Issued "):
                            issue_date = issue_date[7:]
                    if len(spans) >= 4:
                        cred_text = spans[3].text.strip()
                        if cred_text.startswith("Credential ID "):
                            credential_id = cred_text[14:]

                    # Try to get credential URL
                    try:
                        cred_link = item.find_element(By.CSS_SELECTOR, "a[href*='credential']")
                        credential_url = cred_link.get_attribute("href")
                    except NoSuchElementException:
                        pass

                    # Skip placeholder text for empty sections
                    if cert_name and not self._is_empty_section_placeholder(cert_name):
                        certification = Certification(
                            name=cert_name,
                            organization=organization,
                            issue_date=issue_date,
                            credential_id=credential_id,
                            credential_url=credential_url
                        )
                        self.add_certification(certification)
                except (NoSuchElementException, IndexError):
                    continue
        except Exception:
            pass

    def get_honors_awards(self):
        url = os.path.join(self.linkedin_url, "details/honors")
        self.driver.get(url)
        self.focus()
        main = self.wait_for_element_to_load(by=By.TAG_NAME, name="main")
        self.scroll_to_half()
        self.scroll_to_bottom()

        try:
            main_list = self.wait_for_element_to_load(name="pvs-list__container", base=main)
            for item in main_list.find_elements(By.CLASS_NAME, "pvs-list__paged-list-item"):
                try:
                    title = ""
                    issuer = ""
                    issue_date = ""
                    description = ""
                    associated_with = ""

                    # Get all spans with aria-hidden="true" - filter for non-empty unique values
                    spans = item.find_elements(By.XPATH, ".//span[@aria-hidden='true']")

                    # Extract unique non-empty text values (LinkedIn duplicates content for accessibility)
                    seen_texts = set()
                    unique_texts = []
                    for span in spans:
                        text = span.text.strip()
                        if text and text not in seen_texts:
                            seen_texts.add(text)
                            unique_texts.append(text)

                    for text in unique_texts:
                        if "Issued by " in text:
                            # Parse issuer and date from "Issued by X · Date"
                            parts = text.replace("Issued by ", "").split(" · ")
                            if len(parts) >= 1:
                                issuer = parts[0].strip()
                            if len(parts) >= 2:
                                issue_date = parts[1].strip()
                        elif "Associated with " in text:
                            associated_with = text.replace("Associated with ", "")
                        elif not title:
                            # First non-special text is the title
                            title = text
                        else:
                            # Remaining text is likely description
                            if description:
                                description = description + " " + text
                            else:
                                description = text

                    # Skip placeholder text for empty sections
                    if title and not self._is_empty_section_placeholder(title):
                        honor_award = HonorAward(
                            title=title,
                            issuer=issuer,
                            issue_date=issue_date,
                            description=description,
                            associated_with=associated_with
                        )
                        self.add_honor_award(honor_award)
                except (NoSuchElementException, IndexError):
                    continue
        except Exception:
            pass

    def get_interests(self):
        url = os.path.join(self.linkedin_url, "details/interests")
        self.driver.get(url)
        self.focus()
        main = self.wait_for_element_to_load(by=By.TAG_NAME, name="main")
        self.scroll_to_half()
        self.scroll_to_bottom()

        try:
            # Find all tabs (Top Voices, Companies, Groups, Schools)
            tabs = main.find_elements(By.CSS_SELECTOR, "button[role='tab']")

            for tab in tabs:
                try:
                    # Get tab name from aria-hidden span to avoid duplication
                    try:
                        tab_name_elem = tab.find_element(By.XPATH, ".//span[@aria-hidden='true']")
                        tab_name = tab_name_elem.text.strip()
                    except NoSuchElementException:
                        tab_name = tab.text.strip()
                        # Remove duplicates like "Top VoicesTop Voices"
                        if len(tab_name) > 0 and len(tab_name) % 2 == 0:
                            half = len(tab_name) // 2
                            if tab_name[:half] == tab_name[half:]:
                                tab_name = tab_name[:half]

                    tab.click()
                    self.wait(1)  # Wait for tab content to load

                    # Get list items from the current tab panel
                    tab_panel = main.find_element(By.CSS_SELECTOR, "div[role='tabpanel']")
                    self.scroll_to_half()
                    self.scroll_to_bottom()

                    items = tab_panel.find_elements(By.CLASS_NAME, "pvs-list__paged-list-item")

                    for item in items:
                        try:
                            # Get the URL from the first link
                            links = item.find_elements(By.TAG_NAME, "a")
                            link_url = links[0].get_attribute("href") if links else ""

                            # Get text from spans with aria-hidden="true"
                            spans = item.find_elements(By.XPATH, ".//span[@aria-hidden='true']")

                            # Extract unique non-empty text values
                            seen_texts = set()
                            unique_texts = []
                            for span in spans:
                                text = span.text.strip()
                                if text and text not in seen_texts and not text.startswith("·"):
                                    seen_texts.add(text)
                                    unique_texts.append(text)

                            if unique_texts:
                                name = unique_texts[0]  # First text is usually the name
                                description = unique_texts[1] if len(unique_texts) > 1 else ""

                                interest = Interest(
                                    institution_name=name,
                                    linkedin_url=link_url
                                )
                                interest.title = f"{tab_name}: {description}" if description else tab_name
                                self.add_interest(interest)
                        except (NoSuchElementException, IndexError):
                            continue
                except (NoSuchElementException, IndexError):
                    continue
        except Exception:
            pass

    def scrape_logged_in(self, close_on_complete=True):
        driver = self.driver
        duration = None

        root = WebDriverWait(driver, self.__WAIT_FOR_ELEMENT_TIMEOUT).until(
            EC.presence_of_element_located(
                (
                    By.TAG_NAME,
                    self.__TOP_CARD,
                )
            )
        )
        self.focus()
        self.wait(5)

        # get name and location
        self.get_name_and_location()

        self.open_to_work = self.is_open_to_work()

        # get about
        self.get_about()
        driver.execute_script(
            "window.scrollTo(0, Math.ceil(document.body.scrollHeight/2));"
        )
        driver.execute_script(
            "window.scrollTo(0, Math.ceil(document.body.scrollHeight/1.5));"
        )

        # get experience
        self.get_experiences()

        # get education
        self.get_educations()

        # get skills
        self.get_skills()

        # get languages
        self.get_languages()

        # get certifications
        self.get_certifications()

        # get honors & awards
        self.get_honors_awards()

        driver.get(self.linkedin_url)

        # get accomplishment
        try:
            _ = WebDriverWait(driver, self.__WAIT_FOR_ELEMENT_TIMEOUT).until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "//*[@class='pv-profile-section pv-accomplishments-section artdeco-container-card artdeco-card ember-view']",
                    )
                )
            )
            acc = driver.find_element(By.XPATH,
                "//*[@class='pv-profile-section pv-accomplishments-section artdeco-container-card artdeco-card ember-view']"
            )
            for block in acc.find_elements(By.XPATH,
                "//div[@class='pv-accomplishments-block__content break-words']"
            ):
                category = block.find_element(By.TAG_NAME, "h3")
                for title in block.find_element(By.TAG_NAME,
                    "ul"
                ).find_elements(By.TAG_NAME, "li"):
                    accomplishment = Accomplishment(category.text, title.text)
                    self.add_accomplishment(accomplishment)
        except:
            pass

        # get connections
        try:
            driver.get("https://www.linkedin.com/mynetwork/invite-connect/connections/")
            _ = WebDriverWait(driver, self.__WAIT_FOR_ELEMENT_TIMEOUT).until(
                EC.presence_of_element_located((By.CLASS_NAME, "mn-connections"))
            )
            connections = driver.find_element(By.CLASS_NAME, "mn-connections")
            if connections is not None:
                for conn in connections.find_elements(By.CLASS_NAME, "mn-connection-card"):
                    anchor = conn.find_element(By.CLASS_NAME, "mn-connection-card__link")
                    url = anchor.get_attribute("href")
                    name = conn.find_element(By.CLASS_NAME, "mn-connection-card__details").find_element(By.CLASS_NAME, "mn-connection-card__name").text.strip()
                    occupation = conn.find_element(By.CLASS_NAME, "mn-connection-card__details").find_element(By.CLASS_NAME, "mn-connection-card__occupation").text.strip()

                    contact = Contact(name=name, occupation=occupation, url=url)
                    self.add_contact(contact)
        except:
            connections = None

        if close_on_complete:
            driver.quit()

    @property
    def company(self):
        if self.experiences:
            return (
                self.experiences[0].institution_name
                if self.experiences[0].institution_name
                else None
            )
        else:
            return None

    @property
    def job_title(self):
        if self.experiences:
            return (
                self.experiences[0].position_title
                if self.experiences[0].position_title
                else None
            )
        else:
            return None

    def __repr__(self):
        return "<Person {name}\n\nAbout\n{about}\n\nExperience\n{exp}\n\nEducation\n{edu}\n\nSkills\n{skills}\n\nLanguages\n{languages}\n\nCertifications\n{certs}\n\nHonors & Awards\n{honors}\n\nInterest\n{int}\n\nAccomplishments\n{acc}\n\nContacts\n{conn}>".format(
            name=self.name,
            about=self.about,
            exp=self.experiences,
            edu=self.educations,
            skills=self.skills,
            languages=self.languages,
            certs=self.certifications,
            honors=self.honors_awards,
            int=self.interests,
            acc=self.accomplishments,
            conn=self.contacts,
        )
