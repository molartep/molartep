#!/usr/bin/env python3
"""Render both profile themes; optionally refresh public GitHub stats."""
import argparse
from datetime import datetime, timezone
from html import escape
import json
import os
import subprocess
import tempfile
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
USER = 'molartep'


def api(path):
    headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'molartep-profile'}
    if token := os.environ.get('GITHUB_TOKEN'):
        headers['Authorization'] = f'Bearer {token}'
    with urllib.request.urlopen(urllib.request.Request(f'https://api.github.com/{path}', headers=headers), timeout=30) as response:
        return json.load(response)


def pages(path):
    result = []
    page = 1
    while True:
        batch = api(f'{path}&per_page=100&page={page}')
        result.extend(batch)
        if len(batch) < 100:
            return result
        page += 1


def count_lines(repository, shas):
    """Read full, non-merge text diffs for the selected commit IDs."""
    if not shas:
        return 0, 0
    with tempfile.TemporaryDirectory(prefix='profile-history-') as temporary:
        checkout = Path(temporary) / 'history.git'
        subprocess.run(['git', 'clone', '--bare', '--single-branch', '--branch',
                        repository['default_branch'], repository['clone_url'], str(checkout)],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        log = subprocess.run(['git', '-C', str(checkout), 'log', '--no-walk', '--stdin',
                              '--format=', '--numstat', '--no-renames', '--no-merges'],
                             input='\n'.join(sorted(shas)) + '\n', text=True,
                             check=True, capture_output=True).stdout
    added = deleted = 0
    for line in log.splitlines():
        fields = line.split('\t', 2)
        if len(fields) == 3 and fields[0].isdigit() and fields[1].isdigit():
            added += int(fields[0])
            deleted += int(fields[1])
    return added, deleted


def fetch_stats():
    repos = pages(f'users/{USER}/repos?type=owner')
    seen = set()
    added = deleted = 0
    for repo in repos:
        if repo['fork']:
            continue
        # GitHub resolves the account's linked author identities; do not guess names/emails.
        commits = pages(f"repos/{USER}/{repo['name']}/commits?author={USER}&sha={repo['default_branch']}")
        shas = {commit['sha'] for commit in commits} - seen
        plus, minus = count_lines(repo, shas)
        added += plus
        deleted += minus
        seen.update(shas)
    return {
        'public_repos': len(repos),
        'commits': len(seen),
        'added': added,
        'deleted': deleted,
        'lines_of_code': added - deleted,
        'scope': 'Account-authored commits on default branches of owned public non-fork repositories; unique SHAs; non-merge text diffs; binary files excluded.',
        'updated': datetime.now(timezone.utc).strftime('%Y-%m-%d'),
    }


def render(theme, stats):
    dark = theme == 'dark'
    bg, panel, fg, muted, key, value = (
        ('#0d1117', '#161b22', '#e6edf3', '#8b949e', '#ffa657', '#a5d6ff') if dark else
        ('#ffffff', '#f6f8fa', '#24292f', '#57606a', '#953800', '#0a3069')
    )
    parts = [f'''<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="700" viewBox="0 0 1100 700" role="img" aria-labelledby="title desc">
<title id="title">Martin Olarte | AI, data and automation</title>
<desc id="desc">ASCII portrait converted from Martin's own headshot. AI Solutions Engineer focused on Deterministic AI, data and automation. Featured work: Resume Lens, Colombia Company Intelligence, and AI Engineering Interview Prep. Public GitHub stats updated {escape(stats['updated'])}.</desc>
<rect width="1100" height="700" rx="18" fill="{bg}"/>
<rect x="16" y="16" width="1068" height="668" rx="12" fill="{panel}"/>
<g font-family="Menlo,Consolas,DejaVu Sans Mono,monospace" font-size="15" fill="{fg}">
<text x="478" y="49" fill="{value}">molartep@github</text>
<path d="M454 72V648" stroke="{muted}" opacity=".3"/>
''']
    lines = (ROOT / 'assets/portrait.txt').read_text().splitlines()
    colors = json.loads((ROOT / 'assets/portrait.json').read_text())['colors']
    parts.append('<g font-size="10" xml:space="preserve">')
    for y, line in enumerate(lines):
        parts.append(f'<text x="32" y="{85+y*9.4:.1f}">')
        for x, char in enumerate(line):
            if char == ' ':
                continue
            rgb = tuple(int(colors[y][x][i:i+2], 16) for i in (1,3,5))
            # Lift dark hair/suit on the dark canvas, retaining photographic hues.
            if dark:
                rgb = tuple(round(78 + c * .69) for c in rgb)
            else:
                rgb = tuple(round(c * .70) for c in rgb)
            color = '#%02x%02x%02x' % rgb
            parts.append(f'<tspan x="{32+x*6:.1f}" fill="{color}">{escape(char)}</tspan>')
        parts.append('</text>')
    parts.append('</g>')

    def text(x, y, content, color=fg, size=15):
        parts.append(f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}">{escape(content)}</text>')

    # Monospace dot leaders fill the space between each label and right-aligned value.
    columns, char_width, left = 70, 8.4, 478

    def row(y, label, content, segments=None, href=None):
        if href:
            parts.append(f'<a href="{escape(href, quote=True)}">')
        dots = '.' * max(2, columns - len(label) - len(content) - 2)
        text(left, y, label, key, 14)
        text(left + (len(label) + 1) * char_width, y, dots, muted, 14)
        x = left + (columns - len(content)) * char_width
        if segments:
            for part, color in segments:
                text(x, y, part, color, 14)
                x += len(part) * char_width
        else:
            text(x, y, content, value, 14)
        if href:
            parts.append('</a>')

    def section(y, title):
        text(left, y, title, muted, 14)

    text(32, 646, 'MARTIN OLARTE', fg, 17)
    text(32, 668, 'AI / DATA / AUTOMATION', muted, 12)
    text(478, 91, 'Martin Olarte', fg, 25)
    row(130, 'Role', 'AI Solutions Engineer')
    row(157, 'Focus', 'Deterministic AI, data, automation')
    row(184, 'Languages', 'Python, TypeScript, R, SQL, C#')
    row(211, 'Stack', 'React, Express, SQLite')
    row(238, 'Human', 'Spanish / English · Colombia')
    text(478, 277, '$ ls featured/', muted, 14)
    text(478, 307, '01  Resume Lens', key)
    text(514, 330, 'Beyond ATS: decision models for resume review.', value, 14)
    text(478, 361, '02  Colombia Company Intelligence', key)
    text(514, 384, 'A central hub for Colombian company research.', value, 14)
    text(478, 415, '03  AI Engineering Interview Prep', key)
    text(514, 438, 'Local-first study, practice and review.', value, 14)
    section(476, '$ cat contact')
    row(503, 'Email', 'molartep@gmail.com', href='mailto:molartep@gmail.com')
    row(530, 'LinkedIn', 'in/martin-olarte-pallares', href='https://www.linkedin.com/in/martin-olarte-pallares/')
    section(568, '$ github --public-stats')
    row(595, 'Repos', f"{stats['public_repos']:,}")
    row(622, 'Commits', f"{stats['commits']:,}")
    segments = [(f"{stats['lines_of_code']:,} (", value),
                (f"{stats['added']:,}++", '#3fb950' if dark else '#116329'),
                (' / ', muted),
                (f"{stats['deleted']:,}--", '#f85149' if dark else '#cf222e'), (')', value)]
    row(649, 'Lines of Code on GitHub', ''.join(part for part, _ in segments), segments=segments)
    text(478, 674, f"Updated {stats['updated']} UTC · links below", muted, 12)
    parts.append('</g></svg>\n')
    return ''.join(parts)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--refresh', action='store_true', help='Fetch public GitHub stats before rendering')
    args = parser.parse_args()
    stats_path = ROOT / 'assets/stats.json'
    # Complete all requests before replacing the last successful snapshot.
    stats = fetch_stats() if args.refresh else json.loads(stats_path.read_text())
    outputs = {theme: render(theme, stats) for theme in ('dark', 'light')}
    if args.refresh:
        stats_path.write_text(json.dumps(stats, indent=2) + '\n')
    for theme, svg in outputs.items():
        (ROOT / f'{theme}_mode.svg').write_text(svg)


if __name__ == '__main__':
    main()
