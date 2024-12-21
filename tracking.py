from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from datetime import datetime
import re
import os



class TrackingService:
    def __init__(self):
        CHROMEDRIVER_PATH=os.environ.get("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")
        self.options = Options()
        service = Service(CHROMEDRIVER_PATH)
        
        # Performance optimizations
        self.options.page_load_strategy = 'eager'  # Don't wait for all resources
        self.options.add_argument("--headless")
        self.options.add_argument("--no-sandbox")
        self.options.add_argument('--disable-gpu')
        self.options.add_argument('--disable-dev-shm-usage')
        self.options.add_argument('--disable-extensions')
        self.options.add_argument('--disable-infobars')
        self.options.add_argument('--disable-notifications')
        self.options.add_argument('--disable-offer-store-unmasked-wallet-cards')
        self.options.add_argument('--disable-offer-upload-credit-cards')
        self.options.add_argument('--disable-popup-blocking')
        self.options.add_argument('--blink-settings=imagesEnabled=false')  # Disable images
        self.options.add_argument('--ignore-ssl-errors=yes')
        self.options.add_argument('--ignore-certificate-errors')
        
        # Add performance preferences
        self.options.add_experimental_option('prefs', {
            'profile.default_content_setting_values.cookies': 2,
            'profile.default_content_setting_values.images': 2,
            'profile.default_content_setting_values.notifications': 2,
            'profile.default_content_setting_values.plugins': 2,
            'profile.managed_default_content_settings.javascript': 1
        })
        
        self.driver = webdriver.Chrome(service=service, options=self.options)
        self.wait = WebDriverWait(self.driver, 10)
        self.driver.get("https://tracking.post.ir/")
        
    def search_tracking(self, track_code):
        self.start = datetime.now()
        # Use explicit waits instead of implicit
        search_input = self.wait.until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="txtbSearch"]'))
        )
        search_input.clear()
        search_input.send_keys(track_code)
        
        search_button = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="btnSearch"]'))
        )
        search_button.click()
        
        return self.scrap_result()
    
    
    def scrap_result(self):
        page_source = self.driver.page_source
        if "بارکد نامعتبر است." in page_source : return False
        soup = BeautifulSoup(page_source, "html.parser")

        def get_next_text(label_text):
            lbl = soup.find(text=label_text)
            if lbl:
                next_el = lbl.find_next()
                if next_el:
                    return next_el.text.strip()
            return ""

        # Extract the tracking number from the input field
        tracking_number_input = soup.find('input', {'name': 'txtbSearch'})
        tracking_number = tracking_number_input['value'] if tracking_number_input else None

        # Extract tracking info rows
        tracking_info = []
        data_rows = soup.select('#pnlResult .newrowdata')

        for row in data_rows:
            cells = row.select('.newtddata')
            if len(cells) == 4:
                step_info = {
                    'step': cells[0].get_text(strip=True),
                    'description': cells[1].get_text(strip=True),
                    'location': cells[2].get_text(strip=True),
                    'time': cells[3].get_text(strip=True)
                }

                # Check if there's a link to show postman info in the description cell
                link = cells[1].find('a', string=re.compile(r'\(مشاهده اطلاعات نامه رسان\)'))
                if link and 'onclick' in link.attrs:
                    # The onclick attribute contains something like: "$('.moreinfo').fadeOut(0); $('#showuser1').fadeIn(100);"
                    # We need to extract the ID: showuser1
                    onclick = link['onclick']
                    match = re.search(r"#(showuser\d+)", onclick)
                    if match:
                        moreinfo_id = match.group(1)
                        # Now find the corresponding moreinfo div
                        moreinfo_div = soup.find('div', id=moreinfo_id, class_='moreinfo')
                        if moreinfo_div:
                            # Extract postman info: The name is in a div.text-center below the img
                            postman_img = moreinfo_div.find('img', class_='postmanimg')
                            postman_name_div = postman_img.find_next('div', class_='text-center') if postman_img else None
                            postman_info = {
                                'name': postman_name_div.get_text(strip=True) if postman_name_div else None,
                                'image_url': 'https://tracking.post.ir' + postman_img['src'] if postman_img else None
                            }
                            step_info['postman'] = postman_info

                tracking_info.append(step_info)


        # Extract parcel info
        parcel_info = {
            'contents': get_next_text('محتویات مرسوله :'),
            'service_type': get_next_text('نوع سرویس :'),
            'origin_post_office': get_next_text('دفتر پستی مبداء:'),
            'origin': get_next_text('مبدا:'),
            'destination': get_next_text('مقصد :'),
            'sender': get_next_text('نام فرستنده :'),
            'receiver': get_next_text('نام گیرنده :'),
            'weight': get_next_text('وزن :'),
            'postal_cost': get_next_text('هزینه پستی :'),
            # Additional costs, if needed:
            'tax': get_next_text('ماليات بر ارزش افزوده :') or get_next_text('مالیات بر ارزش افزوده :'),
            'total_postal_cost': get_next_text('هزينه پستي (با ماليات) :')
        }
        self.end = datetime.now()
        
        data = {
            'success': True,
            'tracking_number': tracking_number,
            'tracking_info': tracking_info,
            'parcel_info': parcel_info,
            'elapsed_time': str(self.end-self.start)
        }
        
        
        
        return data