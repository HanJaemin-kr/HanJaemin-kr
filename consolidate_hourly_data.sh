#!/bin/bash
#
# 시간별로 저장된 데이터 파일들 중 하루에 하나만 남기고 나머지는 이동시키는 스크립트
#
# 사용법:
#   ./consolidate_hourly_data.sh <기본경로> <폴더선택|all> [--dry-run]
#
# 예시:
#   ./consolidate_hourly_data.sh /data all --dry-run        # 모든 폴더 dry-run
#   ./consolidate_hourly_data.sh /data all                  # 모든 폴더 실제 실행
#   ./consolidate_hourly_data.sh /data "1구간 (롯데정밀화학)" --dry-run  # 특정 폴더
#   ./consolidate_hourly_data.sh /data list                 # 폴더 목록만 보기
#
# 백업 폴더 구조:
#   기본경로/backup/폴더이름/파일들
#

BASE_DIR="$1"
FOLDER_SELECT="$2"
DRY_RUN=false
BACKUP_BASE="backup"

# dry-run 체크
if [ "$3" == "--dry-run" ] || [ "$2" == "--dry-run" ]; then
    DRY_RUN=true
fi

# 인자 확인
if [ -z "$BASE_DIR" ]; then
    echo ""
    echo "사용법: $0 <기본경로> <폴더선택|all|list> [--dry-run]"
    echo ""
    echo "예시:"
    echo "  $0 /data list                           # 폴더 목록 보기"
    echo "  $0 /data all --dry-run                  # 모든 폴더 시뮬레이션"
    echo "  $0 /data all                            # 모든 폴더 실제 실행"
    echo "  $0 /data \"1구간 (롯데정밀화학)\" --dry-run  # 특정 폴더 시뮬레이션"
    echo ""
    echo "백업 폴더 구조:"
    echo "  기본경로/backup/폴더이름/파일들"
    echo ""
    exit 1
fi

if [ ! -d "$BASE_DIR" ]; then
    echo "오류: '$BASE_DIR'는 유효한 디렉토리가 아닙니다."
    exit 1
fi

# 폴더 목록 보기
if [ "$FOLDER_SELECT" == "list" ]; then
    echo ""
    echo "============================================================"
    echo "사용 가능한 폴더 목록:"
    echo "============================================================"
    ls -1 "$BASE_DIR" | grep -E "^[0-9]+.*구간" | sort -t'구' -k1 -n
    echo "============================================================"
    echo ""
    exit 0
fi

if [ -z "$FOLDER_SELECT" ]; then
    echo ""
    echo "오류: 폴더를 선택하세요 (all 또는 특정 폴더명)"
    echo "폴더 목록을 보려면: $0 $BASE_DIR list"
    echo ""
    exit 1
fi

# 처리할 폴더 목록 생성
declare -a FOLDERS_TO_PROCESS

if [ "$FOLDER_SELECT" == "all" ]; then
    while IFS= read -r folder; do
        FOLDERS_TO_PROCESS+=("$folder")
    done < <(ls -1 "$BASE_DIR" | grep -E "^[0-9]+.*구간")
else
    if [ -d "$BASE_DIR/$FOLDER_SELECT" ]; then
        FOLDERS_TO_PROCESS+=("$FOLDER_SELECT")
    else
        echo "오류: '$BASE_DIR/$FOLDER_SELECT' 폴더를 찾을 수 없습니다."
        echo "폴더 목록을 보려면: $0 $BASE_DIR list"
        exit 1
    fi
fi

BACKUP_ROOT="$BASE_DIR/$BACKUP_BASE"

echo ""
echo "============================================================"
echo "데이터 파일 정리 스크립트"
echo "============================================================"
echo "기본 경로: $BASE_DIR"
echo "백업 경로: $BACKUP_ROOT"
echo "처리할 폴더 수: ${#FOLDERS_TO_PROCESS[@]}"
if [ "$DRY_RUN" = true ]; then
    echo "모드: DRY RUN (시뮬레이션)"
else
    echo "모드: 실제 실행"
fi
echo "============================================================"

# 백업 루트 폴더 생성
if [ "$DRY_RUN" = false ] && [ ! -d "$BACKUP_ROOT" ]; then
    mkdir -p "$BACKUP_ROOT"
    echo "백업 루트 폴더 생성: $BACKUP_ROOT"
fi

