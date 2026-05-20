#!/usr/bin/env python3
"""
S.Pin MCP Server - 작업 병목 해결용
기능: 파일 검색, 구조 분석, 웹 데이터 조회, 견적서 생성
"""

from mcp.server.fastmcp import FastMCP
import os
import re
import subprocess
from pathlib import Path
from datetime import datetime
import json

mcp = FastMCP(
    "spin-workflow-server",
    instructions="S.Pin 테크놀로지 작업 자동화 MCP 서버",
)

# ==================== 파일 검색 ====================

@mcp.tool()
def search_files(
    pattern: str,
    path: str = ".",
    file_ext: str = None,
    max_results: int = 50,
) -> dict:
    """파일 내용에서 패턴 검색 (grep/ripgrep 대체)"""
    try:
        cmd = ["rg", "-l", "-n", pattern, path]
        if file_ext:
            cmd.extend(["--glob", f"*.{file_ext}"])
        cmd.extend(["-n", "--max-count", str(max_results)])
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        files = result.stdout.strip().split("\n") if result.stdout.strip() else []
        return {"found": len(files), "files": files[:max_results]}
    except Exception as e:
        return {"error": str(e), "files": []}

@mcp.tool()
def list_dir(
    path: str = ".",
    depth: int = 2,
    include_hidden: bool = False,
) -> dict:
    """디렉토리 구조 리스팅"""
    try:
        base = Path(path).resolve()
        tree = _build_tree(base, depth, include_hidden)
        return {"path": str(base), "tree": tree}
    except Exception as e:
        return {"error": str(e)}

def _build_tree(path: Path, max_depth: int, include_hidden: bool, current_depth: int = 0) -> dict:
    if current_depth >= max_depth:
        return {"type": "directory", "name": path.name, "children": []}
    
    try:
        entries = sorted(path.iterdir())
        if not include_hidden:
            entries = [e for e in entries if not e.name.startswith('.')]
        
        children = []
        for entry in entries:
            if entry.is_dir():
                children.append(_build_tree(entry, max_depth, include_hidden, current_depth + 1))
            else:
                children.append({"type": "file", "name": entry.name, "size": entry.stat().st_size})
        
        return {"type": "directory", "name": path.name, "children": children}
    except Exception:
        return {"type": "directory", "name": path.name, "children": []}

@mcp.tool()
def read_file_content(
    file_path: str,
    lines: int = 100,
) -> dict:
    """파일 내용 읽기 (행 번호 포함)"""
    try:
        path = Path(file_path).resolve()
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        line_count = len(content.split('\n'))
        preview = content[:lines * 100]  # 대략 lines 줄
        return {
            "path": str(path),
            "line_count": line_count,
            "content_preview": preview,
        }
    except Exception as e:
        return {"error": str(e)}

# ==================== 구조 분석 ====================

@mcp.tool()
def analyze_codebase(
    path: str = ".",
    languages: list = None,
) -> dict:
    """프로젝트 구조 및 언어별 LOC 분석"""
    try:
        path = Path(path).resolve()
        extensions = {
            'python': ['.py'],
            'typescript': ['.ts', '.tsx'],
            'javascript': ['.js', '.jsx'],
            'markdown': ['.md'],
            'yaml': ['.yaml', '.yml'],
            'json': ['.json'],
        }
        
        if languages:
            ext_map = {lang: extensions.get(lang, []) for lang in languages}
        else:
            ext_map = extensions
        
        loc = {lang: 0 for lang in ext_map}
        files_by_lang = {lang: [] for lang in ext_map}
        
        for lang, exts in ext_map.items():
            for ext in exts:
                for py in path.rglob(f'*{ext}'):
                    try:
                        with open(py, 'r', encoding='utf-8') as f:
                            lines = len([l for l in f.read().split('\n') if l.strip()])
                        loc[lang] += lines
                        files_by_lang[lang].append(str(py.relative_to(path)))
                    except:
                        pass
        
        total_files = sum(len(v) for v in files_by_lang.values())
        return {
            "total_files": total_files,
            "total_loc": sum(loc.values()),
            "by_language": {lang: loc[lang] for lang in ext_map},
            "sample_files": {lang: files_by_lang[lang][:3] for lang in ext_map}
        }
    except Exception as e:
        return {"error": str(e)}

# ==================== 웹 데이터 조회 ====================

@mcp.tool()
def get_webpage_text(
    url: str,
    max_chars: int = 5000,
) -> dict:
    """웹페이지 텍스트 추출"""
    try:
        import urllib.request
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as response:
            html = response.read().decode('utf-8', errors='ignore')
        
        # 간단한 HTML 태그 제거
        text = re.sub(r'<[^>]+>', ' ', html)
        text = re.sub(r'\s+', ' ', text).strip()
        
        return {
            "url": url,
            "text_preview": text[:max_chars],
            "total_chars": len(text),
        }
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def search_api_json(
    url: str,
    expected_keys: list = None,
) -> dict:
    """API JSON 응답 파싱"""
    try:
        import urllib.request
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode('utf-8'))
        
        if isinstance(data, dict):
            keys = list(data.keys())[:20]
            summary = {k: type(data[k]).__name__ for k in keys}
            return {"type": "dict", "keys": keys, "sample": summary}
        elif isinstance(data, list):
            return {"type": "list", "length": len(data), "first_item_type": type(data[0]).__name__ if data else None}
        else:
            return {"type": type(data).__name__, "value": str(data)[:500]}
    except Exception as e:
        return {"error": str(e)}

# ==================== 견적서 관련 ====================

@mcp.tool()
def generate_quote(
    customer: str,
    project: str,
    contact: str,
    items: list,
) -> dict:
    """견적서 생성 (기존 스크립트 활용)"""
    try:
        import sys
        sys.path.insert(0, '/Users/judepark/Desktop')
        from spin_quote_generator import create_quote
        path = create_quote(
            customer=customer,
            project=project,
            contact=contact,
            items=items,
        )
        return {"status": "success", "path": path}
    except Exception as e:
        return {"error": str(e)}

# ==================== 메인 ====================

if __name__ == '__main__':
    mcp.run(transport='stdio')
