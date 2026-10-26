# insurancecareershub.com: static job search site
- Data: refresh_jobs.py scrapes https://staffmyagency.com/Main/JobSearch?Page=1..N, the same source Job Content Studio uses, and writes jobs.json. It applies the same exclusion as gen26.py (agency contains "Jantz" or city is Edmond, OK). If it finds fewer than 50 jobs it aborts and keeps the old file.
- Daily: /workspace/ich-site/refresh.sh (add a deploy push once a host is logged in)
- Local test: cd /workspace/ich-site && python3 -m http.server 8765
- Deploy (GitHub Pages, after `gh auth login`): gh repo create insurancecareershub --public --source=. --push ; enable Pages from main / root ; the CNAME file is already present.
- GoDaddy DNS for GitHub Pages: A @ 185.199.108.153 / .109.153 / .110.153 / .111.153 ; CNAME www -> <github-user>.github.io ; then tick Enforce HTTPS in Pages settings.
