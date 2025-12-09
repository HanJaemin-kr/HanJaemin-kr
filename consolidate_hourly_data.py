#!/usr/bin/env python3
"""
시간별로 저장된 데이터 파일들을 하루 단위로 통합하는 스크립트

파일 패턴:
- YYYYMMDD_HHMMSS_AE_.dat (약 40MB)
- YYYYMMDD_HHMMSS_AE_Audible.dat (약 13KB)
- YYYYMMDD_HHMMSS_Vib.dat 또는 _Vib_.dat (약 2MB)

사용법:
    python consolidate_hourly_data.py /path/to/data/directory [--dry-run] [--backup]

옵션:
    --dry-run   실제로 파일을 합치지 않고 어떤 작업이 수행될지만 보여줍니다
    --backup    원본 파일들을 backup 폴더로 이동합니다 (기본: 삭제하지 않음)
    --delete    통합 후 원본 파일들을 삭제합니다
"""

import os
import sys
import re
import argparse
from collections import defaultdict
from datetime import datetime
import shutil


def parse_filename(filename):
    """
    파일명을 파싱하여 날짜, 시간, 타입을 추출합니다.
    
    Returns:
        tuple: (date_str, time_str, file_type) 또는 파싱 실패시 None
    """
    # AE_.dat 파일 패턴: YYYYMMDD_HHMMSS_AE_.dat
    ae_pattern = r'^(\d{8})_(\d{6})_AE_\.dat$'
    # AE_Audible.dat 파일 패턴: YYYYMMDD_HHMMSS_AE_Audible.dat
    audible_pattern = r'^(\d{8})_(\d{6})_AE_Audible\.dat$'
    # Vib.dat 파일 패턴: YYYYMMDD_HHMMSS_Vib.dat 또는 YYYYMMDD_HHMMSS_Vib.dat_Vib_.dat
    vib_pattern = r'^(\d{8})_(\d{6})_Vib\.dat(?:_Vib_\.dat)?$'
    
    match = re.match(ae_pattern, filename)
    if match:
        return (match.group(1), match.group(2), 'AE')
    
    match = re.match(audible_pattern, filename)
    if match:
        return (match.group(1), match.group(2), 'AE_Audible')
    
    match = re.match(vib_pattern, filename)
    if match:
        return (match.group(1), match.group(2), 'Vib')
    
    return None


def get_files_by_date_and_type(directory):
    """
    디렉토리의 파일들을 날짜와 타입별로 그룹화합니다.
    
    Returns:
        dict: {(date, type): [(time, filepath), ...]}
    """
    files_grouped = defaultdict(list)
    
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if not os.path.isfile(filepath):
            continue
            
        parsed = parse_filename(filename)
        if parsed:
            date_str, time_str, file_type = parsed
            files_grouped[(date_str, file_type)].append((time_str, filepath))
    
    # 각 그룹 내에서 시간순으로 정렬
    for key in files_grouped:
        files_grouped[key].sort(key=lambda x: x[0])
    
    return files_grouped


def consolidate_files(files, output_path, dry_run=False):
    """
    여러 파일을 하나로 합칩니다.
    
    Args:
        files: [(time, filepath), ...] 시간순 정렬된 파일 목록
        output_path: 출력 파일 경로
        dry_run: True면 실제 작업 수행하지 않음
    
    Returns:
        int: 합쳐진 총 바이트 수
    """
    total_size = 0
    
    if dry_run:
        for time_str, filepath in files:
            size = os.path.getsize(filepath)
            total_size += size
        return total_size
    
    with open(output_path, 'wb') as outfile:
        for time_str, filepath in files:
            with open(filepath, 'rb') as infile:
                data = infile.read()
                outfile.write(data)
                total_size += len(data)
    
    return total_size


