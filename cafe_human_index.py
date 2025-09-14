"""Fetch Naver Cafe posts and compute a simple sentiment index."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import List

import requests


HEADERS = {"User-Agent": "Mozilla/5.0"}


@dataclass
class CafePost:
    """Represents a single post summary from a Naver Cafe."""

    title: str
    views: int
    comments: int


def fetch_naver_cafe_posts(club_url: str, max_pages: int = 5) -> List[CafePost]:
    """Fetch post metadata (title, view count, comment count) from a Naver Cafe.

    The Naver mobile site exposes JSON endpoints used for infinite scrolling. This
    helper first resolves the ``club_url`` to a numeric ``clubid`` and then
    iterates ``ArticleList`` pages until the requested ``max_pages`` is reached or
    the API returns no further articles.
    """

    session = requests.Session()
    info_res = session.get(
        "https://apis.naver.com/cafe-web/cafe-mobile/CafeInfo.json",
        params={"cluburl": club_url},
        headers=HEADERS,
        timeout=10,
    )
    info_res.raise_for_status()
    clubid = info_res.json()["message"]["result"]["cafeInfo"]["cafeId"]

    posts: List[CafePost] = []
    for page in range(1, max_pages + 1):
        res = session.get(
            "https://apis.naver.com/cafe-web/cafe-mobile/ArticleList.json",
            params={"search.clubid": clubid, "search.menuid": 0, "search.page": page},
            headers=HEADERS,
            timeout=10,
        )
        res.raise_for_status()
        article_list = res.json()["message"]["result"].get("articleList", [])
        if not article_list:
            break
        for art in article_list:
            posts.append(
                CafePost(
                    title=art.get("subject", ""),
                    views=int(art.get("readCount", 0)),
                    comments=int(art.get("commentCount", 0)),
                )
            )
    return posts


POSITIVE_KEYWORDS = ["상승", "호재", "급등", "매수", "수익"]
NEGATIVE_KEYWORDS = ["하락", "악재", "급락", "매도", "손실"]


def sentiment_score(titles: List[str]) -> float:
    """Compute a naive sentiment index from a list of post titles.

    The score is the difference between positive and negative hits divided by the
    total number of titles, yielding a value between -1 and 1.
    """

    if not titles:
        return 0.0
    pos = sum(any(k in t for k in POSITIVE_KEYWORDS) for t in titles)
    neg = sum(any(k in t for k in NEGATIVE_KEYWORDS) for t in titles)
    return (pos - neg) / len(titles)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch Naver Cafe posts and compute a simple sentiment index"
    )
    parser.add_argument("club_url", help="Cafe URL identifier (e.g. 'likeusstock')")
    parser.add_argument(
        "--pages", type=int, default=5, help="Number of pages to read via API"
    )
    args = parser.parse_args()

    posts = fetch_naver_cafe_posts(args.club_url, args.pages)
    for post in posts:
        print(f"{post.title} (views: {post.views}, comments: {post.comments})")

    score = sentiment_score([p.title for p in posts])
    print(f"Sentiment score: {score:.3f}")


if __name__ == "__main__":
    main()

