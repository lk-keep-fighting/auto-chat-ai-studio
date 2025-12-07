#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试表格解析功能
验证空单元格和不完整行的处理
"""

import sys
import pandas as pd
from video_automation import VideoProcessor

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
    processor = VideoProcessor()
    
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
            result = processor.parse_table_response(test_case['input'])
            
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
    sys.exit(run_tests())
