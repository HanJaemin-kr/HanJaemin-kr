#!/bin/bash
#
# 시간별로 저장된 데이터 파일들 중 하루에 하나만 남기고 나머지는 이동시키는 스크립트
#
# 사용법:
#   ./consolidate_hourly_data.sh /path/to/data [--dry-run]
#
# 옵션:
#   --dry-run   실제로 파일을 이동하지 않고 어떤 작업이 수행될지만 보여줍니다
#

DATA_DIR="$1"
DRY_RUN=false
MOVE_DIR="hourly_backup"

# 인자 확인
if [ -z "$DATA_DIR" ]; then
    echo "사용법: $0 /path/to/data [--dry-run]"
    exit 1
fi

if [ "$2" == "--dry-run" ]; then
    DRY_RUN=true
fi

if [ ! -d "$DATA_DIR" ]; then
    echo "오류: '$DATA_DIR'는 유효한 디렉토리가 아닙니다."
    exit 1
fi

BACKUP_DIR="$DATA_DIR/$MOVE_DIR"

echo ""
echo "============================================================"
echo "데이터 파일 정리 스크립트"
echo "============================================================"
echo "입력 디렉토리: $DATA_DIR"
echo "이동 디렉토리: $BACKUP_DIR"
if [ "$DRY_RUN" = true ]; then
    echo "모드: DRY RUN (시뮬레이션)"
else
    echo "모드: 실제 실행"
fi
echo "============================================================"
echo ""

# 이동 폴더 생성
if [ "$DRY_RUN" = false ] && [ ! -d "$BACKUP_DIR" ]; then
    mkdir -p "$BACKUP_DIR"
    echo "이동 폴더 생성: $BACKUP_DIR"
    echo ""
fi

total_kept=0
total_moved=0

# AE_.dat 파일 처리
echo "=== AE_.dat 파일 처리 ==="
for date in $(ls "$DATA_DIR" | grep -E '^[0-9]{8}_[0-9]{6}_AE_\.dat$' | cut -c1-8 | sort -u); do
    files=($(ls "$DATA_DIR" | grep -E "^${date}_[0-9]{6}_AE_\.dat$" | sort))
    
    if [ ${#files[@]} -le 1 ]; then
        echo "[$date] AE_: 파일 1개 - 이동 필요 없음"
        ((total_kept++))
        continue
    fi
    
    echo ""
    echo "[$date] AE_ 타입:"
    echo "  ✓ 유지: ${files[0]}"
    
    for ((i=1; i<${#files[@]}; i++)); do
        echo "  → 이동: ${files[$i]}"
        if [ "$DRY_RUN" = false ]; then
            mv "$DATA_DIR/${files[$i]}" "$BACKUP_DIR/"
        fi
        ((total_moved++))
    done
    ((total_kept++))
done

echo ""
echo "=== AE_Audible.dat 파일 처리 ==="
for date in $(ls "$DATA_DIR" | grep -E '^[0-9]{8}_[0-9]{6}_AE_Audible\.dat$' | cut -c1-8 | sort -u); do
    files=($(ls "$DATA_DIR" | grep -E "^${date}_[0-9]{6}_AE_Audible\.dat$" | sort))
    
    if [ ${#files[@]} -le 1 ]; then
        echo "[$date] AE_Audible: 파일 1개 - 이동 필요 없음"
        ((total_kept++))
        continue
    fi
    
    echo ""
    echo "[$date] AE_Audible 타입:"
    echo "  ✓ 유지: ${files[0]}"
    
    for ((i=1; i<${#files[@]}; i++)); do
        echo "  → 이동: ${files[$i]}"
        if [ "$DRY_RUN" = false ]; then
            mv "$DATA_DIR/${files[$i]}" "$BACKUP_DIR/"
        fi
        ((total_moved++))
    done
    ((total_kept++))
done

echo ""
echo "=== Vib.dat 파일 처리 ==="
for date in $(ls "$DATA_DIR" | grep -E '^[0-9]{8}_[0-9]{6}_Vib\.dat' | cut -c1-8 | sort -u); do
    files=($(ls "$DATA_DIR" | grep -E "^${date}_[0-9]{6}_Vib\.dat" | sort))
    
    if [ ${#files[@]} -le 1 ]; then
        echo "[$date] Vib: 파일 1개 - 이동 필요 없음"
        ((total_kept++))
        continue
    fi
    
    echo ""
    echo "[$date] Vib 타입:"
    echo "  ✓ 유지: ${files[0]}"
    
    for ((i=1; i<${#files[@]}; i++)); do
        echo "  → 이동: ${files[$i]}"
        if [ "$DRY_RUN" = false ]; then
            mv "$DATA_DIR/${files[$i]}" "$BACKUP_DIR/"
        fi
        ((total_moved++))
    done
    ((total_kept++))
done

echo ""
echo "============================================================"
echo "작업 요약:"
echo "  유지된 파일 그룹: $total_kept"
echo "  이동된 파일 수: $total_moved"
if [ "$DRY_RUN" = true ]; then
    echo ""
    echo "  ※ DRY RUN 모드였습니다. 실제로 변경된 것은 없습니다."
    echo "  ※ 실제 실행하려면 --dry-run 옵션을 제거하세요."
else
    echo ""
    echo "  ※ 이동된 파일들은 '$BACKUP_DIR'에 있습니다."
fi
echo "============================================================"
echo ""
