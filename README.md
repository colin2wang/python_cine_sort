# Python 豆瓣电影排序工具

这是一个用于查询和处理豆瓣电影信息的Python工具包。

## 功能特性

- 🎬 豆瓣电影搜索查询
- 📊 电影信息解析（待完善）
- 🔧 完善的错误处理机制
- 🌐 支持中文电影名称查询

## 项目结构

```
python_cine_sort/
├── utils/
│   ├── __init__.py
│   ├── douban_html_util.py     # 豆瓣查询核心模块
│   ├── movie_file_scanner.py   # 电影文件扫描器
│   └── logging_util.py         # 日志工具
├── test_douban_html_util.py    # 豆瓣查询测试
├── test_movie_scanner.py       # 电影扫描器测试
├── movie_scanner_example.py    # 扫描器使用示例
├── cleanup_test_files.py       # 测试文件清理工具
├── movies_config_example.yml   # 扫描器配置示例
├── example_usage.py            # 使用示例
├── pyproject.toml              # 项目配置
└── uv.lock                    # 依赖锁定文件
```

## 安装依赖

```bash
# 使用uv安装依赖
uv sync

# 或者使用pip安装
pip install requests>=2.32.5
```

## 使用方法

### 基本使用

```python
from utils.douban_html_util import get_movie_search_result_html

# 查询电影信息
html_content = get_movie_search_result_html("肖申克的救赎", "1994")
if html_content:
    print(f"获取到 {len(html_content)} 字符的内容")
```

### 运行示例

```bash
# 运行豆瓣查询测试
python test_douban_html_util.py

# 运行电影扫描器测试
python test_movie_file_util.py

# 运行电影扫描器示例
python movie_scanner_example.py

# 运行使用示例
python example_usage.py

# 清理测试文件
python cleanup_test_files.py --dry-run  # 预览将要删除的文件
python cleanup_test_files.py            # 实际删除测试文件
```

## 代码改进说明

### 已修复的问题：

1. **函数名拼写错误**：`get_moive` → `get_movie`
2. **字符串格式化**：使用现代的f-string替代旧式%格式化
3. **缺少返回值**：添加了完整的返回逻辑
4. **错误处理不完善**：增加了详细的异常处理
5. **缺少类型提示**：添加了typing注解
6. **文档字符串**：完善了函数说明文档

### 新增功能：

1. **超时控制**：设置10秒请求超时
2. **编码处理**：正确设置UTF-8编码
3. **详细日志**：提供清晰的成功/失败反馈
4. **扩展性设计**：预留了电影信息解析接口

## 注意事项

- 该工具仅用于学习和研究目的
- 请遵守豆瓣网站的使用条款
- 建议适当控制请求频率，避免对服务器造成压力
- 返回的是原始HTML内容，如需结构化数据需要进一步解析

## 开发计划

- [ ] 实现HTML内容解析功能
- [ ] 添加电影评分和详情提取
- [ ] 支持批量查询和导出功能
- [ ] 添加缓存机制提高效率
- [ ] 完善单元测试覆盖

## 许可证

MIT License