"""HWPX 텍스트 수정 예제 스크립트

이 스크립트는 text_modifier.py 모듈을 사용하는 다양한 예제를 보여줍니다.
"""

from text_modifier import (
    modify_hwpx_text, 
    replace_text_in_hwpx, 
    get_hwpx_text_stats,
    uppercase_hwpx_text,
    lowercase_hwpx_text,
    remove_extra_spaces
)
import re


def example_text_formatting():
    """텍스트 서식 변경 예제"""
    input_file = "testFile/tool/textextractor/multipara.hwpx"
    
    # 1. 모든 숫자를 [숫자]로 감싸기
    def wrap_numbers(text):
        return re.sub(r'\d+', r'[\g<0>]', text)
    
    modify_hwpx_text(input_file, "example_numbers_wrapped.hwpx", wrap_numbers)
    print("숫자 감싸기 완료")
    
    # 2. 이메일 주소 제거
    def remove_emails(text):
        return re.sub(r'\S+@\S+\.\S+', '[이메일 제거됨]', text)
    
    modify_hwpx_text(input_file, "example_emails_removed.hwpx", remove_emails)
    print("이메일 제거 완료")
    
    # 3. 첫 글자를 대문자로 만들기 (각 문장의)
    def capitalize_sentences(text):
        sentences = text.split('. ')
        capitalized = [s.capitalize() if s else s for s in sentences]
        return '. '.join(capitalized)
    
    modify_hwpx_text(input_file, "example_capitalized.hwpx", capitalize_sentences)
    print("문장 첫 글자 대문자화 완료")


def example_advanced_replacement():
    """고급 텍스트 교체 예제"""
    input_file = "testFile/tool/textextractor/multipara.hwpx"
    
    # 복수 교체
    replacements = {
        "샌디에이고": "San Diego",
        "시즌": "Season", 
        "홈런": "Home Run",
        "경기": "Game"
    }
    
    def multiple_replace(text):
        for korean, english in replacements.items():
            text = text.replace(korean, english)
        return text
    
    modify_hwpx_text(input_file, "example_korean_to_english.hwpx", multiple_replace)
    print("한영 교체 완료")


def example_text_analysis():
    """텍스트 분석 예제"""
    input_file = "testFile/tool/textextractor/multipara.hwpx"
    
    stats = get_hwpx_text_stats(input_file)
    print("\n=== 텍스트 분석 결과 ===")
    print(f"총 글자 수: {stats['total_characters']:,}")
    print(f"공백 제외 글자 수: {stats['total_characters_no_spaces']:,}")
    print(f"단어 수: {stats['total_words']:,}")
    print(f"줄 수: {stats['total_lines']:,}")
    print(f"문단 수: {stats['total_paragraphs']:,}")
    
    # 평균 단어 길이 계산
    if stats['total_words'] > 0:
        avg_word_length = stats['total_characters_no_spaces'] / stats['total_words']
        print(f"평균 단어 길이: {avg_word_length:.2f}자")


def example_text_cleanup():
    """텍스트 정리 예제"""
    input_file = "testFile/tool/textextractor/multipara.hwpx"
    
    def cleanup_text(text):
        # 1. 연속된 공백 제거
        text = re.sub(r'\s+', ' ', text)
        # 2. 불필요한 특수문자 제거
        text = re.sub(r'[^\w\s가-힣.,!?()]', '', text)
        # 3. 앞뒤 공백 제거
        text = text.strip()
        return text
    
    modify_hwpx_text(input_file, "example_cleaned.hwpx", cleanup_text)
    print("텍스트 정리 완료")


if __name__ == "__main__":
    print("HWPX 텍스트 수정 예제 실행...")
    
    try:
        example_text_analysis()
        example_text_formatting()
        example_advanced_replacement() 
        example_text_cleanup()
        
        print("\n모든 예제 실행 완료!")
        print("생성된 파일들:")
        print("- example_numbers_wrapped.hwpx")
        print("- example_emails_removed.hwpx") 
        print("- example_capitalized.hwpx")
        print("- example_korean_to_english.hwpx")
        print("- example_cleaned.hwpx")
        
    except Exception as e:
        print(f"오류 발생: {e}")
