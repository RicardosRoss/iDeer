import html

from email_utils.base_template import framework


def _escape(text) -> str:
    return html.escape(str(text or ""), quote=True)


def get_idea_card_html(idea: dict, index: int, date: str) -> str:
    """Render a single research idea as an HTML card."""
    title = _escape(idea.get("title", "Untitled"))
    hypothesis = _escape(idea.get("hypothesis", ""))
    research_direction = _escape(idea.get("research_direction", ""))
    project = _escape(idea.get("connects_to_project", "N/A"))
    area = _escape(idea.get("interest_area", ""))
    novelty = _escape(idea.get("novelty_estimate", "UNKNOWN"))
    feasibility = _escape(idea.get("feasibility", "UNKNOWN"))
    composite_score = idea.get("composite_score", 0)
    min_experiment = _escape(idea.get("min_experiment", ""))
    command = f"/idea-from-daily {date} --idea {index}"

    # Inspired-by sources
    inspired_by = idea.get("inspired_by", [])
    sources_html = ""
    for src in inspired_by:
        src_title = _escape(src.get("title", ""))
        src_url = _escape(src.get("url", ""))
        src_source = str(src.get("source", ""))
        badge_color = {"github": "#24292e", "huggingface": "#ff6f00", "twitter": "#1d9bf0"}.get(src_source, "#666")
        sources_html += f'''
        <div style="margin: 4px 0;">
            <span style="display:inline-block;padding:1px 6px;border-radius:8px;
                         background:{badge_color};color:#fff;font-size:11px;margin-right:6px;">{_escape(src_source)}</span>
            <a href="{src_url}" style="color:#1a73e8;text-decoration:none;font-size:13px;">{src_title}</a>
        </div>'''

    # Novelty / feasibility badge colors
    level_colors = {"HIGH": "#16a34a", "MEDIUM": "#d97706", "LOW": "#dc2626", "UNKNOWN": "#6b7280"}
    novelty_color = level_colors.get(novelty, "#6b7280")
    feasibility_color = level_colors.get(feasibility, "#6b7280")

    return f'''
    <table border="0" cellpadding="0" cellspacing="0" width="100%"
           style="font-family:'Helvetica Neue',Arial,sans-serif;border:1px solid #e5e7eb;
                  border-radius:12px;padding:20px;background-color:#fefce8;margin-bottom:16px;
                  border-left:4px solid #8b5cf6;">
    <tr>
      <td>
        <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;">
          <div style="font-size:18px;font-weight:700;color:#1f2937;">
            💡 Idea #{index}: {title}
          </div>
          <div style="font-size:14px;color:#6b7280;">
            Score: <strong style="color:#7c3aed;">{composite_score}</strong>/10
          </div>
        </div>

        <div style="margin:10px 0 8px 0;">
          <span style="display:inline-block;padding:2px 8px;border-radius:10px;
                       background:rgba(139,92,246,0.12);color:#7c3aed;font-size:12px;
                       font-weight:600;margin-right:6px;">📂 {area}</span>
          <span style="display:inline-block;padding:2px 8px;border-radius:10px;
                       background:rgba(139,92,246,0.08);color:#6b7280;font-size:12px;
                       margin-right:6px;">🔗 {project}</span>
          <span style="display:inline-block;padding:2px 8px;border-radius:10px;
                       background:{novelty_color}20;color:{novelty_color};font-size:12px;
                       font-weight:600;margin-right:6px;">Novelty: {novelty}</span>
          <span style="display:inline-block;padding:2px 8px;border-radius:10px;
                       background:{feasibility_color}20;color:{feasibility_color};font-size:12px;
                       font-weight:600;">Feasibility: {feasibility}</span>
        </div>

        <div style="margin:12px 0;padding:12px 16px;background:#fff;border-radius:8px;
                    border:1px solid #e5e7eb;">
          <div style="font-size:13px;font-weight:600;color:#374151;margin-bottom:4px;">假设 / Hypothesis</div>
          <div style="font-size:14px;color:#4b5563;line-height:1.6;">{hypothesis}</div>
        </div>

        <div style="margin:8px 0;padding:12px 16px;background:#fff;border-radius:8px;
                    border:1px solid #e5e7eb;">
          <div style="font-size:13px;font-weight:600;color:#374151;margin-bottom:4px;">最小实验 / Min Experiment</div>
          <div style="font-size:14px;color:#4b5563;line-height:1.6;">{min_experiment}</div>
        </div>

        <div style="margin:10px 0 6px 0;">
          <div style="font-size:13px;font-weight:600;color:#374151;margin-bottom:4px;">灵感来源 / Inspired By</div>
          {sources_html}
        </div>

        <div style="margin:12px 0 0 0;padding:10px 14px;background:#f3f0ff;border-radius:8px;
                    border:1px dashed #8b5cf6;">
          <div style="font-size:12px;color:#6b7280;margin-bottom:2px;">Research Direction (for /idea-from-daily)</div>
          <code style="font-size:13px;color:#5b21b6;word-break:break-all;">{research_direction}</code>
        </div>

        <div style="margin:12px 0 0 0;text-align:center;">
          <code style="font-size:12px;color:#7c3aed;background:#f3f0ff;padding:4px 12px;border-radius:6px;">
            {command}
          </code>
        </div>
      </td>
    </tr>
    </table>
    '''


def render_ideas_email(ideas: list[dict], date: str) -> str:
    """Render the complete ideas email HTML."""
    header = f'''
    <div style="font-family:'Helvetica Neue',Arial,sans-serif;margin-bottom:20px;">
      <div class="section-title" style="border-bottom-color:#8b5cf6;color:#5b21b6;">
        🧪 Daily Research Ideas — {date}
      </div>
      <p style="color:#6b7280;font-size:14px;margin:8px 0 16px 0;">
        基于今日高分推荐 × 研究画像自动生成 · 共 {len(ideas)} 个 ideas
      </p>
    </div>
    '''

    cards = []
    for i, idea in enumerate(ideas, 1):
        cards.append(get_idea_card_html(idea, i, date))

    footer = f'''
    <div style="margin-top:24px;padding:16px;background:#f9fafb;border-radius:8px;
                font-family:'Helvetica Neue',Arial,sans-serif;">
      <div style="font-size:13px;color:#6b7280;line-height:1.8;">
        <strong>Next steps:</strong><br>
        1. 选择感兴趣的 idea<br>
        2. 运行 <code>/idea-from-daily {date} --idea N</code> 启动自动研究流程<br>
        3. 选择管线: Quick (/idea-creator) · Full (/idea-discovery) · End-to-end (/research-pipeline)
      </div>
    </div>
    '''

    content = header + "\n".join(cards) + footer
    return framework.replace("__CONTENT__", content)
