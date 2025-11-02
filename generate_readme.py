#!/usr/bin/env python3
import json
import subprocess
import os
from collections import OrderedDict

TOKEN = os.environ.get("GITHUB_TOKEN")
USERNAME = os.environ.get("GITHUB_USER", "emmahyde")

def fetch_all_starred():
    """Fetch all starred repos with pagination"""
    all_repos = []
    after = None
    page = 0

    while True:
        page += 1
        after_var = f', after: "{after}"' if after else ''

        query = {
            "query": f"""
                query {{
                    user(login: "{USERNAME}") {{
                        starredRepositories(first: 100{after_var}, orderBy: {{direction: DESC, field: STARRED_AT}}) {{
                            totalCount
                            nodes {{
                                nameWithOwner
                                description
                                url
                                isPrivate
                                languages(first: 1, orderBy: {{field: SIZE, direction: DESC}}) {{
                                    edges {{
                                        node {{
                                            name
                                        }}
                                    }}
                                }}
                            }}
                            pageInfo {{
                                endCursor
                                hasNextPage
                            }}
                        }}
                    }}
                }}
            """
        }

        result = subprocess.run(
            ['curl', '-s', '-H', f'Authorization: Bearer {TOKEN}', '-H', 'Content-Type: application/json', '-X', 'POST', '--data', json.dumps(query), 'https://api.github.com/graphql'],
            capture_output=True,
            text=True
        )

        try:
            data = json.loads(result.stdout)
            if 'errors' in data:
                print(f"Error on page {page}: {data['errors']}")
                break

            repos = data['data']['user']['starredRepositories']['nodes']
            all_repos.extend(repos)
            print(f"Page {page}: {len(repos)} repos (total: {len(all_repos)})")

            if not data['data']['user']['starredRepositories']['pageInfo']['hasNextPage']:
                break

            after = data['data']['user']['starredRepositories']['pageInfo']['endCursor']
        except Exception as e:
            print(f"Error parsing page {page}: {e}")
            break

    return all_repos

def main():
    if not TOKEN:
        print("Error: GITHUB_TOKEN environment variable not set")
        return

    print("Fetching starred repositories...")
    repos = fetch_all_starred()
    print(f"\nTotal: {len(repos)} repos\n")

    # Organize by language
    by_lang = {}
    for repo in repos:
        if repo['isPrivate']:
            continue

        lang = 'Others'
        if repo['languages']['edges']:
            lang = repo['languages']['edges'][0]['node']['name']

        if lang not in by_lang:
            by_lang[lang] = []
        by_lang[lang].append(repo)

    # Sort
    sorted_langs = OrderedDict(sorted(by_lang.items()))

    # Generate README
    lines = [
        "# Awesome Stars [![Awesome](https://awesome.re/badge.svg)](https://github.com/sindresorhus/awesome)",
        "",
        "> A curated list of my GitHub stars!",
        "",
        "## Contents",
        ""
    ]

    for lang in sorted_langs:
        anchor = lang.lower().replace('#', '').replace('+', '').replace(' ', '-').replace('.', '')
        lines.append(f"- [{lang}](#{anchor})")

    lines.append("")

    for lang, repos_list in sorted_langs.items():
        lines.append(f"## {lang}")
        lines.append("")
        for repo in repos_list:
            desc = (repo['description'] or '').replace('\n', ' ').strip()[:150]
            desc = desc.replace('>', '&gt;').replace('<', '&lt;')
            lines.append(f"- [{repo['nameWithOwner']}]({repo['url']}) - {desc}")
        lines.append("")

    lines.extend([
        "## License",
        "",
        "[![CC0](http://mirrors.creativecommons.org/presskit/buttons/88x31/svg/cc-zero.svg)](https://creativecommons.org/publicdomain/zero/1.0/)",
        "",
        f"To the extent possible under law, [{USERNAME}](https://github.com/{USERNAME}) has waived all copyright and related or neighboring rights to this work."
    ])

    with open('README.md', 'w') as f:
        f.write('\n'.join(lines))

    print("✓ README.md generated!")
    print(f"\nStats:")
    for lang in sorted_langs:
        print(f"  {lang}: {len(sorted_langs[lang])}")

if __name__ == '__main__':
    main()
