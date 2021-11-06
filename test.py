import numpy as np
import requests
from bs4 import BeautifulSoup
from queue import Queue, Empty
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin, urlparse
from flask_cors import CORS
from flask import Flask, request, jsonify, make_response
import sys
from flask_restx import Api, Resource, fields
class MultiThreadScraper:
    def __init__(self, base_url):
        self.base_url = base_url
        self.root_url ='{}://{}'.format(urlparse(self.base_url).scheme,urlparse(self.base_url).netloc)
        self.pool = ThreadPoolExecutor(max_workers=20)
        self.scraped_pages = set([])
        self.to_crawl = Queue()
        self.to_crawl.put(self.base_url)
        self.data = ''
    def parse_links(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        links = soup.find_all('a', href=True)
        file_name = 'result.txt'
        file = open(file_name,'wb')
        for link in links:
            url = link['href'] + '\n'
            file.write(url.encode())
            if url.startswith('/') or url.startswith(self.root_url):
                url = urljoin(self.root_url, url)
                if url not in self.scraped_pages:
                    self.to_crawl.put(url)
    def scrape_info(self, html):
        return
    def post_scrape_callback(self, res):
        result = res.result()
        if result and result.status_code == 200:
            self.parse_links(result.text)
            self.scrape_info(result.text)
    def scrape_page(self, url):
        try:
            res = requests.get(url, timeout=(3, 30))
            return res
        except requests.RequestException:
            return
    def run_scraper(self):
        while True:
            try:
                target_url = self.to_crawl.get(timeout=60)
                if target_url not in self.scraped_pages:
                    print("Scraping URL: {}".format(target_url))
                    self.scraped_pages.add(target_url)
                    job = self.pool.submit(self.scrape_page, target_url)
                    job.add_done_callback(self.post_scrape_callback)
                    print("Job completed successfully")
            except Empty:
                return
            except Exception as e:
                print(e)
                continue
flask_app = Flask(__name__)
CORS(flask_app)
app = Api(app=flask_app,version="1.0",title="Multi-threaded scraping utility",description="Scrape data from URL")
name_space = app.namespace('scraper', description='Scraping APIs')
model = app.model('Scraping params',{'url': fields.String(required=True,description="URL for scraping",help="URL cannot be left blank"),})
flask_app.run()
@name_space.route("/")
class MainClass(Resource):
    def options(self):
        response = make_response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Headers', "*")
        response.headers.add('Access-Control-Allow-Methods', "*")
        return response
    @app.expect(model)
    def post(self):
        try:
            formData = request.json
            input_raw = [val for val in formData.values()]
            # input_raw[0] is the url
            s = MultiThreadScraper(input_raw[0])
            s.run_scraper()
            response = jsonify({"statusCode": 200,"status": "Scraping Completed","result": "Scraping has been done.Please check the folder for content",})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
        except Exception as error:
            return jsonify({"statusCode": 500,"status": "Could not scrape","result": "Please review your response and try again","error": str(error)})
