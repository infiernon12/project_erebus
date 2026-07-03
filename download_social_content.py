import os
import random
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
import re

READING_DIR = os.path.join(os.path.dirname(__file__), "alex_reading")
os.makedirs(READING_DIR, exist_ok=True)

# Curated daily digests and trivia in Russian for Filler Girl conversation topics
FALLBACK_FACTS = [
    "Знаете ли вы, что прослушивание музыки во время тренировок может повысить выносливость на 15%? Музыка снижает чувство усталости.",
    "Кошки спят около 70% своей жизни. Это помогает им сохранять энергию для охоты, даже если они живут в теплой квартире.",
    "Фильм 'Барби' Греты Гервиг собрал в мировом прокате более 1.4 миллиарда долларов, став самым кассовым фильмом в истории, снятым женщиной-режиссером.",
    "На Венере день длиннее, чем год. Ей требуется 243 земных дня для оборота вокруг своей оси и всего 225 дней для оборота вокруг Солнца.",
    "Эффект дежавю испытывают около 60-70% людей. Чаще всего он возникает у молодых людей в возрасте от 15 до 25 лет.",
    "В моду входят 'микро-моменты' — короткие периоды полного отдыха от гаджетов в течение дня для перезагрузки внимания.",
    "Древние римляне часто использовали мед как природный антисептик для заживления ран благодаря его естественным антибактериальным свойствам.",
    "Гороскоп дня: Сегодня Луна в гармоничном аспекте с Венерой благоприятствует искренним беседам, поиску взаимопонимания и выражению чувств в личных отношениях. Идеальное время, чтобы написать близким."
]

def fetch_rss_headlines(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, timeout=5) as response:
            xml_data = response.read()
        root = ET.fromstring(xml_data)
        items = []
        for item in root.findall('.//item')[:3]:
            title = item.find('title')
            desc = item.find('description')
            t_text = title.text if title is not None else ""
            d_text = desc.text if desc is not None else ""
            if t_text:
                clean_d = re.sub('<[^<]+?>', '', d_text) if d_text else ""
                items.append(f"{t_text}\\n{clean_d}".strip())
        return items
    except Exception:
        return []

def main():
    print("Starting daily social content download...")
    
    headlines = []
    rss_urls = [
        "https://news.yahoo.com/rss/entertainment",
        "https://news.yahoo.com/rss/lifestyle"
    ]
    
    for url in rss_urls:
        fetched = fetch_rss_headlines(url)
        if fetched:
            headlines.extend(fetched)
            
    # Fallback to local Russian news/horoscopes if network is down
    if not headlines:
        print("Using fallback curated Russian trivia, trends, and horoscopes.")
        headlines = random.sample(FALLBACK_FACTS, 4)
    else:
        # Mix in a couple of local Russian horoscopes/facts to keep it human
        headlines = [h.replace("\n", " ") for h in headlines[:3]]
        headlines.extend(random.sample(FALLBACK_FACTS, 2))
        
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"daily_digest_{timestamp}.txt"
    filepath = os.path.join(READING_DIR, filename)
    
    content = f"--- СОЦИАЛЬНЫЙ ДАЙДЖЕСТ ({datetime.now().strftime('%d.%m.%Y')}) ---\\n\\n"
    for i, item in enumerate(headlines, 1):
        content += f"Тема {i}: {item}\\n\\n"
        
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
        
    print(f"Daily social digest successfully saved to {filepath}")

if __name__ == "__main__":
    main()
