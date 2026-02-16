"""
版本检查模块 - 启动时检查 GitHub 是否有新版本
零依赖，缓存结果（每天最多检查一次），失败静默
"""

import json
import os
import time
import urllib.request
from pathlib import Path


def check_for_update(repo: str, version_file: str = None):
    """
    检查 GitHub 是否有新版本并提示用户。
    
    Args:
        repo: GitHub 仓库名，格式 "owner/repo"
        version_file: VERSION 文件路径，默认自动检测
    """
    try:
        # 读本地版本
        if version_file is None:
            version_file = str(Path(__file__).parent.parent / "VERSION")
        
        if not os.path.exists(version_file):
            return
        
        with open(version_file, 'r') as f:
            local_version = f.read().strip()
        
        if not local_version:
            return
        
        # 检查缓存（一天只查一次）
        cache_dir = Path.home() / ".cache" / "openclaw-updates"
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = cache_dir / f"{repo.replace('/', '_')}.json"
        
        now = time.time()
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    cache = json.load(f)
                # 24 小时内不重复检查
                if now - cache.get("checked_at", 0) < 86400:
                    remote = cache.get("remote_version", "")
                    if remote and remote != local_version:
                        _print_update_notice(local_version, remote, repo)
                    return
            except (json.JSONDecodeError, KeyError):
                pass
        
        # 查 GitHub API
        url = f"https://api.github.com/repos/{repo}/releases/latest"
        req = urllib.request.Request(url, headers={"Accept": "application/vnd.github.v3+json"})
        
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
        
        remote_version = data.get("tag_name", "").lstrip("v")
        
        # 写缓存
        with open(cache_file, 'w') as f:
            json.dump({"checked_at": now, "remote_version": remote_version}, f)
        
        # 对比版本
        if remote_version and remote_version != local_version:
            _print_update_notice(local_version, remote_version, repo)
    
    except Exception:
        # 任何错误都静默跳过
        pass


def _print_update_notice(local: str, remote: str, repo: str):
    """打印彩色升级提醒"""
    YELLOW = "\033[33m"
    GREEN = "\033[32m"
    RESET = "\033[0m"
    BOLD = "\033[1m"
    
    print(f"\n{YELLOW}{BOLD}⚠ 新版本可用!{RESET}")
    print(f"  当前: v{local}  →  最新: {GREEN}v{remote}{RESET}")
    print(f"  运行 {BOLD}git pull{RESET} 更新")
    print(f"  详情: https://github.com/{repo}/releases\n")
