#!/usr/bin/env python3
"""
시간별로 저장된 데이터 파일들 중 하루에 하나만 남기고 나머지는 이동시키는 스크립트

파일 패턴:
- YYYYMMDD_HHMMSS_AE_.dat (약 40MB)
- YYYYMMDD_HHMMSS_AE_Audible.dat (약 13KB)
- YYYYMMDD_HHMMSS_Vib.dat 또는 _Vib_.dat (약 2MB)

사용법:
    python consolidate_hourly_data.py /path/to/data/directory [--dry-run] [--move-dir DIRNAME]

옵션:
    --dry-run       실제로 파일을 이동하지 않고 어떤 작업이 수행될지만 보여줍니다
    --move-dir      이동할 폴더 이름 (기본: hourly_backup)
    --keep          남길 파일 선택: first(첫번째), last(마지막) (기본: first)
"""

import os
import sys
import re
import argparse
from collections import defaultdict
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
            files_grouped[(date_str, file_type)].append((time_str, filepath, filename))
    
    # 각 그룹 내에서 시간순으로 정렬
    for key in files_grouped:
        files_grouped[key].sort(key=lambda x: x[0])
    
    return files_grouped


def format_size(size_bytes):
    """바이트를 사람이 읽기 쉬운 형식으로 변환"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} TB"


def main():
    parser = argparse.ArgumentParser(
        description='시간별로 저장된 데이터 파일들 중 하루에 하나만 남기고 나머지는 이동시킵니다.'
    )
    parser.add_argument('directory', help='데이터 파일이 있는 디렉토리 경로')
    parser.add_argument('--dry-run', action='store_true', 
                        help='실제로 파일을 이동하지 않고 어떤 작업이 수행될지만 보여줍니다')
    parser.add_argument('--move-dir', default='hourly_backup',
                        help='이동할 폴더 이름 (기본: hourly_backup)')
    parser.add_argument('--keep', choices=['first', 'last'], default='first',
                        help='남길 파일 선택: first(첫번째), last(마지막) (기본: first)')
    
    args = parser.parse_args()
    
    if not os.path.isdir(args.directory):
        print(f"오류: '{args.directory}'는 유효한 디렉토리가 아닙니다.")
        sys.exit(1)
    
    move_dir = os.path.join(args.directory, args.move_dir)
    
    print(f"\n{'='*60}")
    print(f"데이터 파일 정리 스크립트")
    print(f"{'='*60}")
    print(f"입력 디렉토리: {args.directory}")
    print(f"이동 디렉토리: {move_dir}")
    print(f"남길 파일: {'첫 번째 (가장 이른 시간)' if args.keep == 'first' else '마지막 (가장 늦은 시간)'}")
    print(f"모드: {'DRY RUN (시뮬레이션)' if args.dry_run else '실제 실행'}")
    print(f"{'='*60}\n")
    
    # 파일 그룹화
    files_grouped = get_files_by_date_and_type(args.directory)
    
    if not files_grouped:
        print("처리할 파일을 찾을 수 없습니다.")
        sys.exit(0)
    
    # 이동 폴더 생성
    if not args.dry_run and not os.path.exists(move_dir):
        os.makedirs(move_dir)
        print(f"이동 폴더 생성: {move_dir}\n")
    
    total_kept = 0
    total_moved = 0
    total_moved_size = 0
    
    for (date_str, file_type), files in sorted(files_grouped.items()):
        if len(files) <= 1:
            print(f"[{date_str}] {file_type}: 파일 1개 - 이동 필요 없음")
            total_kept += 1
            continue
        
        # 남길 파일과 이동할 파일 결정
        if args.keep == 'first':
            keep_file = files[0]
            move_files = files[1:]
        else:  # last
            keep_file = files[-1]
            move_files = files[:-1]
        
        print(f"\n[{date_str}] {file_type} 타입:")
        print(f"  ✓ 유지: {keep_file[2]} ({format_size(os.path.getsize(keep_file[1]))})")
        
        for time_str, filepath, filename in move_files:
            size = os.path.getsize(filepath)
            print(f"  → 이동: {filename} ({format_size(size)})")
            
            if not args.dry_run:
                dest_path = os.path.join(move_dir, filename)
                shutil.move(filepath, dest_path)
            
            total_moved += 1
            total_moved_size += size
        
        total_kept += 1
    
    print(f"\n{'='*60}")
    print(f"작업 요약:")
    print(f"  유지된 파일 그룹: {total_kept}")
    print(f"  이동된 파일 수: {total_moved}")
    print(f"  이동된 총 크기: {format_size(total_moved_size)}")
    if args.dry_run:
        print(f"\n  ※ DRY RUN 모드였습니다. 실제로 변경된 것은 없습니다.")
        print(f"  ※ 실제 실행하려면 --dry-run 옵션을 제거하세요.")
    else:
        print(f"\n  ※ 이동된 파일들은 '{move_dir}'에 있습니다.")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    main()
