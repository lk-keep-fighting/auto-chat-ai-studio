#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的表格解析测试
不依赖 VideoProcessor，直接测试解析逻辑
"""

import re
import pandas as pd


def parse_table_response(response_text):
    """解析 AI 响应中的表格数据（简化版）"""
    if not response_text:
        return None
    
    try:
        # 解析 Markdown 表格
        lines = response_text.strip().split('\n')
        table_data = []
        headers = []
        
        for i, line in enumerate(lines):
            # 跳过分隔线
            if re.match(r'^[\s\-\|]+$', line):
                continue
            
            # 检查是否是表格行
            if '|' in line:
                # 分割单元格，但保留空单元格
                cells = line.split('|')
                # 移除首尾的空单元格（Markdown 表格通常以 | 开头和结尾）
                if cells and not cells[0].strip():
                    cells = cells[1:]
                if cells and not cells[-1].strip():
                    cells = cells[:-1]
                # 清理每个单元格的空白
                cells = [cell.strip() for cell in cells]
                
                if cells:
                    if not headers:
                        # 第一行作为表头
                        headers = cells
                        print(f"📋 检测到表头: {headers}")
                    else:
                        # 数据行：即使单元格数量不匹配也尝试解析
                        row_dict = {}
                        for j, header in enumerate(headers):
                            # 如果该列有数据，使用数据；否则使用空字符串
                            if j < len(cells):
                                row_dict[header] = cells[j] if cells[j] else ""
                            else:
                                row_dict[header] = ""
                        table_data.append(row_dict)
        
        if table_data:
            print(f"✅ 解析到 {len(table_data)} 行表格数据")
            # 显示每列的非空数据统计
            if headers:
                for header in headers:
                    non_empty = sum(1 for row in table_data if row.get(header, ""))
                    print(f"  - {header}: {non_empty}/{len(table_data)} 行有数据")
            return table_data
        
        return None
        
    except Exception as e:
        print(f"❌ 解析表格数据失败: {e}")
        import traceback
        traceback.print_exc()
        return None


# 测试用例
test_cases = [
    {
        "name": "完整数据",
        "input": """
| filename | start | end | Folder | Folder2 | Folder3 | music | cover_time | title |
|----------|-------|-----|--------|---------|---------|-------|------------|-------|
| video1.mp4 | 0:00 | 1:00 | action | fight | sword | bgm1.mp3 | 0:30 | Epic Battle |
""",
        "expected_rows": 1,
        "expected_columns": 9,
    },
    {
        "name": "部分空数据",
        "input": """
| filename | start | end | Folder | Folder2 | Folder3 | music | cover_time | title |
|----------|-------|-----|--------|---------|---------|-------|------------|-------|
| video1.mp4 | 0:00 | 1:00 | action | fight | sword | bgm1.mp3 | 0:30 | Epic Battle |
| video2.mp4 | 0:00 | 2:00 | drama | love | | | | Romance Story |
| video3.mp4 | 0:00 | 1:30 | comedy | | | bgm2.mp3 | | |
""",
        "expected_rows": 3,
        "expected_columns": 9,
    },
    {
        "name": "不完整的行",
        "input": """
| filename | start | end | Folder | Folder2 | Folder3 | music | cover_time | title |
|----------|-------|-----|--------|---------|---------|-------|------------|-------|
| video1.mp4 | 0:00 | 1:00 | action | fight | sword |
| video2.mp4 | 0:00 | 2:00 | drama |
| video3.mp4 | 0:00 |
""",
        "expected_rows": 3,
        "expected_columns": 9,
    },
    {
        "name": "全部为空的列",
        "input": """
| filename | start | end | Folder | Folder2 | Folder3 | music | cover_time | title |
|----------|-------|-----|--------|---------|---------|-------|------------|-------|
| video1.mp4 | 0:00 | 1:00 | action | fight | sword | | | |
| video2.mp4 | 0:00 | 2:00 | drama | love | | | | |
| video3.mp4 | 0:00 | 1:30 | comedy | | | | | |
""",
        "expected_rows": 3,
        "expected_columns": 9,
    },
]


def run_tests():
    """运行所有测试用例"""
    print("="*60)
    print("🧪 表格解析测试")
    print("="*60)
    
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(test_cases, start=1):
        print(f"\n{'─'*60}")
        print(f"测试 {i}: {test_case['name']}")
        print(f"{'─'*60}")
        
        try:
            # 解析表格
            result = parse_table_response(test_case['input'])
            
            if result is None:
                print(f"❌ 解析失败: 返回 None")
                failed += 1
                continue
            
            # 转换为 DataFrame 以便检查
            df = pd.DataFrame(result)
            
            # 验证行数
            if len(df) != test_case['expected_rows']:
                print(f"❌ 行数不匹配: 期望 {test_case['expected_rows']}, 实际 {len(df)}")
                failed += 1
                continue
            
            # 验证列数
            if len(df.columns) != test_case['expected_columns']:
                print(f"❌ 列数不匹配: 期望 {test_case['expected_columns']}, 实际 {len(df.columns)}")
                failed += 1
                continue
            
            # 显示解析结果
            print(f"✅ 解析成功")
            print(f"\n📊 数据预览:")
            print(df.to_string(index=False))
            
            # 显示每列的数据统计
            print(f"\n📈 数据统计:")
            for col in df.columns:
                non_empty = df[col].astype(str).str.strip().ne('').sum()
                print(f"  - {col}: {non_empty}/{len(df)} 行有数据")
            
            passed += 1
            
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    # 输出总结
    print(f"\n{'='*60}")
    print(f"🎯 测试总结")
    print(f"{'='*60}")
    print(f"✅ 通过: {passed}/{len(test_cases)}")
    print(f"❌ 失败: {failed}/{len(test_cases)}")
    
    if failed == 0:
        print(f"\n🎉 所有测试通过！")
        return 0
    else:
        print(f"\n⚠️ 有 {failed} 个测试失败")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(run_tests())
