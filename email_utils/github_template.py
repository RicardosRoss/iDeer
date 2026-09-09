LANGUAGE_COLORS = {
    "python": "#3572A5",
    "javascript": "#f1e05a",
    "typescript": "#2b7489",
    "java": "#b07219",
    "go": "#00ADD8",
    "rust": "#dea584",
    "c++": "#f34b7d",
    "c": "#555555",
    "ruby": "#701516",
    "php": "#4F5D95",
    "swift": "#ffac45",
    "kotlin": "#F18E33",
    "scala": "#c22d40",
    "shell": "#89e051",
    "html": "#e34c26",
    "css": "#563d7c",
    "vue": "#41b883",
    "jupyter notebook": "#DA5B0B",
}


def get_language_badge(language: str) -> str:
    if not language:
        return ""
    color = LANGUAGE_COLORS.get(language.lower(), "#6e7681")
    return f'<span class="lang-badge" style="background-color: {color}; color: white;">{language}</span>'


def get_repo_block_html(title: str, rate: str, repo_name: str, summary: str, repo_url: str,
                        stars: int = 0, stars_today: int = 0, forks: int = 0, language: str = "",
                        star_growth_pct=None):
    lang_badge = get_language_badge(language)
    growth_badge = ""
    if star_growth_pct:
        growth_badge = (
            f'<span class="lang-badge" style="background-color: #1a7f37; color: white;">'
            f'📈 +{star_growth_pct}% since last shown</span>'
        )

    if stars >= 1000:
        stars_str = f"{stars/1000:.1f}k"
    else:
        stars_str = str(stars)

    block_template = """
    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="font-family: Arial, sans-serif; border: 1px solid #d0d7de; border-radius: 8px; padding: 16px; background-color: #f6f8fa;">
    <tr>
        <td style="font-size: 20px; font-weight: bold; color: #24292f;">
            {title} {lang_badge} {growth_badge}
        </td>
    </tr>
    <tr>
        <td style="font-size: 14px; color: #333; padding: 8px 0;">
            <strong>Relevance:</strong> {rate}
        </td>
    </tr>
    <tr>
        <td style="font-size: 14px; color: #57606a; padding: 8px 0;">
            ⭐ {stars_str} stars (+{stars_today} today) &nbsp;|&nbsp; 🍴 {forks} forks
        </td>
    </tr>
    <tr>
        <td style="font-size: 14px; color: #333; padding: 8px 0;">
            <strong>Summary:</strong> {summary}
        </td>
    </tr>
    <tr>
        <td style="padding: 8px 0;">
            <a href="{repo_url}" style="display: inline-block; text-decoration: none; font-size: 14px; font-weight: bold; color: #fff; background-color: #238636; padding: 8px 16px; border-radius: 6px;">View Repo</a>
        </td>
    </tr>
</table>
"""
    return block_template.format(
        title=title, rate=rate, repo_name=repo_name, summary=summary, repo_url=repo_url,
        stars_str=stars_str, stars_today=stars_today, forks=forks, lang_badge=lang_badge,
        growth_badge=growth_badge
    )
