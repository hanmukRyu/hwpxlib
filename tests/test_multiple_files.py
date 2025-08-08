#!/usr/bin/env python3
"""
여러 파일로 수정 없이 읽고 저장하는 테스트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from text_modifier import replace_text_in_hwpx
import os

def test_multiple_files():
    """여러 파일을 대상으로 수정 없이 읽고 저장하는 테스트"""
    
    test_files = [
        "../testFile/reader_writer/sample1.hwpx",
        "../testFile/reader_writer/SimpleTable.hwpx", 
        "../testFile/reader_writer/SimplePicture.hwpx",
    ]
    
    for input_file in test_files:
        if not os.path.exists(input_file):
            print(f"⏭️  파일이 존재하지 않음: {input_file}")
            continue
            
        output_file = f"test_save_{os.path.basename(input_file)}"
        
        print(f"\n=== {os.path.basename(input_file)} 테스트 ===")
        print(f"입력: {input_file}")
        print(f"출력: {output_file}")
        
        input_size = os.path.getsize(input_file)
        print(f"입력 크기: {input_size:,} bytes")
        
        try:
            result = replace_text_in_hwpx(
                input_path=input_file,
                output_path=output_file,
                search_text="___NONEXISTENT_TEXT___",
                replace_text="___REPLACEMENT___",
                case_sensitive=True
            )
            
            if os.path.exists(output_file):
                output_size = os.path.getsize(output_file)
                size_ratio = (output_size / input_size) * 100
                print(f"출력 크기: {output_size:,} bytes ({size_ratio:.1f}%)")
                
                if size_ratio >= 95:
                    print("✅ 크기 보존 양호")
                elif size_ratio >= 85:
                    print("⚠️  크기 약간 감소")
                else:
                    print("❌ 크기 많이 감소")
            else:
                print("❌ 출력 파일 생성 실패")
                
        except Exception as e:
            print(f"❌ 오류: {e}")

if __name__ == "__main__":
    test_multiple_files()
