#!/usr/bin/env python3
import argparse
import datetime
import requests

GITLAB_API = "https://gitlab.com/api/v4"


def fetch_stats(user, token):
    headers = {"PRIVATE-TOKEN": token}
    now = datetime.datetime.utcnow()
    week_ago = now - datetime.timedelta(days=7)
    iso_then = week_ago.isoformat()

    # 1) Commits count to any projects under 'slurm' group
    commits_url = f"{GITLAB_API}/users/{user}/events"
    params = {"after": iso_then, "per_page": 100}
    resp = requests.get(commits_url, headers=headers, params=params)
    resp.raise_for_status()
    events = resp.json()

    commit_count = sum(1 for e in events if e.get('action_name') == 'pushed to')
    mr_approvals = sum(1 for e in events if e.get('target_type') == 'MergeRequest' and e.get('action_name') == 'approved merge request')

    # 2) Total merge requests approved ever in slurm group
    mr_url = f"{GITLAB_API}/groups/slurm/merge_requests"
    mr_params = {"state": "merged", "per_page": 1}
    mr_resp = requests.get(mr_url, headers=headers, params=mr_params)
    mr_resp.raise_for_status()
    total_merged = int(mr_resp.headers.get('X-Total', 0))

    return commit_count, mr_approvals, total_merged


def update_readme(output_path, stats):
    commits, approvals, total_merged = stats
    summary = (f"### 🔧 Recent GitLab Activity (bailee2)\n"
               f"- 📝 {commits} commits this week\n"
               # f"- ✅ {approvals} merge requests approved this week\n"
               f"- 🎉 {total_merged} total approved merge requests to `Slurm` HPC software\n")

    # Read existing README
    with open(output_path, 'r') as f:
        lines = f.readlines()

    # Replace section between markers
    start, end = None, None
    for i, line in enumerate(lines):
        if '<!-- GITLAB_ACTIVITY_START -->' in line:
            start = i
        if '<!-- GITLAB_ACTIVITY_END -->' in line:
            end = i
    if start is None or end is None:
        # Insert at top if markers missing
        lines.insert(0, '<!-- GITLAB_ACTIVITY_END -->\n')
        lines.insert(0, summary)
        lines.insert(0, '<!-- GITLAB_ACTIVITY_START -->\n')
    else:
        # Replace between markers
        lines[start+1:end] = [summary + '\n']

    # Write back
    with open(output_path, 'w') as f:
        f.writelines(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--token', required=True)
    parser.add_argument('--user', required=True)
    parser.add_argument('--output', default='README.md')
    args = parser.parse_args()

    stats = fetch_stats(args.user, args.token)
    update_readme(args.output, stats)


if __name__ == '__main__':
    main()
