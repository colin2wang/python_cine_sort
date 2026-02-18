import requests
from typing import Optional

from utils import get_default_logger

# 获取默认日志记录器
logger = get_default_logger()


def get_movie_search_result_html(name: str, year: str) -> Optional[str]:
    """获取豆瓣电影搜索结果
    
    Args:
        name (str): 电影名称
        year (str): 电影年份
    
    Returns:
        Optional[str]: HTML响应内容，失败时返回None
    """
    # 构建搜索URL
    url = f'https://www.douban.com/search?cat=1002&q={name} {year}'
    
    # 设置请求头，模拟浏览器访问
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    try:
        # 发送GET请求
        logger.info(f"GET {url}")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # 检查HTTP状态码
        
        # 设置正确的编码
        response.encoding = 'utf-8'
        
        logger.info(f"✓ 成功获取豆瓣搜索结果: {name} ({year})")
        return response.text
        
    except requests.exceptions.Timeout:
        logger.warning(f"✗ 请求超时: {name} ({year})")
        return None
    except requests.exceptions.ConnectionError:
        logger.error(f"✗ 连接错误: {name} ({year})")
        return None
    except requests.exceptions.HTTPError as e:
        logger.error(f"✗ HTTP错误 {e.response.status_code}: {name} ({year})")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"✗ 请求异常: {e} - {name} ({year})")
        return None
    except Exception as e:
        logger.error(f"✗ 未知错误: {e} - {name} ({year})")
        return None


def _create_empty_movie_info(error_message: str = None) -> dict:
    """创建空的电影信息字典
    
    Args:
        error_message (str, optional): 错误信息
        
    Returns:
        dict: 空的电影信息字典
    """
    return {
        'title': '',
        'rating': '',
        'description': '',
        'directors': [],
        'actors': [],
        'year': '',
        'genres': [],
        'original_title': '',
        'review_count': '',
        'sid': '',
        'error': error_message
    }


def parse_movie_info(html_content: str) -> dict:
    """解析豆瓣搜索结果中的电影信息（使用正则表达式）
    
    Args:
        html_content (str): 豆瓣搜索页面HTML内容
    
    Returns:
        dict: 解析出的电影信息
    """
    import re
    
    # 参数验证
    if html_content is None:
        logger.error("✗ HTML内容为None")
        return _create_empty_movie_info('解析错误: HTML内容为空')
    
    if not isinstance(html_content, str):
        logger.error(f"✗ HTML内容类型错误: {type(html_content)}")
        return _create_empty_movie_info(f'解析错误: 期望字符串类型，得到 {type(html_content).__name__}')
    
    try:
        movie_info = _create_empty_movie_info()
        
        # 使用分步解析的方法，更加稳健
        
        # 首先找到所有的result块
        result_blocks = re.findall(r'<div class="result">.*?</div>\s*</div>', html_content, re.DOTALL)
        
        # 遍历每个result块，找到第一个有效的电影结果
        for result_block in result_blocks:
            # 检查是否包含电影标记和评分
            if '[电影]' in result_block and 'rating_nums' in result_block:
                # 提取标题
                title_pattern = r'<h3>\s*<span>\[电影\]</span>\s*&nbsp;<a[^>]*>([^<]+)</a>'
                title_match = re.search(title_pattern, result_block)
                if title_match:
                    movie_info['title'] = title_match.group(1).strip()

                # 提取豆瓣电影ID (sid)
                sid_pattern = r'sid:\s*(\d+)'
                sid_match = re.search(sid_pattern, result_block)
                if sid_match:
                    movie_info['sid'] = sid_match.group(1)


                # 提取评分
                rating_pattern = r'<span[^>]*class="rating_nums"[^>]*>([\d.]+)</span>'
                rating_match = re.search(rating_pattern, result_block)
                if rating_match:
                    movie_info['rating'] = rating_match.group(1)
                
                # 提取评价人数
                review_pattern = r'<span>\((\d+)人评价\)</span>'
                review_match = re.search(review_pattern, result_block)
                if review_match:
                    movie_info['review_count'] = review_match.group(1)
                
                # 提取原始标题
                original_title_pattern = r'原名:([^/]+)'
                original_match = re.search(original_title_pattern, result_block)
                if original_match:
                    movie_info['original_title'] = original_match.group(1).strip()
                
                # 提取subject-cast信息
                cast_pattern = r'<span[^>]*class="subject-cast"[^>]*>(.*?)</span>'
                cast_match = re.search(cast_pattern, result_block, re.DOTALL)
                if cast_match:
                    cast_text = re.sub(r'<.*?>', '', cast_match.group(1)).strip()
                    
                    # 提取年份
                    year_matches = re.findall(r'(\d{4})', cast_text)
                    if year_matches:
                        movie_info['year'] = year_matches[-1]
                    
                    # 解析导演和演员
                    # 格式: "原名:xxx / 导演 / 演员1 / 演员2 / 年份"
                    clean_cast = re.sub(r'^原名:[^/]*/', '', cast_text).strip()
                    parts = [part.strip() for part in clean_cast.split('/') if part.strip()]
                    
                    if len(parts) >= 2:
                        # 第一个是导演
                        movie_info['directors'] = [parts[0]]
                        # 其他是演员（排除年份）
                        actors = []
                        for part in parts[1:]:
                            if not re.match(r'^\d{4}$', part):
                                actors.append(part)
                            else:
                                break
                        movie_info['actors'] = actors[:5]
                
                # 提取简介
                desc_pattern = r'<p[^>]*>(.*?)</p>'
                desc_match = re.search(desc_pattern, result_block, re.DOTALL)
                if desc_match:
                    desc_text = re.sub(r'<.*?>', '', desc_match.group(1)).strip()
                    movie_info['description'] = desc_text[:200]
                
                # 找到第一个有效结果就退出循环
                break
        
        # 备用方案：如果没有找到结构化的第一个结果
        if not movie_info['title']:
            # 查找所有可能的电影标题
            all_titles_pattern = r'<h3>\s*<span>\[电影\]</span>\s*&nbsp;<a[^>]*href="[^"]*?">([^<]+?)</a>'
            all_titles = re.findall(all_titles_pattern, html_content, re.DOTALL)
            if all_titles:
                movie_info['title'] = all_titles[0].strip()  # 取第一个电影标题
            
            # 如果还是没有标题，使用更宽松的匹配
            if not movie_info['title']:
                simple_title_pattern = r'<a[^>]*>([^<>]{2,50}?)</a>'
                simple_matches = re.findall(simple_title_pattern, html_content)
                for title_text in simple_matches:
                    title_text = title_text.strip()
                    # 过滤掉明显不是电影标题的内容
                    if title_text and not any(keyword in title_text for keyword in ['可播放', '预告', '花絮', '回顶部', '↑', '&#8593;']):
                        movie_info['title'] = title_text
                        break
        
        return movie_info
        
    except Exception as e:
        logger.error(f"✗ 解析HTML时出错: {e}")
        return _create_empty_movie_info(f'解析错误: {str(e)}')