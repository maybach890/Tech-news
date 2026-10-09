import yaml
import feedparser
import hashlib
import json
import os
import re
from datetime import datetime, timezone


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_yaml(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


feeds_config = load_yaml(
    os.path.join(BASE_DIR, "config", "feeds.yaml")
)

keywords_config = load_yaml(
    os.path.join(BASE_DIR, "config", "keywords.yaml")
)


def normalize(text):
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def score_article(title, summary):
    text = normalize(title + " " + summary)

    score = 0
    matched = []

    for keyword in keywords_config["countries"]:
        if keyword.lower() in text:
            score += 2
            matched.append(keyword)

    for keyword in keywords_config["technology"]:
        if keyword.lower() in text:
            score += 2
            matched.append(keyword)

    for keyword in keywords_config["geopolitics"]:
        if keyword.lower() in text:
            score += 3
            matched.append(keyword)

    for keyword in keywords_config["high_priority"]:
        if keyword.lower() in text:
            score += 4
            matched.append(keyword)

    return score, list(set(matched))


def article_id(title):
    return hashlib.sha256(
        title.encode("utf-8")
    ).hexdigest()


articles = []


for feed in feeds_config["feeds"]:

    print(f"Fetching: {feed['name']}")

    parsed = feedparser.parse(feed["url"])

    for item in parsed.entries[:30]:

        title = item.get("title", "")
        summary = item.get("summary", "")
        link = item.get("link", "")

        score, matched = score_article(title, summary)

        articles.append({
            "id": article_id(title),
            "source": feed["name"],
            "title": title,
            "summary": summary,
            "link": link,
            "score": score,
            "matched": matched
        })


# Remove duplicates
unique = {}

for article in articles:
    unique[article["id"]] = article

articles = list(unique.values())


# Sort by geopolitical relevance
articles.sort(
    key=lambda x: x["score"],
    reverse=True
)


report_date = datetime.now(
    timezone.utc
).strftime("%Y-%m-%d")


report_path = os.path.join(
    BASE_DIR,
    "reports",
    f"{report_date}.md"
)


with open(report_path, "w", encoding="utf-8") as f:

    f.write(
        f"# Technology & Geopolitics Daily Brief\n\n"
    )

    f.write(
        f"Date: {report_date}\n\n"
    )

    f.write(
        "## High Priority\n\n"
    )

    for article in articles[:20]:

        f.write(
            f"### [{article['title']}]"
            f"({article['link']})\n\n"
        )

        f.write(
            f"**Source:** {article['source']}\n\n"
        )

        f.write(
            f"**Score:** {article['score']}\n\n"
        )

        f.write(
            f"**Keywords:** "
            f"{', '.join(article['matched'])}\n\n"
        )

        f.write(
            f"{article['summary'][:500]}\n\n"
        )

        f.write("---\n\n")


print(
    f"Generated report: {report_path}"
)
