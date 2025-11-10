"""Web crawler for harvesting structured data from the NumPy documentation."""

# coding =utf-8
import sys
from venv import logger
from lcmeval.utils import setup_logger
from bs4 import BeautifulSoup
import json
import time
import os
import requests

class NumpyDocCrawler:
    def __init__(self, logger, root_path):
        self.base_url = 'https://numpy.org/doc/stable/reference'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://numpy.org/',
            'DNT': '1'
        }
        self.logger = logger
        self.root_path = root_path
        if not os.path.exists(self.root_path):
            os.makedirs(self.root_path)
    
    def get_page(self, url):
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.text
        except (requests.exceptions.RequestException, ConnectionError) as e:
            logger.info(f'[ERROR] 请求失败: {url} | 错误类型: {type(e).__name__}')
            logger.info(f'{url}\t{str(e)}')
            return None
        except Exception as e:
            logger.info(f'[WARN] 未知错误: {url} | 错误信息: {str(e)}')
            return None
    
    def retrieve_np_namespace_np(self):
        page_url = f"{self.base_url}/routines.html#routines"
        page = self.get_page(page_url)
        if not page:
            self.logger.info(f"Fail.")
            return None
        
        soup = BeautifulSoup(page, 'html.parser')
        context = soup.select('article.bd-article')[0]
        
        all_inherent_page_links = []
        section = context.find('div', {'class': 'toctree-wrapper compound'})
        if section:
            for li in section.find_all('li', {'class': 'toctree-l1'}):
                link = li.find('a', {'class': 'reference internal'})
                if link and 'href' in link.attrs:
                    all_inherent_page_links.append(link['href'])
        
        for item in all_inherent_page_links[21:]:
            page_link = f"{self.base_url}/{item}"
            page = self.get_page(page_link)
            if not page:
                self.logger.info(f"Fail to obtain {page_link}.")
            parse_all_inherent_api_links = self.parse_all_inherent_api_links(page)
            if parse_all_inherent_api_links:
                retrieved_apis = self.retrive_apis(parse_all_inherent_api_links)
            else:
                retrieved_apis = self.parse_numpy_constant_page(page)
            self.save_data(current_link=item, data=retrieved_apis)
            time.sleep(1)
    
    def retrieve_np_namespace_polynomial(self):
        page_url = f"{self.base_url}/routines.polynomials-package.html#module-numpy.polynomial"
        page = self.get_page(page_url)
        if not page:
            self.logger.info(f"Fail.")
            return None
        parse_all_inherent_api_links = self.parse_all_inherent_api_links(page)
        if parse_all_inherent_api_links:
            for item in parse_all_inherent_api_links:
                print(item)
                all_apis = []
                api_url = f"{self.base_url}/{item}"
                page = self.get_page(api_url)
                if page:
                    api_data = self.parse_normal_page(page)
                    all_apis.append(api_data)
                    all_method_links = self.parse_all_inherent_api_links(page)
                    if all_method_links:
                        for method_link in all_method_links:
                            method_link = f"{self.base_url}/generated/{method_link}"
                            page = self.get_page(method_link)
                            if page:
                                api_data = self.parse_normal_page(page)
                                all_apis.append(api_data)
                            time.sleep(1)
                self.save_data(current_link=item.replace("generated/", ""), data=all_apis)
                time.sleep(1)
    
    def retrieve_np_namespace_random_generator_legacy(self):
        # This function is suitable for /random/legacy.html and /random/generator.html
        page_url = f"{self.base_url}/random/legacy.html"
        page = self.get_page(page_url)
        if not page:
            self.logger.info(f"Fail.")
            return None
        all_apis = []
        soup = BeautifulSoup(page, 'html.parser')
        for page_inherent_api in soup.find_all('dt', {'class':'sig sig-object py'}):
            api_name = page_inherent_api.text.replace("#", "").replace("\n", "")
            detail = page_inherent_api.find_next('dd')
            api_description = detail.select('p')[0].text.replace('\n','').strip()
            
            all_parameters = []
            for item in detail.select('dl.field-list > dt'):
                current_type = item.text.strip().replace(':', '')
                detail = item.find_next('dd')
                params = []
                for param in detail.select('dl > dt'):
                    if param.find('strong'):
                        param_name = param.find('strong').text.strip()
                    else:
                        param_name = param.text.strip()
                    param_type = param.find('span', {'class': 'classifier'}).text.strip() if param.find('span', {'class': 'classifier'}) else None
                    param_desc = param.find_next('dd').text.replace('\n','').strip()
                    params.append({
                        'name': param_name,
                        'type': param_type,
                        'description': param_desc
                    })
                all_parameters.append({current_type: params})
            # parse examples
            examples = []
            for example in soup.select('div.doctest'):
                code_block = example.select_one('pre').text.strip()
                examples.append(code_block)
            all_apis.append({
                    api_name: {
                        "description": api_description,
                        "parameters": all_parameters,
                        "examples": examples,
                    }
                })
        
        all_method_links = self.parse_all_inherent_api_links(page)
        if all_method_links:
            for method_link in all_method_links:
                method_link = f"{self.base_url}/random/{method_link}"
                page = self.get_page(method_link)
                if page:
                    api_data = self.parse_normal_page(page)
                    all_apis.append(api_data)
                time.sleep(1)
        self.save_data(current_link="random.legacy.html", data=all_apis)
        time.sleep(1)
    
    def retrieve_np_namespace_random_bit_generator(self):
        # This function is suitable for /random/bit_generator.html
        page_url = f"{self.base_url}/random/bit_generators/index.html"
        page = self.get_page(page_url)
        if not page:
            self.logger.info(f"Fail.")
            return None
        all_apis = []
        soup = BeautifulSoup(page, 'html.parser')
        
        # all_inherent_page_links = self.parse_all_inherent_api_links(page)
        
        all_inherent_page_links = []
        section = soup.find('div', {'class': 'toctree-wrapper compound'})
        if section:
            for li in section.find_all('li', {'class': 'toctree-l1'}):
                link = li.find('a', {'class': 'reference internal'})
                if link and 'href' in link.attrs:
                    all_inherent_page_links.append(link['href'])
                    
        for inherent_page in all_inherent_page_links:
            page_url = f"{self.base_url}/random/bit_generators/{inherent_page}"
            page = self.get_page(page_url)
            if not page:
                self.logger.info(f"Fail.")
                return None
            all_apis = []
            soup = BeautifulSoup(page, 'html.parser')
            for page_inherent_api in soup.find_all('dt', {'class':'sig sig-object py'}):
                api_name = page_inherent_api.text.replace("#", "").replace("\n", "")
                detail = page_inherent_api.find_next('dd')
                api_description = detail.select('p')[0].text.replace('\n','').strip()
                
                all_parameters = []
                for item in detail.select('dl.field-list > dt'):
                    current_type = item.text.strip().replace(':', '')
                    detail = item.find_next('dd')
                    params = []
                    for param in detail.select('dl > dt'):
                        if param.find('strong'):
                            param_name = param.find('strong').text.strip()
                        else:
                            param_name = param.text.strip()
                        param_type = param.find('span', {'class': 'classifier'}).text.strip() if param.find('span', {'class': 'classifier'}) else None
                        param_desc = param.find_next('dd').text.replace('\n','').strip()
                        params.append({
                            'name': param_name,
                            'type': param_type,
                            'description': param_desc
                        })
                    all_parameters.append({current_type: params})
                # parse examples
                examples = []
                for example in soup.select('div.doctest'):
                    code_block = example.select_one('pre').text.strip()
                    examples.append(code_block)
                all_apis.append({
                        api_name: {
                            "description": api_description,
                            "parameters": all_parameters,
                            "examples": examples,
                        }
                    })
            
            all_method_links = self.parse_all_inherent_api_links(page)
            if all_method_links:
                for method_link in all_method_links:
                    method_link = f"{self.base_url}/random/bit_generators/{method_link}"
                    page = self.get_page(method_link)
                    if page:
                        api_data = self.parse_normal_page(page)
                        all_apis.append(api_data)
                    time.sleep(1)
            self.save_data(current_link=inherent_page.replace("generated/", "n"), data=all_apis)
            time.sleep(1)
    
    def retrieve_np_namespace_np_typing(self):
        # This function is suitable for /numpy.typing.html
        page_url = f"{self.base_url}/typing.html#typing"
        page = self.get_page(page_url)
        if not page:
            self.logger.info(f"Fail.")
            return None
        all_apis = []
        soup = BeautifulSoup(page, 'html.parser')
        
        for page_inherent_api in soup.find_all('dt', {'class':'sig sig-object py'}):
            api_name = page_inherent_api.text.replace("#", "").replace("\n", "")
            detail = page_inherent_api.find_next('dd')
            api_description = detail.select('p')[0].text.replace('\n','').strip()
            
            all_parameters = []
            for item in detail.select('dl.field-list > dt'):
                current_type = item.text.strip().replace(':', '')
                detail = item.find_next('dd')
                params = []
                for param in detail.select('dl > dt'):
                    if param.find('strong'):
                        param_name = param.find('strong').text.strip()
                    else:
                        param_name = param.text.strip()
                    param_type = param.find('span', {'class': 'classifier'}).text.strip() if param.find('span', {'class': 'classifier'}) else None
                    param_desc = param.find_next('dd').text.replace('\n','').strip()
                    params.append({
                        'name': param_name,
                        'type': param_type,
                        'description': param_desc
                    })
                all_parameters.append({current_type: params})
            # parse examples
            examples = []
            for example in soup.select('div.doctest'):
                code_block = example.select_one('pre').text.strip()
                examples.append(code_block)
            all_apis.append({
                    api_name: {
                        "description": api_description,
                        "parameters": all_parameters,
                        "examples": examples,
                    }
                })
        
        
        self.save_data(current_link="random.generator.html", data=all_apis)
    
    def parse_numpy_constant_page(self, page):
         # this function is used to parse https://numpy.org/doc/stable/reference/constants.html
        soup = BeautifulSoup(page, 'html.parser')
        context = soup.select('article.bd-article')[0]
        
        all_constants = []
        for item in context.find_all('dt', {'class': 'sig sig-object py'}):
            all_constants.append(item['id'])
        return all_constants 
    
    def parse_all_inherent_api_links(self, page):
        soup = BeautifulSoup(page, 'html.parser')
        
        all_api_urls = []
        target_containers = soup.find_all('div', {'class': 'pst-scrollable-table-container'})
        for container in target_containers:
            links = container.find_all('a', {'class': 'reference internal'})
            if links:
                all_api_urls.extend([link['href'] for link in links])
        return all_api_urls
    
    def retrive_apis(self, api_links):
        all_apis = []
        for api_url in api_links:
            api_url = f"{self.base_url}/{api_url}"
            page = self.get_page(api_url)
            if page:
                api_data = self.parse_normal_page(page)
                all_apis.append(api_data)
            time.sleep(1)
        return all_apis
    
    def parse_normal_page(self, page):
        # this function is used to parse the most common page, like: https://numpy.org/doc/stable/reference/generated/numpy.empty.html#numpy.empty
        soup = BeautifulSoup(page, 'html.parser')
        context = soup.select('article.bd-article')[0]
        name = context.select('h1')[0].text.replace("#", "") if context.select('h1') else None
        description = context.select('p')[0].text if context.select('p') else None
        print(name)
        
        details = context.select('dl.field-list > dt')
        all_parameters = []
        for item in details:
            current_type = item.text.strip().replace(':', '')
            detail = item.find_next('dd')
            params = []
            for param in detail.select('dl > dt'):
                if param.find('strong'):
                    param_name = param.find('strong').text.strip()
                else:
                    param_name = param.text.strip()
                param_type = param.find('span', {'class': 'classifier'}).text.strip() if param.find('span', {'class': 'classifier'}) else None
                param_desc = param.find_next('dd').text.replace('\n','').strip()
                params.append({
                    'name': param_name,
                    'type': param_type,
                    'description': param_desc
                })
            all_parameters.append({current_type: params})
        
        # parse examples
        examples = []
        for example in context.select('div.doctest'):
            code_block = example.select_one('pre').text.strip()
            examples.append(code_block)
        
        return {
            name: {
                "description": description,
                "parameters": all_parameters,
                "examples": examples,
            }
        }

    
    def save_data(self, current_link, data):
        output_path = os.path.join(self.root_path, f'{current_link}.json')
        self.logger.info(f"There are {len(data)} apis in {current_link}")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)        

if __name__ == '__main__':
    logger = setup_logger("/Users/lichongyang/Documents/Research/research_projects/TestCodeGenModel/routines.html#routines.log")
    crawler = NumpyDocCrawler(logger=logger, root_path="/Users/lichongyang/Documents/Research/research_projects/TestCodeGenModel/")
    crawler.retrieve_np_namespace_random_generator_legacy()
    # page = crawler.get_page("https://www.baidu.com")
    # print(page)
    # print(crawler.parse_numpy_constant_page(page))