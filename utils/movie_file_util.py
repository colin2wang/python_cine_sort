"""电影文件扫描工具模块

用于扫描指定目录下的视频文件，提取电影名称和年份信息
"""

import re
import yaml
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from .logging_util import get_default_logger

logger = get_default_logger()


@dataclass
class MovieFileInfo:
    """电影文件信息数据类"""
    file_path: Path
    movie_name: str
    year: Optional[str]
    extension: str
    raw_filename: str


class MovieFileScannerConfig:
    """电影文件扫描器配置类"""
    
    def __init__(self, config_file: Optional[Path] = None):
        # 默认值设为空，强制从配置文件读取
        self.extensions = []
        self.cleanup_rules = []
        self.year_patterns = []
        self.movie_name_rules = []

            
        if config_file and config_file.exists():
            self.load_config(config_file)
        else:
            raise ValueError("必须提供有效的配置文件路径")
    
    def load_config(self, config_file: Path):
        """从YAML配置文件加载配置"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            if 'extensions' in config:
                self.extensions = [ext.lower() if ext.startswith('.') else f'.{ext.lower()}' 
                                 for ext in config['extensions']]
                    
            # 新的清理规则配置
            if 'cleanup_rules' in config:
                self.cleanup_rules = config['cleanup_rules']

                    
            if 'year_patterns' in config:
                self.year_patterns = config['year_patterns']
                    
            # 新的电影名规则配置
            if 'movie_name_rules' in config:
                self.movie_name_rules = config['movie_name_rules']
                
            logger.debug(f"✓ 已从 {config_file} 加载配置")
            
        except Exception as e:
            logger.warning(f"✗ 加载配置文件失败: {e}，使用默认配置")


class MovieFileScanner:
    """电影文件扫描器"""
    
    def __init__(self, config: Optional[MovieFileScannerConfig] = None):
        self.config = config or MovieFileScannerConfig()
        self.logger = get_default_logger()
    
    def scan_directory(self, directory: Path, recursive: bool = True) -> List[MovieFileInfo]:
        """扫描目录下的电影文件
        
        Args:
            directory: 要扫描的目录路径
            recursive: 是否递归扫描子目录
            
        Returns:
            List[MovieFileInfo]: 电影文件信息列表
        """
        if not directory.exists():
            self.logger.error(f"✗ 目录不存在: {directory}")
            return []
        
        if not directory.is_dir():
            self.logger.error(f"✗ 路径不是目录: {directory}")
            return []
        
        movie_files = []
        
        # 确定扫描模式
        if recursive:
            file_iterator = directory.rglob('*')
        else:
            file_iterator = directory.iterdir()
        
        for file_path in file_iterator:
            if file_path.is_file() and file_path.suffix.lower() in self.config.extensions:
                movie_info = self.extract_movie_info(file_path)
                if movie_info:
                    movie_files.append(movie_info)
        
        self.logger.info(f"✓ 扫描完成，找到 {len(movie_files)} 个电影文件")
        return movie_files
    
    def extract_movie_info(self, file_path: Path) -> Optional[MovieFileInfo]:
        """从文件名提取电影信息
        
        Args:
            file_path: 文件路径
            
        Returns:
            MovieFileInfo: 电影信息对象，解析失败时返回None
        """
        try:
            filename = file_path.stem  # 获取不带扩展名的文件名
            extension = file_path.suffix.lower()
            
            # 第一阶段：清理文件名中的无用信息
            cleaned_name = self._cleanup_filename(filename)
            
            if not cleaned_name:
                self.logger.warning(f"✗ 清理后文件名为空: {file_path.name}")
                return None
            
            # 第二阶段：从清理后的字符串中提取年份
            year = self._extract_year_from_cleaned(cleaned_name)
            
            # 第三阶段：从清理后的字符串中提取电影名称
            movie_name = self._extract_movie_name_from_cleaned(cleaned_name)
            
            if not movie_name:
                self.logger.warning(f"✗ 无法从清理后的文件名提取电影名称: {file_path.name} -> {cleaned_name}")
                return None
            
            movie_info = MovieFileInfo(
                file_path=file_path,
                movie_name=movie_name,
                year=year,
                extension=extension,
                raw_filename=file_path.name
            )
            
            self.logger.debug(f"✓ 解析文件: {file_path.name} -> 清理后: {cleaned_name}, 名称: {movie_name}, 年份: {year}")
            return movie_info
            
        except Exception as e:
            self.logger.error(f"✗ 解析文件 {file_path.name} 时出错: {e}")
            return None
    
    def _cleanup_filename(self, filename: str) -> str:
        """清理文件名中的无用信息
        
        Args:
            filename: 原始文件名
            
        Returns:
            str: 清理后的文件名
        """
        cleaned = filename
        original = filename
        
        # 按顺序应用清理规则
        for i, pattern in enumerate(self.config.cleanup_rules, 1):
            before_clean = cleaned
            cleaned = re.sub(pattern, ' ', cleaned)
            if before_clean != cleaned:
                self.logger.debug(f"清理规则{i}应用: '{pattern}' -> '{before_clean}' => '{cleaned}'")
        
        # 清理多余的空格和分隔符
        cleaned = re.sub(r'[.\-_]+', ' ', cleaned)  # 点号、横线、下划线转为空格
        cleaned = re.sub(r'\s+', ' ', cleaned)      # 合并多个空格
        cleaned = cleaned.strip()                   # 去除首尾空格
        
        self.logger.debug(f"文件名清理完成: '{original}' -> '{cleaned}'")
        return cleaned
    
    def _extract_year_from_cleaned(self, cleaned_filename: str) -> Optional[str]:
        """从清理后的文件名中提取年份
        
        Args:
            cleaned_filename: 清理后的文件名
            
        Returns:
            str: 年份字符串，未找到时返回None
        """
        # 使用更严格的年份匹配规则
        # 只匹配独立的四位数年份（前后有边界）
        year_pattern = r'(?:^|\s)(19|20)\d{2}(?:$|\s)'
        
        # 寻找所有可能的年份
        matches = re.finditer(year_pattern, cleaned_filename)
        valid_years = []
        
        for match in matches:
            year_str = match.group().strip()
            year_num = int(year_str)
            
            # 验证年份合理性（1900-2030范围内）
            if 1900 <= year_num <= 2030:
                # 检查是否可能是电影标题的一部分而不是真正的年份
                context_before = cleaned_filename[:match.start()].strip()
                context_after = cleaned_filename[match.end():].strip()
                
                # 如果年份前后都有内容，且长度都不太短，可能是标题的一部分
                if len(context_before) > 2 and len(context_after) > 2:
                    # 进一步检查：如果年份出现在标题中间位置，可能是剧情元素而非发行年份
                    words_before = context_before.split()
                    words_after = context_after.split()
                    
                    # 对于电影文件名，如果年份后面跟着明显的技术标识，则更可能是发行年份
                    # 而不是标题内容
                    if (words_before and len(words_before[-1]) > 1 and 
                        words_after and len(words_after[0]) > 1):
                        # 检查年份后是否有技术标识
                        next_word = words_after[0].upper()
                        tech_indicators = ['1080P', '720P', 'HD', 'BD', 'DVD', 'X264', 'H264', 'AAC', 'MP4', 'MKV']
                        if any(indicator in next_word for indicator in tech_indicators):
                            # 年份后有技术标识，很可能是发行年份
                            self.logger.debug(f"年份 {year_str} 后有技术标识 '{next_word}'，判断为发行年份")
                        else:
                            self.logger.debug(f"跳过年份 {year_str}，判断为标题内容: '{cleaned_filename}'")
                            continue
                
                valid_years.append(year_str)
                self.logger.debug(f"找到有效年份: '{cleaned_filename}' -> {year_str}")
        
        # 返回最后一个有效的年份（通常是文件名末尾的年份）
        if valid_years:
            return valid_years[-1]
        
        return None
    
    def _extract_movie_name_from_cleaned(self, cleaned_filename: str) -> Optional[str]:
        """从清理后的文件名中提取电影名称
        
        Args:
            cleaned_filename: 清理后的文件名
            
        Returns:
            str: 电影名称，未匹配时返回None
        """
        # 首先尝试使用电影名规则进行匹配
        for i, pattern in enumerate(self.config.movie_name_rules, 1):
            match = re.search(pattern, cleaned_filename, re.IGNORECASE)
            if match:
                movie_name = match.group(1).strip()
                if movie_name:
                    self.logger.debug(f"电影名规则{i}匹配成功: '{cleaned_filename}' -> '{movie_name}'")
                    return movie_name
        
        # 如果没有专门的规则，需要进一步清理可能残留的技术信息
        refined_name = cleaned_filename
        
        # 移除可能残留的年份（更严格的匹配）
        refined_name = re.sub(r'(?:^|\s)(19|20)\d{2}(?:$|\s)', ' ', refined_name)
        
        # 移除可能残留的分辨率和技术标识
        tech_patterns = [
            r'\d+[pP]', r'\d+[kK]', r'\b4[Kk]\b', r'\b8[Kk]\b',
            r'\bHD\b', r'\bBD\b', r'\bDVD\b', r'\bWEBRIP\b', r'\bBLURAY\b',
            r'\bBDRIP\b', r'\bHDRIP\b', r'\bCAM\b', r'\bR5\b', r'\bTS\b', r'\bTC\b',
            r'\bSCR\b', r'\bHQ\b', r'\bHQCD\b',
            r'\bXVID\b', r'\bDIVX\b', r'\bH264\b', r'\bH\.264\b', r'\bH265\b', 
            r'\bH\.265\b', r'\bHEVC\b', r'\bAVC\b', r'\bVP9\b',
            # 发布组标识
            r'\bBDYS\b|\bYJYS\b|\bJYYS\b|\bDYYS\b|\bYYDS\b'
        ]
        
        for pattern in tech_patterns:
            refined_name = re.sub(pattern, ' ', refined_name, flags=re.IGNORECASE)
        
        # 移除语言和字幕标识
        language_patterns = [
            r'\b国语\b', r'\b粤语\b', r'\b台配\b', r'\b日语\b', r'\b韩语\b',
            r'\b英语\b', r'\b法语\b', r'\b德语\b', r'\b俄语\b', r'\b西班牙语\b', r'\b泰语\b',
            r'\b菲律宾语\b', r'\b他加禄语\b',
            r'\b中字\b', r'\b中英双字\b', r'\b双语字幕\b', r'\b内嵌中字\b',
            r'\b简体中字\b', r'\b繁体中字\b', r'\b无水印\b', r'\b完整版\b',
            r'\b高清版\b', r'\b修复版\b', r'\b导演版\b', r'\b加长版\b',
            r'\b国粤双语\b', r'\b日语中字\b', r'\b英语中字\b',
            # 英文语言标识（完整单词匹配，避免误删标题）
            r'\bFilipino\b', r'\bTagalog\b', r'\bEnglish\b', r'\bChinese\b'
        ]
        
        for pattern in language_patterns:
            refined_name = re.sub(pattern, ' ', refined_name, flags=re.IGNORECASE)
        
        # 再次清理多余的空格和标点
        refined_name = re.sub(r'\s+', ' ', refined_name)  # 合并多个空格
        refined_name = re.sub(r'[\s\-_.]+$', '', refined_name)  # 移除结尾的空格和标点
        refined_name = re.sub(r'^[\s\-_.]+', '', refined_name)  # 移除开头的空格和标点
        refined_name = refined_name.strip()
        
        # 移除残留的技术标识（在精细化处理的最后阶段）
        final_tech_patterns = [
            r'\b\d+[pP]\b', r'\b\d+[kK]\b',  # 分辨率
            r'\bX264\b|\bH264\b|\bH\.264\b',  # 编码格式
            r'\bAAC\b|\bAC3\b|\bDTS\b',  # 音频格式
            r'\bMP4\b|\bMKV\b|\bAVI\b',  # 文件格式
            r'\bBDYS\b|\bYJYS\b|\bJYYS\b'  # 发布组标识
        ]
        
        # 单独处理年份移除（避免影响其他处理）
        refined_name = re.sub(r'(?:^|\s)(19|20)\d{2}(?:$|\s)', ' ', refined_name)
        
        for pattern in final_tech_patterns:
            refined_name = re.sub(pattern, ' ', refined_name, flags=re.IGNORECASE)
            refined_name = re.sub(r'\s+', ' ', refined_name)  # 重新合并空格
        
        refined_name = refined_name.strip()
        
        # 移除孤立的单字符（可能是残留的标点或字母）
        words = refined_name.split()
        filtered_words = [word for word in words if len(word) > 1 or word.isalnum()]
        refined_name = ' '.join(filtered_words)
        
        if refined_name:
            self.logger.debug(f"精细化处理: '{cleaned_filename}' -> '{refined_name}'")
            return refined_name
        
        # 最后兜底：如果还有内容就返回
        if cleaned_filename:
            self.logger.debug(f"使用默认规则: '{cleaned_filename}' -> '{cleaned_filename}'")
            return cleaned_filename
        
        return None


def scan_movies_from_directory(directory: str, 
                              config_file: Optional[str] = None,
                              recursive: bool = True) -> List[Dict]:
    """便捷函数：扫描目录并返回字典格式的结果
    
    Args:
        directory: 目录路径
        config_file: 配置文件路径（可选）
        recursive: 是否递归扫描
        
    Returns:
        List[Dict]: 包含电影信息的字典列表
    """
    dir_path = Path(directory)
    
    # 查找同名配置文件
    if config_file is None:
        config_candidates = [
            dir_path / f"{dir_path.name}.yml",
            dir_path / f"{dir_path.name}.yaml",
            dir_path / "config.yml",
            dir_path / "config.yaml"
        ]
        for candidate in config_candidates:
            if candidate.exists():
                config_file = str(candidate)
                break
    
    # 创建配置对象
    config_obj = None
    if config_file:
        config_obj = MovieFileScannerConfig(Path(config_file))
    
    # 扫描文件
    scanner = MovieFileScanner(config_obj)
    movie_files = scanner.scan_directory(dir_path, recursive)
    
    # 转换为字典格式
    result = []
    for movie_info in movie_files:
        result.append({
            'file_path': str(movie_info.file_path),
            'movie_name': movie_info.movie_name,
            'year': movie_info.year,
            'extension': movie_info.extension,
            'raw_filename': movie_info.raw_filename
        })
    
    return result