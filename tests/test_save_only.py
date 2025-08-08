#!/usr/bin/env python3
"""
데이터 수정 없이 읽고 바로 저장하는 테스트
실제 교체는 하지 않고 파일 저장 로직만 테스트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from text_modifier import replace_text_in_hwpx
import os

def test_save_without_modification():
    """데이터 수정 없이 읽고 바로 저장하는 테스트"""
    
    # 테스트할 입력 파일
    input_file = "testFile/reader_writer/sample1.hwpx"
    output_file = "test_save_only_output.hwpx"
    
    print(f"입력 파일: {input_file}")
    print(f"출력 파일: {output_file}")
    
    # 파일 존재 확인
    if not os.path.exists(input_file):
        print(f"❌ 입력 파일이 존재하지 않습니다: {input_file}")
        return
    
    # 입력 파일 크기 확인
    input_size = os.path.getsize(input_file)
    print(f"입력 파일 크기: {input_size:,} bytes")
    
    try:
        # 실제로는 교체하지 않는 텍스트로 테스트
        # 존재하지 않을 것 같은 텍스트를 찾아서 교체 시도
        result = replace_text_in_hwpx(
            input_path=input_file,
            output_path=output_file,
            search_text="___NONEXISTENT_TEXT___",  # 존재하지 않을 텍스트
            replace_text="___REPLACEMENT___",       # 교체될 텍스트
            case_sensitive=True
        )
        
        print(f"✅ 저장 완료")
        print(f"교체 횟수: {result} (예상: 0)")
        
        # 출력 파일 크기 확인
        if os.path.exists(output_file):
            output_size = os.path.getsize(output_file)
            print(f"출력 파일 크기: {output_size:,} bytes")
            
            # 크기 비교
            size_diff = output_size - input_size
            size_ratio = (output_size / input_size) * 100
            print(f"크기 차이: {size_diff:+,} bytes ({size_ratio:.1f}%)")
            
            if size_ratio >= 95:  # 95% 이상이면 양호
                print(f"✅ 파일 크기가 적절하게 보존되었습니다.")
            else:
                print(f"⚠️  파일 크기가 많이 줄어들었습니다. 데이터 손실 가능성이 있습니다.")
        else:
            print(f"❌ 출력 파일이 생성되지 않았습니다.")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_save_without_modification()
