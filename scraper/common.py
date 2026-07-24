# -*- coding: utf-8 -*-
"""공통 유틸: HTTP 세션, 아이템 생성, 연락처 추출"""
import hashlib
import json
import os
import re
import requests
import urllib3

urllib3.disable_warnings()

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_keywords():
    """저장소 루트 keywords.json 로드 (없으면 빈 dict)"""
    try:
        with open(os.path.join(ROOT, "keywords.json"), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
PHONE_RE = re.compile(r"0\d{1,2}[-.\s]?\d{3,4}[-.\s]?\d{4}")


def get(url, timeout=25, headers=None, params=None):
    h = {
        "User-Agent": UA,
        "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
        "Sec-Ch-Ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Upgrade-Insecure-Requests": "1",
    }
    if headers:
        h.update(headers)
    try:
        return requests.get(url, headers=h, timeout=timeout, params=params)
    except requests.exceptions.SSLError:
        return requests.get(url, headers=h, timeout=timeout, params=params, verify=False)


def make_id(source, key):
    return source + "-" + hashlib.md5(key.encode("utf-8")).hexdigest()[:12]


def find_email(text):
    m = EMAIL_RE.search(text or "")
    return m.group(0) if m else ""


def find_phone(text):
    m = PHONE_RE.search(text or "")
    return m.group(0) if m else ""


def item(source, category, title, url, company="", description="",
         email="", phone="", posted=""):
    return {
        "id": make_id(source, url or title),
        "source": source,
        "category": category,
        "title": (title or "").strip()[:200],
        "url": url,
        "company": (company or "").strip()[:100],
        "description": (description or "").strip()[:300],
        "email": email,
        "phone": phone,
        "posted": posted,
    }
