# public

将 get_issues, get_forks 替换为下面的函数，再跑一下

```
ISSUE_CACHE = {}

def get_issues(repo):
    """
    get all issues of a repo sorted by created
    """
    issues = ISSUE_CACHE.get(repo)
    if issues is None:
        repository = g.get_repo(repo)
        issues = []
        for issue in repository.get_issues(state='all', since=since_date, sort='created'):
            issues.append(issue)

        ISSUE_CACHE[repo] = issues
    
    return issues


def get_forks(repo):
    """
    get forks of a repo
    """
    repository = g.get_repo(repo)
    forks = []
    for fork in repository.get_forks():
        forks.append(fork)
    return forks
```
