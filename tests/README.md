# Tests Directory

이 디렉토리에는 hwpxlib의 모든 테스트 파일들이 포함되어 있습니다.

## 테스트 구조

### 단계별 검증 테스트
- `step1_validate_originals.py` - 원본 HWPX 파일 유효성 검증
- `step2_test_reader.py` - HWPXReader 기능 테스트  
- `step3_test_writer.py` - HwpxWriter 기능 테스트
- `step4_debug_text_modifier.py` - 텍스트 수정 기능 디버깅
- `step5_compare_xml.py` - XML 비교 분석
- `step6_hwp_compatibility.py` - 한글 프로그램 호환성 검증
- `step7_test_compatible.py` - 호환성 개선된 저장 테스트

### 기능별 테스트
- `test_reader_writer.py` - 기본 읽기/쓰기 기능 테스트
- `test_roundtrip.py` - 라운드트립 테스트
- `test_save_only.py` - 저장 전용 테스트
- `test_multiple_files.py` - 다중 파일 테스트

### 통합 테스트
- `final_test.py` - 최종 통합 테스트

### 실험적 기능
- `text_modifier_fixed.py` - 수정된 텍스트 모디파이어
- `text_modifier_binary.py` - 바이너리 복사 기반 텍스트 모디파이어
- `text_modifier_examples.py` - 텍스트 모디파이어 사용 예제

## 실행 방법

```bash
# 개별 테스트 실행
cd tests
python3 step1_validate_originals.py

# 전체 단계별 테스트 실행
python3 step1_validate_originals.py
python3 step2_test_reader.py
python3 step3_test_writer.py
# ...

# 최종 테스트
python3 final_test.py
```

## 테스트 데이터

테스트는 `../testFile/reader_writer/` 디렉토리의 샘플 HWPX 파일들을 사용합니다:
- `sample1.hwpx` - 기본 텍스트 문서
- `SimpleTable.hwpx` - 표가 포함된 문서  
- `SimplePicture.hwpx` - 이미지가 포함된 문서
