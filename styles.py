"""
Unified design system: all CSS, typography, animations, and layout tokens
for the entire multi-page application.

Palette: Muted obsidian, warm graphite, soft ivory typography.
No neon. No bright glare. No saturated accents.
"""


def inject_global_styles():
    """Returns the full CSS stylesheet as a string for st.markdown injection."""
    return """
<style>
    /* ─── Web Fonts ───────────────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;1,6..72,400&family=JetBrains+Mono:wght@400;500&display=swap');

    /* ─── Design Tokens (CSS Variables) ───────────────────────── */
    :root {
        --bg-root:        #0A0D12;
        --bg-surface:     #11151E;
        --bg-raised:      #171C28;
        --bg-hover:       #1D2335;
        --border-faint:   rgba(255, 255, 255, 0.055);
        --border-subtle:  rgba(255, 255, 255, 0.09);
        --border-hover:   rgba(255, 255, 255, 0.16);
        --text-primary:   #F0F2F5;
        --text-secondary: #A0AABB;
        --text-tertiary:  #6B7688;
        --text-muted:     #4A5568;
        --accent-warm:    #BFA07A;       /* Muted gold / warm sand */
        --accent-sage:    #7A9E87;       /* Muted sage green */
        --accent-steel:   #8494A7;       /* Muted steel */
        --accent-clay:    #B0846A;       /* Muted terracotta */
        --radius-sm:      6px;
        --radius-md:      10px;
        --radius-lg:      14px;
        --radius-pill:    9999px;
        --shadow-card:    0 2px 12px rgba(0, 0, 0, 0.25);
        --shadow-hover:   0 6px 24px rgba(0, 0, 0, 0.35);
        --ease-out-expo:  cubic-bezier(0.16, 1, 0.3, 1);
        --font-sans:      'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        --font-serif:     'Newsreader', Georgia, 'Times New Roman', serif;
        --font-mono:      'JetBrains Mono', 'Fira Code', monospace;
    }

    /* ─── Global Reset ────────────────────────────────────────── */
    .stApp {
        background-color: var(--bg-root) !important;
        color: var(--text-primary);
        font-family: var(--font-sans);
    }
    section[data-testid="stSidebar"] {
        background-color: #0C1018 !important;
        border-right: 1px solid var(--border-faint) !important;
    }
    section[data-testid="stSidebar"] * {
        font-family: var(--font-sans) !important;
    }

    /* ─── Keyframe Animations ─────────────────────────────────── */
    @keyframes fadeSlideUp {
        from { opacity: 0; transform: translateY(10px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    @keyframes fadeIn {
        from { opacity: 0; }
        to   { opacity: 1; }
    }
    @keyframes subtleShimmer {
        0%   { background-position: 0% 50%; }
        50%  { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    @keyframes pulse {
        0%   { box-shadow: 0 0 0 0 rgba(122, 158, 135, 0.45); }
        70%  { box-shadow: 0 0 0 7px rgba(122, 158, 135, 0); }
        100% { box-shadow: 0 0 0 0 rgba(122, 158, 135, 0); }
    }
    @keyframes marquee {
        0%   { transform: translateX(0); }
        100% { transform: translateX(-50%); }
    }
    @keyframes countUp {
        from { opacity: 0; transform: translateY(5px); }
        to   { opacity: 1; transform: translateY(0); }
    }

    /* ─── Navigation Page Links ───────────────────────────────── */
    [data-testid="stSidebarNav"] a {
        color: var(--text-secondary) !important;
        font-weight: 500 !important;
        border-radius: var(--radius-sm) !important;
        transition: all 0.15s ease !important;
    }
    [data-testid="stSidebarNav"] a:hover {
        color: var(--text-primary) !important;
        background: rgba(255,255,255,0.04) !important;
    }

    /* ─── Wire Ticker ─────────────────────────────────────────── */
    .wire-ticker-wrap {
        width: 100%;
        overflow: hidden;
        background: var(--bg-surface);
        border-bottom: 1px solid var(--border-faint);
        padding: 9px 0;
        margin-bottom: 0;
    }
    .wire-ticker-track {
        display: flex;
        white-space: nowrap;
        animation: marquee 90s linear infinite;
        will-change: transform;
    }
    .wire-ticker-track:hover {
        animation-play-state: paused;
    }
    .wire-ticker-item {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 0 28px;
        font-size: 0.78rem;
        font-weight: 500;
        color: var(--text-secondary);
    }
    .wire-ticker-item a {
        color: var(--text-secondary);
        text-decoration: none;
        transition: color 0.15s ease;
    }
    .wire-ticker-item a:hover {
        color: var(--text-primary);
    }
    .wire-ticker-src {
        font-size: 0.65rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: var(--text-muted);
        padding: 1px 6px;
        background: rgba(255,255,255,0.04);
        border-radius: 3px;
    }
    .wire-ticker-dot {
        width: 3px;
        height: 3px;
        border-radius: 50%;
        background: var(--text-muted);
        flex-shrink: 0;
    }

    /* ─── Hero Area ───────────────────────────────────────────── */
    .hero-wrap {
        padding: 2.5rem 0 2rem 0;
        border-bottom: 1px solid var(--border-faint);
        margin-bottom: 2rem;
        animation: fadeSlideUp 0.5s var(--ease-out-expo);
    }
    .hero-eyebrow {
        display: inline-flex;
        align-items: center;
        gap: 7px;
        padding: 4px 14px;
        border-radius: var(--radius-pill);
        background: rgba(255,255,255,0.03);
        border: 1px solid var(--border-subtle);
        font-size: 0.7rem;
        font-weight: 600;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--text-tertiary);
        margin-bottom: 1.1rem;
    }
    .hero-pulse {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background-color: var(--accent-sage);
        animation: pulse 2.5s infinite;
    }
    .hero-title {
        font-family: var(--font-serif);
        font-size: 3rem;
        font-weight: 500;
        letter-spacing: -0.025em;
        color: var(--text-primary);
        margin: 0 0 0.65rem 0;
        line-height: 1.1;
    }
    .hero-subtitle {
        font-size: 1.05rem;
        color: var(--text-secondary);
        line-height: 1.6;
        max-width: 700px;
        margin: 0;
        font-weight: 400;
    }

    /* ─── Section Labels ──────────────────────────────────────── */
    .section-label {
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: var(--text-muted);
        margin-bottom: 14px;
        padding-bottom: 8px;
        border-bottom: 1px solid var(--border-faint);
    }

    /* ─── Stat Cards ──────────────────────────────────────────── */
    .stat-row {
        display: flex;
        gap: 14px;
        margin-bottom: 2rem;
        animation: fadeSlideUp 0.4s var(--ease-out-expo) 0.1s both;
    }
    .stat-card {
        flex: 1;
        background: var(--bg-surface);
        border: 1px solid var(--border-faint);
        border-radius: var(--radius-md);
        padding: 18px 20px;
        transition: all 0.2s ease;
    }
    .stat-card:hover {
        border-color: var(--border-hover);
        background: var(--bg-raised);
    }
    .stat-label {
        font-size: 0.68rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--text-muted);
        margin-bottom: 6px;
    }
    .stat-value {
        font-family: var(--font-mono);
        font-size: 1.6rem;
        font-weight: 500;
        color: var(--text-primary);
        line-height: 1;
        animation: countUp 0.4s ease-out;
    }
    .stat-sub {
        font-size: 0.75rem;
        color: var(--text-tertiary);
        margin-top: 5px;
    }

    /* ─── Topic Cluster Cards ─────────────────────────────────── */
    .cluster-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
        gap: 16px;
        margin-bottom: 2rem;
    }
    .cluster-card {
        background: var(--bg-surface);
        border: 1px solid var(--border-faint);
        border-radius: var(--radius-lg);
        padding: 20px 22px;
        transition: all 0.25s var(--ease-out-expo);
        cursor: default;
        position: relative;
        overflow: hidden;
        animation: fadeSlideUp 0.4s var(--ease-out-expo) both;
    }
    .cluster-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: linear-gradient(90deg, var(--accent-warm) 0%, var(--accent-steel) 100%);
        opacity: 0;
        transition: opacity 0.25s ease;
    }
    .cluster-card:hover {
        border-color: var(--border-hover);
        background: var(--bg-raised);
        transform: translateY(-3px);
        box-shadow: var(--shadow-hover);
    }
    .cluster-card:hover::before {
        opacity: 1;
    }
    .cluster-topic {
        font-family: var(--font-serif);
        font-size: 1.15rem;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 8px;
        line-height: 1.3;
    }
    .cluster-meta {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 12px;
    }
    .cluster-count {
        font-family: var(--font-mono);
        font-size: 0.75rem;
        font-weight: 500;
        color: var(--accent-warm);
        padding: 2px 8px;
        background: rgba(191, 160, 122, 0.1);
        border-radius: var(--radius-sm);
        border: 1px solid rgba(191, 160, 122, 0.15);
    }
    .cluster-sources {
        font-size: 0.72rem;
        color: var(--text-tertiary);
    }
    .cluster-headline {
        font-size: 0.84rem;
        color: var(--text-secondary);
        line-height: 1.45;
        border-top: 1px solid var(--border-faint);
        padding-top: 10px;
        margin-top: 4px;
    }
    .cluster-headline a {
        color: var(--text-secondary);
        text-decoration: none;
        transition: color 0.12s ease;
    }
    .cluster-headline a:hover {
        color: var(--text-primary);
    }
    .cluster-kw-list {
        display: flex;
        gap: 5px;
        flex-wrap: wrap;
        margin-bottom: 10px;
    }
    .cluster-kw {
        font-size: 0.68rem;
        font-weight: 500;
        padding: 2px 7px;
        border-radius: 3px;
        background: rgba(255,255,255,0.04);
        color: var(--text-tertiary);
        border: 1px solid var(--border-faint);
    }

    /* ─── Recent Wire Feed ────────────────────────────────────── */
    .wire-item {
        display: flex;
        gap: 16px;
        padding: 14px 0;
        border-bottom: 1px solid var(--border-faint);
        animation: fadeSlideUp 0.35s var(--ease-out-expo) both;
        transition: background 0.15s ease;
    }
    .wire-item:hover {
        background: rgba(255,255,255,0.015);
    }
    .wire-time-col {
        min-width: 56px;
        text-align: right;
        padding-top: 2px;
    }
    .wire-time-val {
        font-family: var(--font-mono);
        font-size: 0.75rem;
        color: var(--text-muted);
        font-weight: 500;
    }
    .wire-time-unit {
        font-size: 0.65rem;
        color: var(--text-muted);
    }
    .wire-body {
        flex: 1;
    }
    .wire-body-title {
        font-size: 0.92rem;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 3px;
        line-height: 1.35;
    }
    .wire-body-title a {
        color: var(--text-primary);
        text-decoration: none;
    }
    .wire-body-title a:hover {
        color: var(--accent-warm);
    }
    .wire-body-source {
        font-size: 0.7rem;
        font-weight: 600;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: var(--text-muted);
    }

    /* ─── Synthesis / Explainer Card ──────────────────────────── */
    .synthesis-card {
        background: var(--bg-surface);
        border: 1px solid var(--border-faint);
        border-radius: var(--radius-lg);
        padding: 28px 30px;
        margin-top: 1rem;
        box-shadow: var(--shadow-card);
        animation: fadeSlideUp 0.4s var(--ease-out-expo);
    }
    .synthesis-card h3 {
        font-family: var(--font-serif);
        color: var(--text-primary);
        font-size: 1.2rem;
        font-weight: 600;
        margin-top: 1.8rem;
        margin-bottom: 0.7rem;
        padding-bottom: 0.4rem;
        border-bottom: 1px solid var(--border-faint);
    }
    .synthesis-card h3:first-child { margin-top: 0; }
    .synthesis-card p, .synthesis-card li {
        color: var(--text-secondary);
        line-height: 1.7;
        font-size: 0.93rem;
    }
    .synthesis-card strong { color: var(--text-primary); }

    /* ─── Dossier Source Cards ─────────────────────────────────── */
    .dossier-card {
        background: var(--bg-surface);
        border: 1px solid var(--border-faint);
        border-radius: var(--radius-md);
        padding: 18px 20px;
        margin-bottom: 14px;
        transition: all 0.2s ease;
        animation: fadeSlideUp 0.3s var(--ease-out-expo) both;
    }
    .dossier-card:hover {
        background: var(--bg-raised);
        border-color: var(--border-hover);
        transform: translateY(-2px);
        box-shadow: var(--shadow-hover);
    }
    .dossier-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
    }
    .source-tag {
        font-size: 0.68rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        padding: 3px 8px;
        border-radius: 4px;
        background: rgba(255,255,255,0.04);
        color: var(--text-tertiary);
        border: 1px solid var(--border-faint);
    }
    .time-tag {
        font-size: 0.75rem;
        color: var(--text-muted);
        font-weight: 500;
    }
    .dossier-title {
        font-size: 1rem;
        font-weight: 600;
        color: var(--text-primary);
        margin: 4px 0 8px 0;
        line-height: 1.35;
    }
    .dossier-title a {
        color: var(--text-primary);
        text-decoration: none;
        transition: color 0.12s ease;
    }
    .dossier-title a:hover { color: var(--accent-warm); }
    .dossier-text {
        font-size: 0.86rem;
        color: var(--text-secondary);
        line-height: 1.6;
        background: rgba(0,0,0,0.18);
        padding: 12px 16px;
        border-radius: var(--radius-sm);
        border-left: 2px solid var(--border-subtle);
        margin-top: 10px;
    }
    .match-bar-bg {
        width: 100%;
        height: 3px;
        background: rgba(255,255,255,0.04);
        border-radius: 2px;
        overflow: hidden;
        margin-top: 10px;
    }
    .match-bar-fill {
        height: 100%;
        background: linear-gradient(90deg, var(--accent-steel), var(--accent-warm));
        border-radius: 2px;
        transition: width 0.5s var(--ease-out-expo);
    }

    /* ─── Timeline ────────────────────────────────────────────── */
    .timeline-wrap {
        position: relative;
        padding: 12px 0 24px 24px;
        margin: 16px 0 24px 12px;
    }
    .timeline-wrap::before {
        content: '';
        position: absolute;
        left: 0;
        top: 0;
        bottom: 0;
        width: 1px;
        background: linear-gradient(to bottom, var(--border-subtle), transparent);
    }
    .timeline-node {
        position: relative;
        margin-bottom: 28px;
        animation: fadeSlideUp 0.35s var(--ease-out-expo) both;
    }
    .timeline-node:last-child { margin-bottom: 0; }
    .timeline-dot {
        position: absolute;
        left: -28.5px;
        top: 4px;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: var(--text-muted);
        border: 2px solid var(--bg-root);
        transition: background 0.15s ease;
    }
    .timeline-node:hover .timeline-dot {
        background: var(--accent-warm);
    }
    .timeline-date {
        font-family: var(--font-mono);
        font-size: 0.7rem;
        font-weight: 500;
        color: var(--text-muted);
        letter-spacing: 0.04em;
        margin-bottom: 3px;
    }
    .timeline-headline {
        font-size: 0.95rem;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 4px;
        line-height: 1.35;
    }
    .timeline-body {
        font-size: 0.84rem;
        color: var(--text-secondary);
        line-height: 1.55;
    }
    .timeline-body a {
        color: var(--text-tertiary);
        text-decoration: none;
        transition: color 0.12s ease;
    }
    .timeline-body a:hover { color: var(--text-primary); }

    /* ─── Sidebar Metric Box ──────────────────────────────────── */
    .metric-box {
        background: rgba(255,255,255,0.025);
        border: 1px solid var(--border-faint);
        border-radius: var(--radius-md);
        padding: 14px 16px;
        margin: 10px 0;
    }

    /* ─── Input Field ─────────────────────────────────────────── */
    .stTextInput input {
        background-color: var(--bg-surface) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: var(--radius-md) !important;
        padding: 13px 18px !important;
        font-size: 1rem !important;
        font-family: var(--font-sans) !important;
        transition: border-color 0.2s ease !important;
    }
    .stTextInput input:focus {
        border-color: var(--accent-steel) !important;
        box-shadow: 0 0 0 1px rgba(132,148,167,0.2) !important;
    }
    .stTextInput input::placeholder {
        color: var(--text-muted) !important;
    }

    /* ─── Example Pill Buttons ────────────────────────────────── */
    div[data-testid="column"] button {
        background-color: var(--bg-surface) !important;
        color: var(--text-secondary) !important;
        border: 1px solid var(--border-faint) !important;
        border-radius: var(--radius-sm) !important;
        padding: 0.55rem 0.9rem !important;
        font-size: 0.82rem !important;
        font-weight: 400 !important;
        font-family: var(--font-sans) !important;
        text-align: left !important;
        transition: all 0.2s var(--ease-out-expo) !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.15) !important;
    }
    div[data-testid="column"] button:hover {
        background-color: var(--bg-raised) !important;
        border-color: var(--border-hover) !important;
        color: var(--text-primary) !important;
        transform: translateY(-2px);
        box-shadow: var(--shadow-hover) !important;
    }

    /* ─── Tabs ────────────────────────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0px;
        border-bottom: 1px solid var(--border-faint);
    }
    .stTabs [data-baseweb="tab"] {
        font-family: var(--font-sans) !important;
        font-size: 0.85rem !important;
        font-weight: 500 !important;
        color: var(--text-tertiary) !important;
        padding: 10px 20px !important;
        transition: color 0.15s ease !important;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: var(--text-primary) !important;
    }
    .stTabs [aria-selected="true"] {
        color: var(--text-primary) !important;
    }

    /* ─── Stagger Animation Delays ────────────────────────────── */
    .stagger-1 { animation-delay: 0.05s; }
    .stagger-2 { animation-delay: 0.10s; }
    .stagger-3 { animation-delay: 0.15s; }
    .stagger-4 { animation-delay: 0.20s; }
    .stagger-5 { animation-delay: 0.25s; }
    .stagger-6 { animation-delay: 0.30s; }
</style>
"""
