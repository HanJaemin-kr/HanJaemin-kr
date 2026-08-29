#!/usr/bin/env python3
"""
시간별로 저장된 .dat 파일들을 하루 단위로 합치는 스크립트

파일명 형식: YYYYMMDD_HHMMSS_TYPE.dat
예: 20251206_170008_AE_.dat, 20251206_180007_AE_.dat -> 20251206_AE_.dat

사용법:
    python consolidate_hourly_data.py <입력_디렉토리> [출력_디렉토리]
    
    출력_디렉토리가 지정되지 않으면 입력_디렉토리/consolidated 에 저장됩니다.
"""

import os
import sys
import re
from collections import defaultdict
from pathlib import Path


def parse_filename(filename):
    """
    파일명을 파싱하여 날짜, 시간, 타입을 추출합니다.
    
    예: 20251206_170008_AE_.dat -> (20251206, 170008, AE_)
        20251206_170008_AE_Audible.dat -> (20251206, 170008, AE_Audible)
        20251209_135924_Vib.dat_Vib_.dat -> (20251209, 135924, Vib.dat_Vib_)
        20251209_155926_Vib.dat -> (20251209, 155926, Vib)
    """
    # 파일명에서 .dat 확장자 제거
    base = filename
    if base.endswith('.dat'):
        base = base[:-4]
    
    # YYYYMMDD_HHMMSS_TYPE 형식 파싱
    # 패턴: 8자리 날짜 + _ + 6자리 시간 + _ + 나머지(타입)
    pattern = r'^(\d{8})_(\d{6})_(.+)$'
    match = re.match(pattern, base)
    
    if match:
        date = match.group(1)
        time = match.group(2)
        file_type = match.group(3)
        return date, time, file_type
    
    return None, None, None


def get_file_type_category(file_type):
    """
    파일 타입을 카테고리로 분류합니다.
    
    - AE_ -> AE_
    - AE_Audible -> AE_Audible
    - Vib, Vib_, Vib.dat_Vib_ -> Vib
    """
    if 'Audible' in file_type:
        return 'AE_Audible'
    elif file_type.startswith('AE'):
        return 'AE_'
    elif 'Vib' in file_type:
        return 'Vib'
    else:
        return file_type


def consolidate_files(input_dir, output_dir=None, dry_run=False):
    """
    입력 디렉토리의 파일들을 날짜+타입별로 그룹화하여 합칩니다.
    
    Args:
        input_dir: 입력 디렉토리 경로
        output_dir: 출력 디렉토리 경로 (None이면 input_dir/consolidated)
        dry_run: True면 실제 작업 없이 계획만 출력
    """
    input_path = Path(input_dir)
    
    if not input_path.exists():
        print(f"오류: 입력 디렉토리가 존재하지 않습니다: {input_dir}")
        sys.exit(1)
    
    if output_dir is None:
        output_path = input_path / 'consolidated'
    else:
        output_path = Path(output_dir)
    
    # 파일들을 (날짜, 타입) 별로 그룹화
    file_groups = defaultdict(list)
    
    for filename in os.listdir(input_path):
        if not filename.endswith('.dat'):
            continue
        
        filepath = input_path / filename
        if not filepath.is_file():
            continue
        
        date, time, file_type = parse_filename(filename)
        
        if date is None:
            print(f"경고: 파싱 실패, 건너뜀: {filename}")
            continue
        
        category = get_file_type_category(file_type)
        key = (date, category)
        file_groups[key].append((time, filename, filepath))
    
    if not file_groups:
        print("처리할 .dat 파일이 없습니다.")
        return
    
    # 결과 출력
    print(f"\n{'='*60}")
    print(f"파일 통합 계획")
    print(f"{'='*60}")
    print(f"입력 디렉토리: {input_path.absolute()}")
    print(f"출력 디렉토리: {output_path.absolute()}")
    print(f"{'='*60}\n")
    
    # 각 그룹별로 정보 출력
    total_input_files = 0
    total_output_files = 0
    
    for key in sorted(file_groups.keys()):
        date, category = key
        files = sorted(file_groups[key])  # 시간순 정렬
        
        total_input_files += len(files)
        total_output_files += 1
        
        output_filename = f"{date}_{category}.dat"
        total_size = sum(f[2].stat().st_size for f in files)
        
        print(f"\n[{date}] {category}")
        print(f"  출력 파일: {output_filename}")
        print(f"  입력 파일 수: {len(files)}")
        print(f"  예상 크기: {total_size / (1024*1024):.2f} MB")
        print(f"  포함 파일:")
        for time, fname, fpath in files:
            size = fpath.stat().st_size
            print(f"    - {fname} ({size / (1024*1024):.2f} MB)")
    
    print(f"\n{'='*60}")
    print(f"요약: {total_input_files}개 파일 -> {total_output_files}개 파일")
    print(f"{'='*60}\n")
    
    if dry_run:
        print("--dry-run 모드: 실제 작업은 수행되지 않았습니다.")
        return
    
    # 사용자 확인
    response = input("계속 진행하시겠습니까? (y/N): ")
    if response.lower() != 'y':
        print("작업이 취소되었습니다.")
        return
    
    # 출력 디렉토리 생성
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 파일 합치기
    print("\n파일 통합 중...")
    
    for key in sorted(file_groups.keys()):
        date, category = key
        files = sorted(file_groups[key])  # 시간순 정렬
        
        output_filename = f"{date}_{category}.dat"
        output_filepath = output_path / output_filename
        
        print(f"  생성 중: {output_filename}...", end=" ", flush=True)
        
        with open(output_filepath, 'wb') as outfile:
            for time, fname, fpath in files:
                with open(fpath, 'rb') as infile:
                    # 큰 파일을 위해 청크 단위로 복사
                    while True:
                        chunk = infile.read(1024 * 1024)  # 1MB 청크
                        if not chunk:
                            break
                        outfile.write(chunk)
        
        final_size = output_filepath.stat().st_size
        print(f"완료 ({final_size / (1024*1024):.2f} MB)")
    
    print(f"\n통합 완료! 결과는 {output_path.absolute()} 에 저장되었습니다.")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("\n사용 예시:")
        print("  python consolidate_hourly_data.py /path/to/data")
        print("  python consolidate_hourly_data.py /path/to/data /path/to/output")
        print("  python consolidate_hourly_data.py /path/to/data --dry-run")
        sys.exit(1)
    
    input_dir = sys.argv[1]
    output_dir = None
    dry_run = False
    
    for arg in sys.argv[2:]:
        if arg == '--dry-run':
            dry_run = True
        else:
            output_dir = arg
    
    consolidate_files(input_dir, output_dir, dry_run)


if __name__ == '__main__':
    main()
