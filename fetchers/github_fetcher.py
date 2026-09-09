"""
Fetch GitHub Trending Repositories
"""

import requests
from bs4 import BeautifulSoup
import re


def get_trending_repos(language: str = None, since: str = "daily", max_results: int = 50) -> list:
    """
    Fetch GitHub Trending repositories by scraping the page.

    Args:
        language: Programming language filter (python, javascript, go, rust, etc.)
                  Use None or "all" for all languages
        since: Time range (daily, weekly, monthly)
        max_results: Maximum number of repos to return

    Returns:
        List[Dict]: Repos with repo_name, description, language, stars, stars_today, forks, repo_url
    """
    # Build URL
    if language and language.lower() != "all":
        url = f"https://github.com/trending/{language.lower()}?since={since}"
    else:
        url = f"https://github.com/trending?since={since}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
    except Exception as e:
        print(f"Failed to fetch GitHub trending page: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    repos = []

    # Find all repo articles
    repo_articles = soup.find_all("article", class_="Box-row")

    for article in repo_articles[:max_results]:
        try:
            # Extract repo name (owner/repo)
            h2 = article.find("h2")
            if not h2:
                continue

            repo_link = h2.find("a")
            if not repo_link:
                continue

            repo_path = repo_link.get("href", "").strip("/")
            if "/" not in repo_path:
                continue

            parts = repo_path.split("/")
            if len(parts) < 2:
                continue

            owner = parts[0]
            repo_name = parts[1]
            full_name = f"{owner}/{repo_name}"
            repo_url = f"https://github.com/{full_name}"

            # Extract description
            desc_p = article.find("p", class_="col-9")
            description = desc_p.get_text(strip=True) if desc_p else ""

            # Extract programming language
            lang_span = article.find("span", itemprop="programmingLanguage")
            language_name = lang_span.get_text(strip=True) if lang_span else ""

            # Extract total stars
            stars = 0
            star_links = article.find_all("a", href=re.compile(r"/stargazers"))
            if star_links:
                star_text = star_links[0].get_text(strip=True).replace(",", "")
                try:
                    stars = int(star_text)
                except:
                    pass

            # Extract forks
            forks = 0
            fork_links = article.find_all("a", href=re.compile(r"/forks"))
            if fork_links:
                fork_text = fork_links[0].get_text(strip=True).replace(",", "")
                try:
                    forks = int(fork_text)
                except:
                    pass

            # Extract stars today/this week/this month
            stars_today = 0
            stars_span = article.find("span", class_="d-inline-block float-sm-right")
            if stars_span:
                stars_text = stars_span.get_text(strip=True)
                # Extract number from text like "1,234 stars today"
                match = re.search(r"([\d,]+)\s+stars", stars_text)
                if match:
                    try:
                        stars_today = int(match.group(1).replace(",", ""))
                    except:
                        pass

            # Extract built by (contributors)
            built_by = []
            built_by_span = article.find("span", class_="d-inline-block mr-3")
            if built_by_span:
                contributor_links = built_by_span.find_all("a")
                for link in contributor_links:
                    img = link.find("img")
                    if img and img.get("alt"):
                        built_by.append(img.get("alt").replace("@", ""))

            repo_info = {
                "repo_name": full_name,
                "owner": owner,
                "name": repo_name,
                "description": description,
                "language": language_name,
                "stars": stars,
                "stars_today": stars_today,
                "forks": forks,
                "repo_url": repo_url,
                "built_by": built_by[:5],  # Limit to top 5 contributors
            }
            repos.append(repo_info)

        except Exception as e:
            print(f"Error parsing repo: {e}")
            continue

    return repos


def search_rising_repos(created_within_days: int = 14, min_stars: int = 100, max_results: int = 30) -> list:
    """
    Search recently created repos with fast star growth via the GitHub search API.

    Complements the trending page: a repo can only be "newly created" once, so
    this pool is naturally free of day-over-day repeats.

    Returns repos in the same shape as get_trending_repos, with an extra
    ``is_supplement`` flag.
    """
    from datetime import date, timedelta

    created_after = (date.today() - timedelta(days=created_within_days)).isoformat()
    url = "https://api.github.com/search/repositories"
    params = {
        "q": f"created:>={created_after} stars:>{min_stars}",
        "sort": "stars",
        "order": "desc",
        "per_page": max_results,
    }
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "ideer-daily-briefing",
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
    except Exception as e:
        print(f"Failed to search rising repos: {e}")
        return []

    repos = []
    for item in response.json().get("items", []):
        owner_login = (item.get("owner") or {}).get("login", "")
        repos.append({
            "repo_name": item["full_name"],
            "owner": owner_login,
            "name": item.get("name", ""),
            "description": item.get("description") or "",
            "language": item.get("language") or "",
            "stars": item.get("stargazers_count", 0),
            "stars_today": 0,
            "forks": item.get("forks_count", 0),
            "repo_url": item["html_url"],
            "built_by": [],
            "is_supplement": True,
        })
    return repos
    """
    Fetch GitHub Trending developers.

    Args:
        language: Programming language filter
        since: Time range (daily, weekly, monthly)
        max_results: Maximum number of developers to return

    Returns:
        List[Dict]: Developers with username, full_name, avatar_url, repo_name, repo_description
    """
    if language and language.lower() != "all":
        url = f"https://github.com/trending/developers/{language.lower()}?since={since}"
    else:
        url = f"https://github.com/trending/developers?since={since}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
    except Exception as e:
        print(f"Failed to fetch GitHub trending developers: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    developers = []

    dev_articles = soup.find_all("article", class_="Box-row")

    for article in dev_articles[:max_results]:
        try:
            # Extract username
            username_link = article.find("h1", class_="h3")
            if not username_link:
                continue
            username_a = username_link.find("a")
            if not username_a:
                continue
            username = username_a.get("href", "").strip("/")

            # Extract full name
            full_name_p = article.find("p", class_="f4")
            full_name = full_name_p.get_text(strip=True) if full_name_p else username

            # Extract avatar
            avatar_img = article.find("img", class_="avatar")
            avatar_url = avatar_img.get("src", "") if avatar_img else ""

            # Extract featured repo
            repo_article = article.find("article")
            repo_name = ""
            repo_description = ""
            if repo_article:
                repo_link = repo_article.find("a")
                if repo_link:
                    repo_name = repo_link.get_text(strip=True)
                repo_desc = repo_article.find("div", class_="f6")
                if repo_desc:
                    repo_description = repo_desc.get_text(strip=True)

            developer_info = {
                "username": username,
                "full_name": full_name,
                "avatar_url": avatar_url,
                "repo_name": repo_name,
                "repo_description": repo_description,
                "profile_url": f"https://github.com/{username}",
            }
            developers.append(developer_info)

        except Exception as e:
            continue

    return developers


if __name__ == "__main__":
    # Test trending repos
    print("=== Testing Trending Repos (All Languages) ===")
    repos = get_trending_repos(max_results=5)
    for r in repos:
        print(f"Repo: {r['repo_name']}")
        print(f"Stars: {r['stars']} (+{r['stars_today']} today), Language: {r['language']}")
        print(f"Description: {r['description'][:80]}...")
        print()

    print("=== Testing Trending Repos (Python) ===")
    repos = get_trending_repos(language="python", max_results=5)
    for r in repos:
        print(f"Repo: {r['repo_name']}")
        print(f"Stars: {r['stars']} (+{r['stars_today']} today)")
        print()