def format_size(size_bytes):
    """바이트를 사람이 읽기 쉬운 형식으로 변환"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} TB"


def main():
    parser = argparse.ArgumentParser(
        description='시간별로 저장된 데이터 파일들을 하루 단위로 통합합니다.'
    )
    parser.add_argument('directory', help='데이터 파일이 있는 디렉토리 경로')
    parser.add_argument('--dry-run', action='store_true', 
                        help='실제로 파일을 합치지 않고 어떤 작업이 수행될지만 보여줍니다')
    parser.add_argument('--backup', action='store_true',
                        help='원본 파일들을 backup 폴더로 이동합니다')
    parser.add_argument('--delete', action='store_true',
                        help='통합 후 원본 파일들을 삭제합니다')
    parser.add_argument('--output-dir', default=None,
                        help='통합된 파일을 저장할 디렉토리 (기본: 원본과 같은 디렉토리)')
    
    args = parser.parse_args()
    
    if not os.path.isdir(args.directory):
        print(f"오류: '{args.directory}'는 유효한 디렉토리가 아닙니다.")
        sys.exit(1)
    
    if args.backup and args.delete:
        print("오류: --backup과 --delete는 동시에 사용할 수 없습니다.")
        sys.exit(1)
    
    output_dir = args.output_dir or args.directory
    if not os.path.exists(output_dir):
        if not args.dry_run:
            os.makedirs(output_dir)
        print(f"출력 디렉토리 생성: {output_dir}")
    
    print(f"\n{'='*60}")
    print(f"데이터 파일 통합 스크립트")
    print(f"{'='*60}")
    print(f"입력 디렉토리: {args.directory}")
    print(f"출력 디렉토리: {output_dir}")
    print(f"모드: {'DRY RUN (시뮬레이션)' if args.dry_run else '실제 실행'}")
    if args.backup:
        print("원본 파일: backup 폴더로 이동")
    elif args.delete:
        print("원본 파일: 삭제")
    else:
        print("원본 파일: 유지")
    print(f"{'='*60}\n")
    
    # 파일 그룹화
    files_grouped = get_files_by_date_and_type(args.directory)
    
    if not files_grouped:
        print("통합할 파일을 찾을 수 없습니다.")
        sys.exit(0)
    
    # 통합 작업 수행
    file_type_extensions = {
        'AE': 'AE_.dat',
        'AE_Audible': 'AE_Audible.dat',
        'Vib': 'Vib.dat'
    }
    
    backup_dir = os.path.join(args.directory, 'backup_hourly')
    
    total_consolidated = 0
    total_original_files = 0
    
    for (date_str, file_type), files in sorted(files_grouped.items()):
        if len(files) <= 1:
            print(f"[건너뛰기] {date_str} {file_type}: 파일이 1개뿐입니다.")
            continue
        
        # 첫 번째 파일의 시간을 사용하여 출력 파일명 생성
        first_time = files[0][0]
        ext = file_type_extensions.get(file_type, f'{file_type}.dat')
        output_filename = f"{date_str}_{first_time}_{ext}"
        output_path = os.path.join(output_dir, output_filename)
        
        print(f"\n[{date_str}] {file_type} 타입 통합:")
        print(f"  파일 개수: {len(files)}")
        
        # 원본 파일 정보 출력
        total_input_size = 0
        for time_str, filepath in files:
            size = os.path.getsize(filepath)
            total_input_size += size
            print(f"    - {os.path.basename(filepath)} ({format_size(size)})")
        
        print(f"  총 입력 크기: {format_size(total_input_size)}")
        print(f"  출력 파일: {output_filename}")
        
        if not args.dry_run:
            # 파일 통합
            consolidated_size = consolidate_files(files, output_path)
            print(f"  통합 완료: {format_size(consolidated_size)}")
            
            # 원본 파일 처리
            if args.backup:
                if not os.path.exists(backup_dir):
                    os.makedirs(backup_dir)
                for time_str, filepath in files:
                    backup_path = os.path.join(backup_dir, os.path.basename(filepath))
                    shutil.move(filepath, backup_path)
                print(f"  원본 파일들을 backup 폴더로 이동했습니다.")
            elif args.delete:
                for time_str, filepath in files:
                    os.remove(filepath)
                print(f"  원본 파일들을 삭제했습니다.")
        else:
            print(f"  [DRY RUN] 통합 예정 크기: {format_size(total_input_size)}")
        
        total_consolidated += 1
        total_original_files += len(files)
    
    print(f"\n{'='*60}")
    print(f"작업 요약:")
    print(f"  통합된 그룹 수: {total_consolidated}")
    print(f"  처리된 원본 파일 수: {total_original_files}")
    if args.dry_run:
        print(f"\n  ※ DRY RUN 모드였습니다. 실제로 변경된 것은 없습니다.")
        print(f"  ※ 실제 실행하려면 --dry-run 옵션을 제거하세요.")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    main()
