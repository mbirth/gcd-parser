# -*- coding: utf-8 -*-

"""
Many thanks to Alex Whiter whom this work is based on.
See https://github.com/AlexWhiter/GarminRelatedStuff/tree/master/GetFirmwareUpdates .
"""

from . import devices
from .proto import GetAllUnitSoftwareUpdates_pb2
from xml.dom.minidom import getDOMImplementation, parseString
from urllib.parse import unquote
import requests

PROTO_API_GETALLUNITSOFTWAREUPDATES_URL = "http://omt.garmin.com/Rce/ProtobufApi/SoftwareUpdateService/GetAllUnitSoftwareUpdates"
WEBUPDATER_SOFTWAREUPDATE_URL = "https://www.garmin.com/support/WUSoftwareUpdate.jsp"
GRMN_CLIENT_VERSION = "6.17.0.0"

class UpdateInfo:
    def __init__(self):
        self.source = None
        self.sku = None
        self.device_name = None
        self.fw_version = None
        self.license_url = None
        self.changelog = None
        self.notes = None
        self.language_code = None
        self.update_type = None
        self.local_filename = None
        self.files = []
        self.build_type = None
        self.additional_info_url = None

    def fill_from_protobuf(self, protobuf_info):
        self.source = "Express"
        self.sku = protobuf_info.product_sku
        self.device_name = protobuf_info.device_name
        self.fw_version = protobuf_info.fw_version
        self.license_url = protobuf_info.license_url
        self.changelog = "\n".join(protobuf_info.changelog)
        self.language_code = protobuf_info.language
        self.local_filename = protobuf_info.update_file
        self.update_type = protobuf_info.file_type
        for i in protobuf_info.files_list:
            self.files.append( {
                "url": i.url,
                "md5": i.md5,
                "size": i.file_size,
                "size_is_rounded": False,
            } )

    # From https://docs.python.org/3/library/xml.dom.minidom.html
    def dom_get_text(self, node_list):
        rc = []
        for rnode in node_list:
            for node in rnode.childNodes:
                if node.nodeType == node.TEXT_NODE:
                    rc.append(node.data)
        return ''.join(rc)

    def fill_from_response_dom(self, dom):
        self.source = "WebUpdater"
        self.sku = self.dom_get_text(dom.getElementsByTagName("RequestedPartNumber"))
        self.device_name = self.dom_get_text(dom.getElementsByTagName("Description"))
        version_major = self.dom_get_text(dom.getElementsByTagName("VersionMajor"))
        version_minor = self.dom_get_text(dom.getElementsByTagName("VersionMinor"))
        if len(version_minor) > 0:
            self.fw_version = "{}.{:0>2s}".format(version_major, version_minor)
        self.license_url = self.dom_get_text(dom.getElementsByTagName("LicenseLocation"))
        self.changelog = unquote(self.dom_get_text(dom.getElementsByTagName("ChangeDescription"))).replace("+", " ")
        self.notes = unquote(self.dom_get_text(dom.getElementsByTagName("Notes"))).replace("+", " ")
        self.language_code = self.dom_get_text(dom.getElementsByTagName("RequestedRegionId"))
        self.build_type = self.dom_get_text(dom.getElementsByTagName("BuildType"))
        self.additional_info_url = self.dom_get_text(dom.getElementsByTagName("AdditionalInfo"))
        files = dom.getElementsByTagName("UpdateFile")
        for f in files:
            # For some reason, WebUpdater returns file size in KiB instead of Bytes
            size_kb = self.dom_get_text(f.getElementsByTagName("Size"))
            size_bytes = float(size_kb) * 1024
            self.files.append( {
                "url": self.dom_get_text(f.getElementsByTagName("Location")),
                "md5": self.dom_get_text(f.getElementsByTagName("MD5Sum")),
                "size": size_bytes,
                "size_is_rounded": True,
            } )

    def get_json(self):
        # TODO
        pass

    def __str__(self):
        url = "-"
        if len(self.files) > 0:
            url = self.files[0]["url"]
        txt = "[{}] {} {} {}: {}".format(self.source, self.sku, self.device_name, self.fw_version, url)
        if self.changelog:
            txt += "\nChangelog:\n" + self.changelog
        if self.notes:
            txt += "\n\nNotes:\n" + self.notes
        if self.additional_info_url:
            txt += "\nAdditional Information: " + self.additional_info_url
        return txt

    def __repr__(self):
        return "[{}] {} {} {}".format(self.source, self.sku, self.device_name, self.fw_version)

