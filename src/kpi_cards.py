import streamlit as st


CARD_CSS = """
<style>
.kpi-row {
    display: flex;
    gap: 16px;
    margin: 8px 0 24px 0;
}

.kpi-card {
    flex: 1;
    background: linear-gradient(135deg, #ffffff 0%, #f8f9fc 100%);
    border: 1px solid #eaeaf2;
    border-radius: 14px;
    padding: 20px 22px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
    transition: transform 0.15s ease, box-shadow 0.15s ease;
    border-top: 3px solid var(--accent, #6366f1);
}

.kpi-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(0, 0, 0, 0.08);
}

.kpi-icon {
    font-size: 22px;
    margin-bottom: 6px;
}

.kpi-label {
    font-size: 13px;
    font-weight: 600;
    color: #6b7280;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin-bottom: 4px;
}

.kpi-value {
    font-size: 28px;
    font-weight: 700;
    color: #111827;
    line-height: 1.2;
}

.kpi-delta {
    font-size: 13px;
    font-weight: 600;
    margin-top: 6px;
    display: inline-block;
}

.kpi-delta.positive {
    color: #16a34a;
}

.kpi-delta.negative {
    color: #dc2626;
}

.kpi-delta.neutral {
    color: #9ca3af;
}
</style>
"""


def _format_delta(delta):
    """Return (text, css_class) for a delta value, or (None, None) if not provided."""
    if delta is None:
        return None, None
    if delta > 0:
        return f"▲ {delta:.1f}%", "positive"
    elif delta < 0:
        return f"▼ {abs(delta):.1f}%", "negative"
    else:
        return "— 0.0%", "neutral"


def render_kpi_cards(cards):
    """
    Render a row of styled KPI cards.

    cards: list of dicts, each with:
        - label (str): e.g. "Total Revenue"
        - value (str): pre-formatted display value, e.g. "$12,345.00"
        - icon (str, optional): an emoji or short symbol
        - accent (str, optional): hex color for the top border, e.g. "#6366f1"
        - delta (float, optional): percent change; omit if not available/reliable
    """
    st.markdown(CARD_CSS, unsafe_allow_html=True)

    cols_html = []
    for card in cards:
        icon = card.get("icon", "")
        accent = card.get("accent", "#6366f1")
        delta_text, delta_class = _format_delta(card.get("delta"))

        delta_html = ""
        if delta_text:
            delta_html = f'<div class="kpi-delta {delta_class}">{delta_text}</div>'

        # NOTE: no leading whitespace on these lines — indentation here
        # gets misread by Streamlit's markdown parser as a code block.
        card_html = (
            f'<div class="kpi-card" style="--accent: {accent};">'
            f'<div class="kpi-icon">{icon}</div>'
            f'<div class="kpi-label">{card["label"]}</div>'
            f'<div class="kpi-value">{card["value"]}</div>'
            f'{delta_html}'
            f'</div>'
        )
        cols_html.append(card_html)

    full_html = '<div class="kpi-row">' + "".join(cols_html) + '</div>'
    st.markdown(full_html, unsafe_allow_html=True)