# 폴더별 처리 함수
process_folder() {
    local DATA_DIR="$1"
    local FOLDER_NAME="$2"
    local BACKUP_DIR="$BACKUP_ROOT/$FOLDER_NAME"
    
    local folder_kept=0
    local folder_moved=0
    
    echo ""
    echo "############################################################"
    echo "# 처리 중: $FOLDER_NAME"
    echo "############################################################"
    echo "# 원본: $DATA_DIR"
    echo "# 백업: $BACKUP_DIR"
    echo "############################################################"
    
    # 백업 폴더 생성
    if [ "$DRY_RUN" = false ] && [ ! -d "$BACKUP_DIR" ]; then
        mkdir -p "$BACKUP_DIR"
        echo "백업 폴더 생성: $BACKUP_DIR"
    fi
    
    # AE_.dat 파일 처리
    echo ""
    echo "=== AE_.dat 파일 처리 ==="
    for date in $(ls "$DATA_DIR" 2>/dev/null | grep -E '^[0-9]{8}_[0-9]{6}_AE_\.dat$' | cut -c1-8 | sort -u); do
        files=($(ls "$DATA_DIR" 2>/dev/null | grep -E "^${date}_[0-9]{6}_AE_\.dat$" | sort))
        
        if [ ${#files[@]} -eq 0 ]; then
            continue
        fi
        
        if [ ${#files[@]} -le 1 ]; then
            echo "[$date] AE_: 파일 1개 - 이동 필요 없음"
            ((folder_kept++))
            continue
        fi
        
        echo ""
        echo "[$date] AE_ 타입 (${#files[@]}개):"
        echo "  ✓ 유지: ${files[0]}"
        
        for ((i=1; i<${#files[@]}; i++)); do
            echo "  → 이동: ${files[$i]}"
            if [ "$DRY_RUN" = false ]; then
                mv "$DATA_DIR/${files[$i]}" "$BACKUP_DIR/"
            fi
            ((folder_moved++))
        done
        ((folder_kept++))
    done
    
    # AE_Audible.dat 파일 처리
    echo ""
    echo "=== AE_Audible.dat 파일 처리 ==="
    for date in $(ls "$DATA_DIR" 2>/dev/null | grep -E '^[0-9]{8}_[0-9]{6}_AE_Audible\.dat$' | cut -c1-8 | sort -u); do
        files=($(ls "$DATA_DIR" 2>/dev/null | grep -E "^${date}_[0-9]{6}_AE_Audible\.dat$" | sort))
        
        if [ ${#files[@]} -eq 0 ]; then
            continue
        fi
        
        if [ ${#files[@]} -le 1 ]; then
            echo "[$date] AE_Audible: 파일 1개 - 이동 필요 없음"
            ((folder_kept++))
            continue
        fi
        
        echo ""
        echo "[$date] AE_Audible 타입 (${#files[@]}개):"
        echo "  ✓ 유지: ${files[0]}"
        
        for ((i=1; i<${#files[@]}; i++)); do
            echo "  → 이동: ${files[$i]}"
            if [ "$DRY_RUN" = false ]; then
                mv "$DATA_DIR/${files[$i]}" "$BACKUP_DIR/"
            fi
            ((folder_moved++))
        done
        ((folder_kept++))
    done
    
    # Vib 파일 처리 (Vib_.dat 및 Vib.dat 모두)
    echo ""
    echo "=== Vib.dat / Vib_.dat 파일 처리 ==="
    for date in $(ls "$DATA_DIR" 2>/dev/null | grep -E '^[0-9]{8}_[0-9]{6}_Vib' | cut -c1-8 | sort -u); do
        files=($(ls "$DATA_DIR" 2>/dev/null | grep -E "^${date}_[0-9]{6}_Vib" | sort))
        
        if [ ${#files[@]} -eq 0 ]; then
            continue
        fi
        
        if [ ${#files[@]} -le 1 ]; then
            echo "[$date] Vib: 파일 1개 - 이동 필요 없음"
            ((folder_kept++))
            continue
        fi
        
        echo ""
        echo "[$date] Vib 타입 (${#files[@]}개):"
        echo "  ✓ 유지: ${files[0]}"
        
        for ((i=1; i<${#files[@]}; i++)); do
            echo "  → 이동: ${files[$i]}"
            if [ "$DRY_RUN" = false ]; then
                mv "$DATA_DIR/${files[$i]}" "$BACKUP_DIR/"
            fi
            ((folder_moved++))
        done
        ((folder_kept++))
    done
    
    echo ""
    echo "[$FOLDER_NAME] 요약: 유지 $folder_kept 그룹, 이동 $folder_moved 파일"
    
    # 전역 카운터 업데이트
    ((total_kept+=folder_kept))
    ((total_moved+=folder_moved))
}

# 전역 카운터
total_kept=0
total_moved=0

# 각 폴더 처리
for folder in "${FOLDERS_TO_PROCESS[@]}"; do
    process_folder "$BASE_DIR/$folder" "$folder"
done

echo ""
echo "============================================================"
echo "전체 작업 요약:"
echo "============================================================"
echo "  처리된 폴더 수: ${#FOLDERS_TO_PROCESS[@]}"
echo "  유지된 파일 그룹: $total_kept"
echo "  이동된 파일 수: $total_moved"
if [ "$DRY_RUN" = true ]; then
    echo ""
    echo "  ※ DRY RUN 모드였습니다. 실제로 변경된 것은 없습니다."
    echo "  ※ 실제 실행하려면 --dry-run 옵션을 제거하세요."
else
    echo ""
    echo "  ※ 이동된 파일들은 '$BACKUP_ROOT/폴더이름/' 에 있습니다."
fi
echo "============================================================"
echo ""