class UpdateServer:

    def __init__(self):
        self.device_id = "2345678910"
        self.unlock_codes = []
        self.debug = False

    def query_express(self, sku_numbers):
        # Garmin Express Protobuf API
        device_xml = self.get_device_xml(sku_numbers)
        reply = self.get_unit_updates(device_xml)
        results = []
        if reply:
            for i in range(0, len(reply.update_info)):
                ui = reply.update_info[i]
                r = UpdateInfo()
                r.fill_from_protobuf(ui)
                results.append(r)
        return results

    def query_webupdater(self, sku_numbers):
        # WebUpdater
        requests_xml = self.get_requests_xml(sku_numbers)
        reply = self.get_webupdater_softwareupdate(requests_xml)

        # ElementTree might have been easier if it wouldn't be so obnoxious with namespaces
        # See https://stackoverflow.com/questions/14853243/parsing-xml-with-namespace-in-python-via-elementtree
        dom = parseString(reply)

        results = []
        for resp in dom.getElementsByTagName("Response"):
            uf = resp.getElementsByTagName("UpdateFile")
            if len(uf) == 0:
                # Empty result
                continue
            r = UpdateInfo()
            r.fill_from_response_dom(resp)
            results.append(r)

        return results

    def query_updates(self, sku_numbers, query_express=True, query_webupdater=True):
        results = []

        if query_express:
            results.append(self.query_express(sku_numbers))

        if query_webupdater:
            results.append(self.query_webupdater(sku_numbers))

        return results

    def dom_add_text(self, doc, parent, elem_name, text):
        e = doc.createElement(elem_name)
        t = doc.createTextNode(text)
        e.appendChild(t)
        parent.appendChild(e)

    def get_device_xml(self, sku_numbers):
        dom = getDOMImplementation()
        doc = dom.createDocument(None, "Device", None)

        root = doc.documentElement

        root.setAttribute("xmlns", "http://www.garmin.com/xmlschemas/GarminDevice/v2")
        root.setAttribute("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
        root.setAttribute("xsi:schemaLocation", "http://www.garmin.com/xmlschemas/GarminDevice/v2 http://www.garmin.com/xmlschemas/GarminDevicev2.xsd")

        model = doc.createElement("Model")
        self.dom_add_text(doc, model, "PartNumber", sku_numbers[0])
        self.dom_add_text(doc, model, "SoftwareVersion", "1")
        self.dom_add_text(doc, model, "Description", "-")
        root.appendChild(model)

        self.dom_add_text(doc, root, "Id", self.device_id)

        for uc in self.unlock_codes:
            ul = doc.createElement("Unlock")
            self.dom_add_text(doc, ul, "Code", uc)
            root.appendChild(ul)

        msm = doc.createElement("MassStorageMode")
        for sku in sku_numbers:
            uf = doc.createElement("UpdateFile")
            self.dom_add_text(doc, uf, "PartNumber", sku)
            v = doc.createElement("Version")
            self.dom_add_text(doc, v, "Major", "0")
            self.dom_add_text(doc, v, "Minor", "00")
            uf.appendChild(v)
            self.dom_add_text(doc, uf, "Path", "GARMIN")
            self.dom_add_text(doc, uf, "FileName", "GUPDATE.GCD")
            msm.appendChild(uf)
        root.appendChild(msm)

        xml = doc.toxml("utf-8")
        return xml

    def get_requests_xml(self, sku_numbers):
        dom = getDOMImplementation()
        doc = dom.createDocument(None, "Requests", None)
        doc.standalone = False

        root = doc.documentElement

        root.setAttribute("xmlns", "http://www.garmin.com/xmlschemas/UnitSoftwareUpdate/v3")

        for sku in sku_numbers:
            req = doc.createElement("Request")
            self.dom_add_text(doc, req, "PartNumber", sku)
            self.dom_add_text(doc, req, "TransferType", "USB")

            reg = doc.createElement("Region")
            self.dom_add_text(doc, reg, "RegionId", "14")

            ver = doc.createElement("Version")
            self.dom_add_text(doc, ver, "VersionMajor", "0")
            self.dom_add_text(doc, ver, "VersionMinor", "1")
            self.dom_add_text(doc, ver, "BuildType", "Release")

            reg.appendChild(ver)
            req.appendChild(reg)
            root.appendChild(req)

        xml = doc.toxml("utf-8")
        return xml

    def get_unit_updates(self, device_xml):
        query = GetAllUnitSoftwareUpdates_pb2.GetAllUnitSoftwareUpdates()
        query.client_data.client = "express"
        query.client_data.language ="en_GB"
        query.client_data.client_platform = "Windows"
        query.client_data.client_platform_version = "1000 "
        query.device_xml = device_xml
        proto_msg = query.SerializeToString()

        if self.debug:
            #print(proto_msg)
            with open("protorequest.bin", "wb") as f:
                f.write(proto_msg)
                f.close()

        headers = {
            "User-Agent": "Garmin Express Win - {}".format(GRMN_CLIENT_VERSION),
            "Garmin-Client-Name": "Express",
            "Garmin-Client-Version": GRMN_CLIENT_VERSION,
            "X-garmin-client-id": "EXPRESS",
            "Garmin-Client-Platform": "windows",
            "Garmin-Client-Platform-Version": "1000",
            "Garmin-Client-Platform-Version-Revision": "0",
            "Content-Type": "application/octet-stream",
        }

        r = requests.post(PROTO_API_GETALLUNITSOFTWAREUPDATES_URL, headers=headers, data=proto_msg)

        if r.status_code != 200:
            r.raise_for_status()
            return None

        if self.debug:
            #print(r.content)
            with open("protoreply.bin", "wb") as f:
                f.write(r.content)
                f.close()

        reply = GetAllUnitSoftwareUpdates_pb2.GetAllUnitSoftwareUpdatesReply()
        reply.ParseFromString(r.content)

        return reply

    def get_webupdater_softwareupdate(self, requests_xml):
        headers = {
            "User-Agent": "Undefined agent",
        }

        data = {
            "req": requests_xml,
        }

        r = requests.post(WEBUPDATER_SOFTWAREUPDATE_URL, headers=headers, data=data)

        if r.status_code != 200:
            r.raise_for_status()
            return None

        if self.debug:
            #print(r.content)
            with open("webupdaterreply.xml", "wb") as f:
                f.write(r.content)
                f.close()

        return r.content
