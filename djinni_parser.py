import asyncio
import csv
import time
from dataclasses import dataclass, fields, astuple
from datetime import datetime
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup
from httpx import AsyncClient

BASE_URL = "https://djinni.co/"
URL = "https://djinni.co/jobs/?primary_keyword=Python"


@dataclass
class Job:
    title: str
    url: str
    category: str
    technologies: list
    english: str
    experience: int


JOB_FIELDS = [field.name for field in fields(Job)]


class DjinniScraper(object):
    def __init__(self, url):
        self.url = url
        self.job_urls = []
        self.pages = self.get_num_pages()
        asyncio.run(self.main())

    def get_num_pages(self) -> int:
        response = httpx.get(self.url)
        soup = BeautifulSoup(response.content, "html.parser")
        pagination = soup.select_one(".pagination")
        self.job_urls = [urljoin(BASE_URL, job_url.attrs["href"]) for job_url in soup.select(".profile")]

        if pagination is None:
            return 1
        return int(pagination.select("li")[-2].text)

    async def get_all_job_urls(self, page: int, client: AsyncClient) -> None:
        response = await client.get(self.url, params={"page": page})
        soup = BeautifulSoup(response.content, "html.parser")
        self.job_urls.extend([urljoin(BASE_URL, job_url.attrs["href"]) for job_url in soup.select(".profile")])

    @staticmethod
    async def get_job_details(url, client):
        response = await client.get(url)
        soup = BeautifulSoup(response, "html.parser")
        additional_info = soup.select_one(".job-additional-info--body").select("li")
        technologies = None
        english = None
        for info in additional_info:
            if "Категорія:" in info.text:
                category = info.text.split()[-1]
                continue
            if "досвіду" in info.text:
                try:
                    experience = int(info.text.split()[0])
                except ValueError:
                    experience = 0
                continue
            if "Англ" in info.text:
                english = info.text.split()[-1]
                continue
            else:
                technologies = list(map(str.strip, info.text.replace("/", ",").split(",")))

        return Job(
            title=soup.select_one(".detail--title-wrapper").text.strip(),
            url=url,
            category=category,
            technologies=technologies,
            english=english,
            experience=experience
        )

    async def main(self) -> None:
        now = datetime.now().today()
        file_name = f"python_vacancies-{now.date()}-{now.hour}:{now.minute}.csv"
        with open(file_name, "w") as file:
            writer = csv.writer(file)
            writer.writerow(JOB_FIELDS)
            async with AsyncClient(verify=False) as client:
                await asyncio.gather(*[self.get_all_job_urls(page, client) for page in range(2, self.pages + 1)])
                jobs = await asyncio.gather(*[self.get_job_details(url, client) for url in self.job_urls])
                writer.writerows(astuple(job) for job in jobs)


start_time = time.perf_counter()
djinni = DjinniScraper(url=URL)
end_time = time.perf_counter()
print("Elapsed:", end_time - start_time)
