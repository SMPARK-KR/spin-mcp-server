# S.Pin MCP Server - 작업 자동화

## 기능
- 파일 검색 (search_files)
- 디렉토리 리스팅 (list_dir)  
- 파일 내용 읽기 (read_file_content)
- 코드베이스 분석 (analyze_codebase)
- 웹페이지 추출 (get_webpage_text)
- API JSON 파싱 (search_api_json)
- 견적서 생성 (generate_quote)

## 설치
pip install mcp

## 실행
python3 spin_mcp_server.py

## 구조
search_files - 검색_files_pattern_path_file_ext_max_results
list_dir - 디렉토리 구조 리스팅
read_file_content - 파일 내용 읽기
analyze_codebase - 프로젝트 구조 분석
get_webpage_text - 웹페이지 텍스트 추출
search_api_json - API JSON 응답 파싱
generate_quote - 견적서 생성
