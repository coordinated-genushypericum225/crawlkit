"""
GitHub Parser — Extract repo info, README, issues, code from GitHub URLs.

Features:
- Repository metadata (stars, forks, description, topics)
- README content extraction
- Issues and pull requests
- File and directory content
- User and organization profiles
- Repository search/discovery
- No authentication needed for public repos
"""

from __future__ import annotations
import re
import base64
import logging
from typing import Any, Optional
from urllib.parse import urlparse, parse_qs

from ..base import BaseParser

logger = logging.getLogger(__name__)


class GitHubParser(BaseParser):
    name = "github"
    domain = "github.com"
    
    # Base API URL
    API_BASE = "https://api.github.com"
    
    # URL Pattern matching
    URL_PATTERNS = {
        'repo': r'github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$',
        'issues_list': r'github\.com/([^/]+)/([^/]+)/issues/?$',
        'issue': r'github\.com/([^/]+)/([^/]+)/issues/(\d+)',
        'pulls_list': r'github\.com/([^/]+)/([^/]+)/pulls/?$',
        'pull': r'github\.com/([^/]+)/([^/]+)/pull/(\d+)',
        'blob': r'github\.com/([^/]+)/([^/]+)/blob/([^/]+)/(.*)',
        'tree': r'github\.com/([^/]+)/([^/]+)/tree/([^/]+)/?(.*)',
        'releases': r'github\.com/([^/]+)/([^/]+)/releases',
        'user': r'github\.com/([^/]+)/?$',
    }

    def can_handle(self, url: str) -> bool:
        """Check if this parser can handle the given URL."""
        if self.domain not in url.lower():
            return False
        
        # Additional validation: must have at least owner/repo structure
        # Reject bare "github.com/" URLs
        url_type, _ = self._parse_url(url)
        return url_type is not None  # Only handle if pattern matches

    def parse(self, html: str, url: str = "", text: str = "") -> dict[str, Any]:
        """
        Parse GitHub URL — extract content based on URL pattern.
        
        Args:
            html: Not used for GitHub (uses REST API)
            url: GitHub URL
            text: Not used
        """
        if not url:
            return {"error": "No URL provided"}
        
        # Determine URL type and extract relevant parts
        url_type, matches = self._parse_url(url)
        
        if not url_type:
            return {"error": f"Unsupported GitHub URL pattern: {url}"}
        
        # Route to appropriate handler
        handlers = {
            'repo': self._parse_repo,
            'issues_list': self._parse_issues_list,
            'issue': self._parse_issue,
            'pulls_list': self._parse_pulls_list,
            'pull': self._parse_pull,
            'blob': self._parse_file,
            'tree': self._parse_tree,
            'releases': self._parse_releases,
            'user': self._parse_user,
        }
        
        handler = handlers.get(url_type)
        if not handler:
            return {"error": f"No handler for URL type: {url_type}"}
        
        try:
            result = handler(matches)
            result['source'] = 'github'
            result['url'] = url
            return result
        except Exception as e:
            logger.error(f"GitHub parse error for {url}: {e}")
            return {"error": str(e), "url": url}

    def _parse_url(self, url: str) -> tuple[Optional[str], Optional[re.Match]]:
        """Identify URL pattern and extract components."""
        for url_type, pattern in self.URL_PATTERNS.items():
            match = re.search(pattern, url)
            if match:
                return url_type, match
        return None, None

    def _api_request(self, endpoint: str, params: dict = None) -> dict:
        """Make GitHub API request with proper headers."""
        try:
            import httpx
            
            headers = {
                'User-Agent': 'CrawlKit/0.1.0 (https://crawlkit.org)',
                'Accept': 'application/vnd.github+json',
            }
            
            url = f"{self.API_BASE}{endpoint}"
            response = httpx.get(url, headers=headers, params=params or {}, timeout=15)
            
            # Check rate limiting
            remaining = response.headers.get('X-RateLimit-Remaining', '0')
            reset_time = response.headers.get('X-RateLimit-Reset', 'unknown')
            if int(remaining) < 5:
                logger.warning(f"GitHub API rate limit low: {remaining} requests remaining (resets at {reset_time})")
            
            if response.status_code == 404:
                return {"error": f"GitHub repository not found or is private: {endpoint}"}
            
            if response.status_code == 403:
                return {
                    "error": f"GitHub API rate limit exceeded. Resets at {reset_time}. "
                             f"Remaining: {remaining}/60 per hour"
                }
            
            response.raise_for_status()
            data = response.json()
            
            # Debug logging for repo endpoints
            if "/repos/" in endpoint and not endpoint.endswith(("/readme", "/issues", "/pulls", "/contents", "/releases")):
                logger.debug(f"GitHub API response for {endpoint}: stargazers_count={data.get('stargazers_count', 'N/A')}")
            
            return data
            
        except ImportError:
            return {"error": "httpx library not installed"}
        except Exception as e:
            logger.error(f"GitHub API request failed for {endpoint}: {e}")
            return {"error": str(e)}

    def _parse_repo(self, match: re.Match) -> dict[str, Any]:
        """Parse repository main page."""
        owner, repo = match.groups()
        
        # Get repo metadata
        repo_data = self._api_request(f"/repos/{owner}/{repo}")
        if "error" in repo_data:
            return repo_data
        
        # Get README
        readme_data = self._api_request(f"/repos/{owner}/{repo}/readme")
        readme_content = ""
        if "content" in readme_data and not "error" in readme_data:
            readme_content = base64.b64decode(readme_data["content"]).decode('utf-8', errors='ignore')
        
        # Build response
        full_name = f"{owner}/{repo}"
        title = repo_data.get("full_name", full_name)
        
        # Create markdown content
        content_parts = [f"# {title}\n"]
        if repo_data.get("description"):
            content_parts.append(f"{repo_data['description']}\n")
        if readme_content:
            content_parts.append(readme_content)
        
        result = {
            "title": title,
            "content": "\n".join(content_parts),
            "content_type": "repository",
            "structured": {
                "owner": owner,
                "repo": repo,
                "full_name": full_name,
                "description": repo_data.get("description", ""),
                "stars": repo_data.get("stargazers_count", 0),
                "forks": repo_data.get("forks_count", 0),
                "watchers": repo_data.get("watchers_count", 0),
                "open_issues": repo_data.get("open_issues_count", 0),
                "language": repo_data.get("language"),
                "license": repo_data.get("license", {}).get("name") if repo_data.get("license") else None,
                "topics": repo_data.get("topics", []),
                "created_at": repo_data.get("created_at", ""),
                "updated_at": repo_data.get("updated_at", ""),
                "default_branch": repo_data.get("default_branch", "main"),
                "homepage": repo_data.get("homepage"),
                "readme": readme_content,
                "is_fork": repo_data.get("fork", False),
                "is_archived": repo_data.get("archived", False),
                "is_private": repo_data.get("private", False),
            }
        }
        
        return result

    def _parse_issues_list(self, match: re.Match) -> dict[str, Any]:
        """Parse issues list page."""
        owner, repo = match.groups()
        
        # Get issues (GitHub API returns both issues and PRs in /issues endpoint)
        # We filter out PRs by checking for 'pull_request' field
        issues_data = self._api_request(
            f"/repos/{owner}/{repo}/issues",
            params={"state": "open", "per_page": 30}
        )
        
        if "error" in issues_data:
            return issues_data
        
        # Filter out pull requests (they have pull_request field)
        issues = [i for i in issues_data if "pull_request" not in i]
        
        # Build markdown list
        content_parts = [f"# {owner}/{repo} — Open Issues\n"]
        for issue in issues[:30]:
            labels_str = ", ".join([f"`{l['name']}`" for l in issue.get("labels", [])])
            content_parts.append(
                f"## #{issue['number']}: {issue['title']}\n"
                f"**Author:** @{issue['user']['login']} | "
                f"**State:** {issue['state']} | "
                f"**Labels:** {labels_str}\n"
                f"{issue.get('body', '')[:200]}...\n"
            )
        
        result = {
            "title": f"{owner}/{repo} — Open Issues",
            "content": "\n".join(content_parts),
            "content_type": "issues_list",
            "structured": {
                "owner": owner,
                "repo": repo,
                "total_count": len(issues),
                "items": [
                    {
                        "number": i["number"],
                        "title": i["title"],
                        "state": i["state"],
                        "author": i["user"]["login"],
                        "labels": [l["name"] for l in i.get("labels", [])],
                        "created_at": i["created_at"],
                        "updated_at": i["updated_at"],
                        "comments": i.get("comments", 0),
                    }
                    for i in issues[:30]
                ]
            }
        }
        
        return result

    def _parse_issue(self, match: re.Match) -> dict[str, Any]:
        """Parse single issue page."""
        owner, repo, number = match.groups()
        
        # Get issue details
        issue_data = self._api_request(f"/repos/{owner}/{repo}/issues/{number}")
        if "error" in issue_data:
            return issue_data
        
        # Get comments
        comments_data = self._api_request(f"/repos/{owner}/{repo}/issues/{number}/comments")
        comments = []
        if isinstance(comments_data, list):
            comments = [
                {
                    "author": c["user"]["login"],
                    "body": c["body"],
                    "created_at": c["created_at"],
                }
                for c in comments_data
            ]
        
        # Build content
        content_parts = [
            f"# Issue #{number}: {issue_data['title']}\n",
            f"**Author:** @{issue_data['user']['login']}",
            f"**State:** {issue_data['state']}",
            f"**Created:** {issue_data['created_at']}",
            f"**Labels:** {', '.join([l['name'] for l in issue_data.get('labels', [])])}\n",
            issue_data.get("body", ""),
        ]
        
        if comments:
            content_parts.append("\n## Comments\n")
            for c in comments:
                content_parts.append(f"**@{c['author']}** ({c['created_at']}):\n{c['body']}\n")
        
        result = {
            "title": f"Issue #{number}: {issue_data['title']}",
            "content": "\n".join(content_parts),
            "content_type": "issue",
            "structured": {
                "owner": owner,
                "repo": repo,
                "number": int(number),
                "title": issue_data["title"],
                "state": issue_data["state"],
                "author": issue_data["user"]["login"],
                "body": issue_data.get("body", ""),
                "labels": [l["name"] for l in issue_data.get("labels", [])],
                "assignees": [a["login"] for a in issue_data.get("assignees", [])],
                "comments_count": issue_data.get("comments", 0),
                "created_at": issue_data["created_at"],
                "updated_at": issue_data["updated_at"],
                "closed_at": issue_data.get("closed_at"),
                "comments": comments,
            }
        }
        
        return result

    def _parse_pulls_list(self, match: re.Match) -> dict[str, Any]:
        """Parse pull requests list page."""
        owner, repo = match.groups()
        
        # Get PRs
        pulls_data = self._api_request(
            f"/repos/{owner}/{repo}/pulls",
            params={"state": "open", "per_page": 30}
        )
        
        if "error" in pulls_data:
            return pulls_data
        
        # Build markdown list
        content_parts = [f"# {owner}/{repo} — Open Pull Requests\n"]
        for pr in pulls_data[:30]:
            labels_str = ", ".join([f"`{l['name']}`" for l in pr.get("labels", [])])
            content_parts.append(
                f"## #{pr['number']}: {pr['title']}\n"
                f"**Author:** @{pr['user']['login']} | "
                f"**State:** {pr['state']} | "
                f"**Labels:** {labels_str}\n"
                f"{pr.get('body', '')[:200]}...\n"
            )
        
        result = {
            "title": f"{owner}/{repo} — Open Pull Requests",
            "content": "\n".join(content_parts),
            "content_type": "pulls_list",
            "structured": {
                "owner": owner,
                "repo": repo,
                "total_count": len(pulls_data),
                "items": [
                    {
                        "number": pr["number"],
                        "title": pr["title"],
                        "state": pr["state"],
                        "author": pr["user"]["login"],
                        "labels": [l["name"] for l in pr.get("labels", [])],
                        "created_at": pr["created_at"],
                        "updated_at": pr["updated_at"],
                        "draft": pr.get("draft", False),
                    }
                    for pr in pulls_data[:30]
                ]
            }
        }
        
        return result

    def _parse_pull(self, match: re.Match) -> dict[str, Any]:
        """Parse single pull request (treat as issue with PR metadata)."""
        owner, repo, number = match.groups()
        
        # GitHub PRs are also issues, so we can use issue endpoint
        # But we'll also get PR-specific data
        pr_data = self._api_request(f"/repos/{owner}/{repo}/pulls/{number}")
        if "error" in pr_data:
            return pr_data
        
        # Get comments
        comments_data = self._api_request(f"/repos/{owner}/{repo}/issues/{number}/comments")
        comments = []
        if isinstance(comments_data, list):
            comments = [
                {
                    "author": c["user"]["login"],
                    "body": c["body"],
                    "created_at": c["created_at"],
                }
                for c in comments_data
            ]
        
        # Build content
        content_parts = [
            f"# Pull Request #{number}: {pr_data['title']}\n",
            f"**Author:** @{pr_data['user']['login']}",
            f"**State:** {pr_data['state']}",
            f"**Created:** {pr_data['created_at']}",
            f"**Branch:** {pr_data['head']['ref']} → {pr_data['base']['ref']}",
            f"**Mergeable:** {pr_data.get('mergeable', 'Unknown')}\n",
            pr_data.get("body", ""),
        ]
        
        if comments:
            content_parts.append("\n## Comments\n")
            for c in comments:
                content_parts.append(f"**@{c['author']}** ({c['created_at']}):\n{c['body']}\n")
        
        result = {
            "title": f"PR #{number}: {pr_data['title']}",
            "content": "\n".join(content_parts),
            "content_type": "pull_request",
            "structured": {
                "owner": owner,
                "repo": repo,
                "number": int(number),
                "title": pr_data["title"],
                "state": pr_data["state"],
                "author": pr_data["user"]["login"],
                "body": pr_data.get("body", ""),
                "labels": [l["name"] for l in pr_data.get("labels", [])],
                "created_at": pr_data["created_at"],
                "updated_at": pr_data["updated_at"],
                "merged_at": pr_data.get("merged_at"),
                "draft": pr_data.get("draft", False),
                "mergeable": pr_data.get("mergeable"),
                "head_branch": pr_data["head"]["ref"],
                "base_branch": pr_data["base"]["ref"],
                "commits": pr_data.get("commits", 0),
                "additions": pr_data.get("additions", 0),
                "deletions": pr_data.get("deletions", 0),
                "changed_files": pr_data.get("changed_files", 0),
                "comments": comments,
            }
        }
        
        return result

    def _parse_file(self, match: re.Match) -> dict[str, Any]:
        """Parse file content from blob URL."""
        owner, repo, branch, path = match.groups()
        
        # Get file content
        file_data = self._api_request(
            f"/repos/{owner}/{repo}/contents/{path}",
            params={"ref": branch}
        )
        
        if "error" in file_data:
            return file_data
        
        # Decode content
        content = ""
        if "content" in file_data:
            try:
                content = base64.b64decode(file_data["content"]).decode('utf-8', errors='ignore')
            except Exception as e:
                logger.warning(f"Failed to decode file content: {e}")
                content = f"[Binary file or encoding error: {e}]"
        
        # Determine language from file extension
        language = None
        if "." in path:
            ext = path.split(".")[-1].lower()
            ext_to_lang = {
                "py": "Python", "js": "JavaScript", "ts": "TypeScript",
                "java": "Java", "go": "Go", "rs": "Rust",
                "c": "C", "cpp": "C++", "cs": "C#",
                "rb": "Ruby", "php": "PHP", "swift": "Swift",
                "kt": "Kotlin", "scala": "Scala", "md": "Markdown",
                "json": "JSON", "yaml": "YAML", "yml": "YAML",
                "xml": "XML", "html": "HTML", "css": "CSS",
            }
            language = ext_to_lang.get(ext)
        
        result = {
            "title": f"{owner}/{repo}/{path}",
            "content": content,
            "content_type": "code",
            "structured": {
                "owner": owner,
                "repo": repo,
                "path": path,
                "branch": branch,
                "size": file_data.get("size", 0),
                "language": language,
                "encoding": file_data.get("encoding", "utf-8"),
                "sha": file_data.get("sha", ""),
            }
        }
        
        return result

    def _parse_tree(self, match: re.Match) -> dict[str, Any]:
        """Parse directory listing from tree URL."""
        owner, repo, branch, path = match.groups()
        
        # Get directory contents
        tree_data = self._api_request(
            f"/repos/{owner}/{repo}/contents/{path or ''}",
            params={"ref": branch}
        )
        
        if "error" in tree_data:
            return tree_data
        
        if not isinstance(tree_data, list):
            return {"error": "Expected directory, got file"}
        
        # Build markdown listing
        content_parts = [f"# {owner}/{repo}/{path or 'root'}\n"]
        
        files = []
        dirs = []
        for item in tree_data:
            if item["type"] == "dir":
                dirs.append(item)
            else:
                files.append(item)
        
        if dirs:
            content_parts.append("## Directories\n")
            for d in dirs:
                content_parts.append(f"- 📁 {d['name']}/")
        
        if files:
            content_parts.append("\n## Files\n")
            for f in files:
                size_kb = f.get("size", 0) / 1024
                content_parts.append(f"- 📄 {f['name']} ({size_kb:.1f} KB)")
        
        result = {
            "title": f"{owner}/{repo} — {path or 'root'}",
            "content": "\n".join(content_parts),
            "content_type": "directory",
            "structured": {
                "owner": owner,
                "repo": repo,
                "path": path or "",
                "branch": branch,
                "total_items": len(tree_data),
                "directories": [
                    {"name": d["name"], "path": d["path"]}
                    for d in dirs
                ],
                "files": [
                    {
                        "name": f["name"],
                        "path": f["path"],
                        "size": f.get("size", 0),
                        "sha": f.get("sha", ""),
                    }
                    for f in files
                ]
            }
        }
        
        return result

    def _parse_releases(self, match: re.Match) -> dict[str, Any]:
        """Parse releases page."""
        owner, repo = match.groups()
        
        # Get releases
        releases_data = self._api_request(
            f"/repos/{owner}/{repo}/releases",
            params={"per_page": 10}
        )
        
        if "error" in releases_data:
            return releases_data
        
        # Build markdown list
        content_parts = [f"# {owner}/{repo} — Releases\n"]
        for rel in releases_data[:10]:
            content_parts.append(
                f"## {rel['name'] or rel['tag_name']}\n"
                f"**Tag:** {rel['tag_name']} | "
                f"**Published:** {rel.get('published_at', 'N/A')} | "
                f"**Author:** @{rel['author']['login']}\n"
                f"{rel.get('body', '')[:300]}...\n"
            )
        
        result = {
            "title": f"{owner}/{repo} — Releases",
            "content": "\n".join(content_parts),
            "content_type": "releases",
            "structured": {
                "owner": owner,
                "repo": repo,
                "total_count": len(releases_data),
                "items": [
                    {
                        "name": r.get("name", r["tag_name"]),
                        "tag": r["tag_name"],
                        "author": r["author"]["login"],
                        "created_at": r.get("created_at"),
                        "published_at": r.get("published_at"),
                        "draft": r.get("draft", False),
                        "prerelease": r.get("prerelease", False),
                        "body": r.get("body", ""),
                    }
                    for r in releases_data[:10]
                ]
            }
        }
        
        return result

    def _parse_user(self, match: re.Match) -> dict[str, Any]:
        """Parse user or organization profile."""
        username = match.group(1)
        
        # Try user first
        user_data = self._api_request(f"/users/{username}")
        if "error" in user_data:
            # Try org
            user_data = self._api_request(f"/orgs/{username}")
            if "error" in user_data:
                return user_data
        
        is_org = user_data.get("type") == "Organization"
        
        # Build content
        content_parts = [
            f"# {user_data.get('name', username)}\n",
            f"**Username:** @{username}",
            f"**Type:** {'Organization' if is_org else 'User'}",
        ]
        
        if user_data.get("bio"):
            content_parts.append(f"\n{user_data['bio']}")
        
        if user_data.get("company"):
            content_parts.append(f"**Company:** {user_data['company']}")
        
        if user_data.get("location"):
            content_parts.append(f"**Location:** {user_data['location']}")
        
        if user_data.get("blog"):
            content_parts.append(f"**Website:** {user_data['blog']}")
        
        content_parts.append(
            f"\n**Stats:**\n"
            f"- Public repos: {user_data.get('public_repos', 0)}\n"
            f"- Followers: {user_data.get('followers', 0)}\n"
            f"- Following: {user_data.get('following', 0)}"
        )
        
        result = {
            "title": user_data.get("name", username),
            "content": "\n".join(content_parts),
            "content_type": "user_profile" if not is_org else "org_profile",
            "structured": {
                "username": username,
                "name": user_data.get("name"),
                "type": user_data.get("type"),
                "bio": user_data.get("bio"),
                "company": user_data.get("company"),
                "location": user_data.get("location"),
                "email": user_data.get("email"),
                "blog": user_data.get("blog"),
                "twitter": user_data.get("twitter_username"),
                "public_repos": user_data.get("public_repos", 0),
                "public_gists": user_data.get("public_gists", 0),
                "followers": user_data.get("followers", 0),
                "following": user_data.get("following", 0),
                "created_at": user_data.get("created_at"),
                "updated_at": user_data.get("updated_at"),
                "avatar_url": user_data.get("avatar_url"),
                "profile_url": user_data.get("html_url"),
            }
        }
        
        return result

    def discover(self, query: Optional[str] = None, limit: int = 100) -> list[dict]:
        """
        Discover GitHub repositories via search API.
        
        Args:
            query: Search query (e.g., "web scraping python")
            limit: Maximum number of results
        """
        if not query:
            query = "stars:>1000"  # Default: popular repos
        
        search_data = self._api_request(
            "/search/repositories",
            params={
                "q": query,
                "sort": "stars",
                "order": "desc",
                "per_page": min(limit, 100)
            }
        )
        
        if "error" in search_data:
            return []
        
        items = search_data.get("items", [])
        return [
            {
                "url": f"https://github.com/{item['full_name']}",
                "title": item["full_name"],
                "description": item.get("description", ""),
                "stars": item.get("stargazers_count", 0),
                "language": item.get("language"),
            }
            for item in items[:limit]
        ]
