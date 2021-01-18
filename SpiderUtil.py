import os
import re
import csv
import json
import logging
import asyncio
import collections
import urllib.parse

import aiohttp


PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))


class SpiderUtil:
    BASE_URL = "http://139.64.56.74:19100/api/getoasresult"
    QUERY_STRING = {
        "sid": "geo_parser_custom_info",
        "output_type": "1,2,3,4,6,8,9,10,13"
    }
    PATH_PARSE = (
        ("result.segmentAddr", "segment"),
        ("result.structText", "structure"),
        ("result.formattedText", "complete"),
        ("result.poiCategory", "poi_category"),
        ("result.zipCode", "zipcode"),
        ("result.poiPredict", "poi_predict"),
        ("result.offlineLocation", "gcj02"),
        ("result.wgs84Location", "wgs84"),
        ("result.unifyAddressInfo.unifyAddress", "poi_alias_list"),
        ("result.policeStation", "block_mapping")
    )
    REGEX_INT = re.compile(r"^\d+$")

    @classmethod
    def _get_finish(cls, file_path_write, index=0) -> set:
        finish = set()
        if os.path.isfile(file_path_write):
            with open(file_path_write, encoding="utf-8", newline="") as f:
                spam_reader = csv.reader(f)
                for row in spam_reader:
                    addr = row[index].strip()
                    if addr:
                        finish.add(addr)
        return finish

    @classmethod
    def read_from_file(cls, file_path_read, file_path_write) -> collections.Iterator:
        finish = cls._get_finish(file_path_write)
        with open(file_path_read, encoding="utf-8", newline="\n") as f:
            line_num = 0
            for line in f:
                line_num += 1
                addr = line.strip()
                if addr and addr not in finish:
                    cls.QUERY_STRING["addr"] = addr
                    url = "{}?{}".format(cls.BASE_URL, urllib.parse.urlencode(cls.QUERY_STRING))
                    finish.add(addr)
                    yield {"url": url, "method": "get", "extra": [addr, line_num]}

    @classmethod
    def _write(cls, file_path_write, row) -> None:
        with open(file_path_write, "a", encoding="utf-8", newline="") as f:
            spam_writer = csv.writer(f)
            spam_writer.writerow(row)

    @classmethod
    async def worker(cls, iterator: collections.Iterator, file_path_write):
        async with aiohttp.ClientSession() as session:
            for kwargs in iterator:
                row = kwargs.pop("extra", [])
                url = kwargs["url"]
                if not url:
                    cls._write(file_path_write, [])
                    continue
                try:
                    async with session.request(**kwargs) as response:
                        if hasattr(response, "status") and response.status == 200:
                            ret = json.loads(await response.text(encoding="utf-8"))
                            if isinstance(ret, dict) and ret.get("status", "") == "OK":
                                for path_parse, func_name in cls.PATH_PARSE:
                                    current_data = ret
                                    path_list = path_parse.split(".")
                                    max_ind = len(path_list) - 1
                                    for ind, p in enumerate(path_list):
                                        if ind < max_ind:
                                            current_data = current_data.get(p, {})
                                        else:
                                            row.append(current_data.get(p, ""))
                                cls._write(file_path_write, row)
                except Exception as e:
                    logging.error("Exception: url={}, exception={}".format(url, str(e)))


def main():
    fpr = os.path.join(PROJECT_ROOT, "addr.txt")
    fpw = os.path.join(PROJECT_ROOT, "result.txt")
    ite = SpiderUtil.read_from_file(fpr, fpw)
    parallel = 10
    tasks = []
    for _ in range(parallel):
        tasks.append(SpiderUtil.worker(ite, fpw))
    lo = asyncio.get_event_loop()
    current = lo.time()
    print("---------- start ----------")
    lo.run_until_complete(asyncio.gather(*tasks))
    print("---------- finish takes={}s ----------".format(lo.time() - current))


if __name__ == "__main__":
    main()
