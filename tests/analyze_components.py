#!/usr/bin/env python3
"""
원본과 저장본의 모든 구성요소를 추출해서 비교 분석
"""

import zipfile
import os
from pathlib import Path

def extract_all_components(hwpx_file_path, output_dir):
    """HWPX 파일의 모든 구성요소를 개별 파일로 추출"""
    
    # 출력 디렉토리 생성
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    print(f"=== {hwpx_file_path} 구성요소 추출 ===")
    
    try:
        with zipfile.ZipFile(hwpx_file_path, 'r') as zf:
            file_list = zf.namelist()
            print(f"총 {len(file_list)}개 파일:")
            
            total_size = 0
            for filename in file_list:
                try:
                    file_data = zf.read(filename)
                    file_size = len(file_data)
                    total_size += file_size
                    
                    print(f"  {filename}: {file_size:,} bytes")
                    
                    # 파일 저장 (경로 생성)
                    safe_filename = filename.replace('/', '_').replace('\\', '_')
                    output_file = output_path / safe_filename
                    
                    with open(output_file, 'wb') as f:
                        f.write(file_data)
                        
                    # XML 파일인 경우 텍스트로도 저장
                    if filename.endswith('.xml') or filename.endswith('.hpf'):
                        try:
                            text_content = file_data.decode('utf-8')
                            text_file = output_path / f"{safe_filename}.txt"
                            with open(text_file, 'w', encoding='utf-8') as f:
                                f.write(text_content)
                        except UnicodeDecodeError:
                            pass
                            
                except Exception as e:
                    print(f"  {filename}: 추출 실패 - {e}")
            
            print(f"총 크기: {total_size:,} bytes")
            print(f"추출 완료: {output_dir}")
            return total_size
            
    except Exception as e:
        print(f"오류: {e}")
        return 0

def compare_file_sizes(original_dir, saved_dir):
    """두 디렉토리의 파일 크기 비교"""
    print(f"\\n=== 파일 크기 비교 ===")
    
    original_files = {}
    saved_files = {}
    
    # 원본 파일들 크기 수집
    for file_path in Path(original_dir).glob("*"):
        if not file_path.name.endswith('.txt'):
            original_files[file_path.name] = file_path.stat().st_size
    
    # 저장본 파일들 크기 수집
    for file_path in Path(saved_dir).glob("*"):
        if not file_path.name.endswith('.txt'):
            saved_files[file_path.name] = file_path.stat().st_size
    
    # 비교
    all_files = set(original_files.keys()) | set(saved_files.keys())
    
    print(f"{'파일명':<25} {'원본 크기':<12} {'저장본 크기':<12} {'차이':<10} {'비율'}")
    print("-" * 70)
    
    total_original = 0
    total_saved = 0
    
    for filename in sorted(all_files):
        orig_size = original_files.get(filename, 0)
        saved_size = saved_files.get(filename, 0)
        
        total_original += orig_size
        total_saved += saved_size
        
        if orig_size > 0 and saved_size > 0:
            diff = saved_size - orig_size
            ratio = (saved_size / orig_size) * 100
            status = "✅" if abs(diff) < 10 else "⚠️" if ratio > 90 else "❌"
            print(f"{filename:<25} {orig_size:<12,} {saved_size:<12,} {diff:+<10,} {ratio:>6.1f}% {status}")
        elif orig_size > 0:
            print(f"{filename:<25} {orig_size:<12,} {'누락':<12} {-orig_size:+<10,} {'0.0%':>6} ❌")
        else:
            print(f"{filename:<25} {'누락':<12} {saved_size:<12,} {saved_size:+<10,} {'∞':>6} ❌")
    
    print("-" * 70)
    total_diff = total_saved - total_original
    total_ratio = (total_saved / total_original) * 100 if total_original > 0 else 0
    print(f"{'총합':<25} {total_original:<12,} {total_saved:<12,} {total_diff:+<10,} {total_ratio:>6.1f}%")

def analyze_xml_differences(original_dir, saved_dir):
    """XML 파일들의 내용 차이 분석"""
    print(f"\\n=== XML 파일 내용 분석 ===")
    
    xml_files = []
    for file_path in Path(original_dir).glob("*.xml.txt"):
        xml_files.append(file_path.stem.replace('.xml', ''))
    
    for xml_name in xml_files:
        orig_file = Path(original_dir) / f"{xml_name}.xml.txt"
        saved_file = Path(saved_dir) / f"{xml_name}.xml.txt"
        
        if orig_file.exists() and saved_file.exists():
            print(f"\\n📄 {xml_name}.xml:")
            
            # 파일 크기 비교
            orig_size = orig_file.stat().st_size
            saved_size = saved_file.stat().st_size
            print(f"  크기: {orig_size:,} → {saved_size:,} bytes ({(saved_size/orig_size)*100:.1f}%)")
            
            # 내용 샘플 비교
            try:
                with open(orig_file, 'r', encoding='utf-8') as f:
                    orig_content = f.read()
                with open(saved_file, 'r', encoding='utf-8') as f:
                    saved_content = f.read()
                
                print(f"  원본 시작: {orig_content[:100]}...")
                print(f"  저장본 시작: {saved_content[:100]}...")
                
                # 네임스페이스 체크
                if 'xmlns:' in orig_content and 'xmlns:' not in saved_content:
                    print("  ❌ 네임스페이스 손실됨")
                elif 'xmlns:' in orig_content and 'xmlns:' in saved_content:
                    print("  ✅ 네임스페이스 보존됨")
                
            except Exception as e:
                print(f"  파일 읽기 오류: {e}")

def main():
    """메인 함수"""
    import sys
    if len(sys.argv) >= 3:
        original_file = sys.argv[1]
        saved_file = sys.argv[2]
    else:
        original_file = "../sample.hwpx"
        saved_file = "../sample_upper_token.hwpx"
    
    # 추출 디렉토리
    original_dir = "original_components"
    saved_dir = "saved_components"
    
    # 기존 디렉토리 정리
    import shutil
    for dir_path in [original_dir, saved_dir]:
        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)
    
    print("=== HWPX 파일 구성요소 비교 분석 ===\\n")
    
    # 원본 파일 추출
    if os.path.exists(original_file):
        original_total = extract_all_components(original_file, original_dir)
    else:
        print(f"❌ 원본 파일이 없습니다: {original_file}")
        return
    
    print()
    
    # 저장본 파일 추출
    if os.path.exists(saved_file):
        saved_total = extract_all_components(saved_file, saved_dir)
    else:
        print(f"❌ 저장본 파일이 없습니다: {saved_file}")
        return
    
    # 비교 분석
    compare_file_sizes(original_dir, saved_dir)
    analyze_xml_differences(original_dir, saved_dir)
    
    print(f"\\n=== 분석 완료 ===")
    print(f"원본 구성요소: {original_dir}/ 디렉토리")
    print(f"저장본 구성요소: {saved_dir}/ 디렉토리")
    print(f"각 파일들을 직접 열어서 내용을 비교해보세요.")

if __name__ == "__main__":
    main()
