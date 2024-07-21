"""
introduce:
    此 脚本用于下载WRF-Hydro所需的FORCING数据（NLDAS数据），
    单个NLDAS数据来源如：
            https://hydro1.gesdisc.eosdis.nasa.gov/data/NLDAS/NLDAS_FORA0125_H.002/2024/032/NLDAS_FORA0125_H.A20240201.0100.002.grb
    所有用户都必须在 Earthdata 登录系统上注册才能访问 GES DISC 数据，可通过下面链接注册
        [earthdata login](https://urs.earthdata.nasa.gov/oauth/authorize?response_type=code&redirect_uri=http%3A%2F%2Fdisc.gsfc.nasa.gov%2Flogin%2Fcallback&client_id=C_kKX7TXHiCUqzt352ZwTQ)
    其它关于Earthdata数据访问问题及流程可查看下面链接
        https://disc.gsfc.nasa.gov/information/documents?title=Data%20Access
parameters:
    start_date: datetime
        开始时间
    end_date: datetime
        结束时间
    username: str
        NASA Earthdata账号登陆用户名
    password: str
        NASA Earthdata账号登陆用户名
    dld_dir: str
        下载的NLDAS数据保存的路径
usage:
    main()
"""

import requests
from pathlib import Path, PosixPath
from datetime import datetime, timedelta
import os, shutil
import tqdm

start_date = datetime(2024, 1, 3, 0, 0, 0)
end_date = datetime(2024, 1, 3, 23, 0, 0)
username = "ManaSakura"
password = "Txy199906301152"
dld_dir = r'./Results/NLDAS_dld'

class SessionWithHeaderRedirection(requests.Session):

    AUTH_HOST = 'urs.earthdata.nasa.gov'

    def __init__(self, username, password):
        super().__init__()
        self.auth = (username, password)

    # Overrides from the library to keep headers when redirected to or from
    # the NASA auth host.

    def rebuild_auth(self, prepared_request, response):
        headers = prepared_request.headers
        url = prepared_request.url

        if 'Authorization' in headers:
            original_parsed = requests.utils.urlparse(response.request.url)
            redirect_parsed = requests.utils.urlparse(url)

            if (original_parsed.hostname != redirect_parsed.hostname) and \
                    redirect_parsed.hostname != self.AUTH_HOST and \
                    original_parsed.hostname != self.AUTH_HOST:
                del headers['Authorization']
        return

def download_files_from_url(session, urls, out_dir):

    responses = []

    # display progress bar (thanks tqdm!) and download the files
    for url in tqdm.tqdm(urls, ncols=80):
        # extract the filename from the url to be used when saving the file
        filename = url[url.rfind('/') + 1:]

        try:
            # submit the request using the session
            response = session.get(url, stream=True)
            responses.append(response)

            # raise an exception in case of http errors
            response.raise_for_status()

            # save the file
            with open(os.path.join(out_dir, filename), 'wb') as fd:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    fd.write(chunk)

        except requests.exceptions.HTTPError as e:
            # handle any errors here
            print(e)

    return responses

def downloader(start_date, end_date, username, password, save_dir='./'):

    date_list = []
    url_list = []
    current_date = start_date
    session = SessionWithHeaderRedirection(username, password)
    while current_date <= end_date:
        date_list.append(current_date)
        current_date += timedelta(hours=1)
    for date in date_list:
        int_year, int_month, int_day, int_hr = date.year, date.month, date.day, date.hour
        url = get_url(int_year, int_month, int_day, int_hr)
        url_list.append(url)
    download_files_from_url(session, url_list, save_dir)

def get_url(year:int, month:int, day:int, hr:int):

    DOY = ymd_to_doy(year, month, day)
    YYYY = str(year)
    MM = str(month).zfill(2)
    DD = str(day).zfill(2)
    HH = str(hr).zfill(2)
    URL = f'https://hydro1.gesdisc.eosdis.nasa.gov/data/NLDAS/NLDAS_FORA0125_H.002/{YYYY}/{DOY}/NLDAS_FORA0125_H.A{YYYY}{MM}{DD}.{HH}00.002.grb'

    return URL

def ymd_to_doy(year, month, day):
    """

    :param year: int
    :param month: int
    :param day: int
    :return: str
    """
    date = datetime(year, month, day)
    date_doy = date.timetuple().tm_yday
    return str(date_doy).zfill(3)

def main():
    if os.path.exists(dld_dir):
        shutil.rmtree(dld_dir)
    os.mkdir(dld_dir)
    downloader(start_date, end_date, username, password, dld_dir)
if __name__ == "__main__":
    main()