#!/usr/bin/env python3

import requests
import re

BASE_URL = "https://kenwood.garmin.com"
MAIN_URL = "/kenwood/site/filterHeadUnitList"

reqs = requests.Session()

def get_url(url, params = {}, outfile = None):
    global reqs
    print("Now fetching {} ...".format(url))
    #print(repr(params))
    req = reqs.get(url, params=params)
    page = req.content
    #if outfile:
    #    with open(outfile, "wb") as f:
    #        f.write(page)
    page = str(page).replace("\\n", "").replace("\\r", "").replace("\\t", "")
    page = re.sub(r"\s+", " ", page)
    return page

devlist = get_url(BASE_URL + MAIN_URL, {"regionKey": 0, "seriesKey": 0}, "kenmain.html")
devices = re.findall(r"<div class=\"item\"> <a href=\"(.*?)\">(.*?)</a> </div>", devlist)

print("Found {} devices.".format(len(devices)))
#print(repr(devices))

f = open("kenfiles.txt", "wt")
f.write("# Download with: wget -x -nc -i kenfiles.txt\n\n")

for dev in devices:
    (url, devname) = dev
    print("Checking updates for {} ...".format(devname.strip()))
    url = url.strip()
    (url, paramstr) = url.split("?", 1)
    parampairs = paramstr.split("&")
    params = {}
    for p in parampairs:
        (key, val) = p.split("=", 1)
        params[key] = val
    params["origin"] = "productUpdate"   # gets added via JavaScript?

    devpage = get_url(BASE_URL + url, params, "kendev.html")

    updateLink = re.search(r"(/kenwood/site/softwareUpdates.*?)\\", devpage)

    if not updateLink:
        print("### No updates for {} found.".format(devname))
        continue

    updateLink = updateLink.group(1)
    #print(repr(updateLink))

    updpage = get_url(BASE_URL + updateLink, {}, "kenupd.html")
    #print(repr(updpage))

    links = re.findall(r"(https?://.*?)[\\\"']", updpage)

    f.write("# {}\n".format(devname))
    for l in links:
        if l.endswith(("favicon.ico", "garmin.png", "termsOfUse.htm", "privacy-statement", "/us/")):
            continue
        #print(repr(l))
        f.write(l)
        f.write("\n")
    f.write("\n")

f.close()
