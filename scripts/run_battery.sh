#!/bin/bash
# ==============================================================================
# Robustness Battery 
# ==============================================================================
# B1 (heuristic sweep):  A/C × {s,S,c,C,p} × 3 counter-balanced reps @ 300s
# B2 (phase timing):     derivation-check phase timing captured for every run
#
# Total design: 2 variants × 5 heuristics × 3 reps = 30 runs
# Worst-case time budget:
#   raw (A)     5 × 3 × 300s = 4500s = 75 min  (expected: all 15 timeout)
#   carrier (C) 5 × 3 × ~80s  = 1200s = 20 min (expected: all 15 verified)
# Total ≈ 95 min wall-clock (well within 2.5h target).
#
# Environment requirements:
#   - tamarin-prover 1.10.0 or 1.12.0 on PATH (recommend 1.12.0 to match the frozen baseline)
#   - maude 3.4+ on PATH
#   - Physical RAM ≥ 8 GiB (past runs peak at 6.2 GiB on A_raw)
#   - GNU coreutils (/usr/bin/time -v)
#   - Not run inside a memory-capped container/sandbox
#
# Reproduces the exact command line used for the timeout-curve measurements:
#   tamarin-prover --diff --prove --heuristic=<H> --stop-on-trace=dfs \
#     --derivcheck-timeout=30 <model> +RTS -N2 -RTS
# ==============================================================================

set -u

# ------------------------------------------------------------------
# Configuration (override via environment variables if needed)
# ------------------------------------------------------------------
KIT_DIR="${KIT_DIR:-$(cd "$(dirname "$0")/.." && pwd)}"
TAMARIN="${TAMARIN:-$(command -v tamarin-prover)}"
MODELS_DIR="${MODELS_DIR:-$KIT_DIR/models}"
OUT_DIR="${OUT_DIR:-$KIT_DIR/runs}"
BUDGET="${BUDGET:-300}"                 # outer wall-clock budget in seconds
DERIVCHECK="${DERIVCHECK:-30}"          # --derivcheck-timeout value
RTS_CORES="${RTS_CORES:-2}"             # +RTS -N<N> -RTS
HEURISTICS_STR="${HEURISTICS:-s S c C p}"
REPS="${REPS:-3}"

mkdir -p "$OUT_DIR"
LOG="$OUT_DIR/battery.log"
SUMMARY="$OUT_DIR/summary.tsv"
PHASE_TIMING="$OUT_DIR/phase_timing.tsv"

if [ -z "$TAMARIN" ] || [ ! -x "$TAMARIN" ]; then
    echo "ERROR: tamarin-prover not found on PATH (set TAMARIN=<path> to override)" >&2
    exit 2
fi

# ------------------------------------------------------------------
# Preflight
# ------------------------------------------------------------------
{
    echo "========================================================"
    echo "Robustness Battery run"
    echo "started_utc: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "hostname:    $(hostname)"
    echo "tamarin:     $("$TAMARIN" --version 2>&1 | grep -o 'tamarin-prover [0-9.]*' | head -1)"
    echo "maude:       $(maude --version 2>/dev/null | head -1 || echo 'not on PATH')"
    echo "kernel:      $(uname -srm)"
    echo "cores_avail: $(nproc)"
    echo "mem_total:   $(awk '/MemTotal/ {print $2, $3}' /proc/meminfo)"
    echo "budget_s:    $BUDGET"
    echo "derivcheck:  $DERIVCHECK"
    echo "rts_cores:   $RTS_CORES"
    echo "heuristics:  $HEURISTICS_STR"
    echo "reps:        $REPS"
    echo "models_dir:  $MODELS_DIR"
    echo "out_dir:     $OUT_DIR"
    echo "========================================================"
} | tee "$LOG"

# Model paths
declare -A MODEL_FILE
MODEL_FILE[A]="$MODELS_DIR/A_raw.spthy"
MODEL_FILE[C]="$MODELS_DIR/C_state_carrier.spthy"

for v in A C; do
    if [ ! -f "${MODEL_FILE[$v]}" ]; then
        echo "ERROR: model file not found: ${MODEL_FILE[$v]}" >&2
        exit 2
    fi
done

read -a HEURISTICS <<< "$HEURISTICS_STR"

# Initialise output TSVs with headers
echo -e "variant\theuristic\trep\toutcome\twall_s\trss_kb\trc\ttamarin_version" > "$SUMMARY"
echo -e "variant\theuristic\trep\tderivcheck_s\tmain_s\ttotal_s" > "$PHASE_TIMING"

# ------------------------------------------------------------------
# Cell runner
# ------------------------------------------------------------------
run_cell() {
    local variant=$1
    local heur=$2
    local rep=$3
    local model="${MODEL_FILE[$variant]}"
    local tag="${variant}_h${heur}_r${rep}"
    local stdout_f="$OUT_DIR/${tag}.stdout"
    local stderr_f="$OUT_DIR/${tag}.stderr"
    local meta_f="$OUT_DIR/${tag}.meta"

    echo "-- $tag start=$(date -u +%H:%M:%SZ)" | tee -a "$LOG"

    local t0 t1 wall rc rss outcome
    t0=$(date +%s.%N)
    # /usr/bin/time -v -> $meta_f captures peak RSS
    # timeout --kill-after adds 5s grace to allow Tamarin to flush on SIGTERM
    /usr/bin/time -v -o "$meta_f" \
        timeout --kill-after=5s "${BUDGET}s" \
        "$TAMARIN" \
            --diff --prove \
            --heuristic="$heur" \
            --stop-on-trace=dfs \
            --derivcheck-timeout="$DERIVCHECK" \
            "$model" \
            +RTS "-N${RTS_CORES}" -RTS \
        > "$stdout_f" 2> "$stderr_f"
    rc=$?
    t1=$(date +%s.%N)
    wall=$(awk "BEGIN{printf \"%.2f\", $t1 - $t0}")

    # Classify outcome
    if [ "$rc" -eq 124 ] || [ "$rc" -eq 137 ]; then
        outcome="TIMEOUT"
    elif grep -qE "verified" "$stdout_f" 2>/dev/null; then
        outcome="VERIFIED"
    elif grep -qE "falsified" "$stdout_f" 2>/dev/null; then
        outcome="FALSIFIED"
    else
        outcome="OTHER"
    fi

    # Peak RSS in kB (from /usr/bin/time -v)
    rss=$(awk -F': ' '/Maximum resident set size/ {print $2}' "$meta_f" 2>/dev/null | tr -d ' ')
    [ -z "$rss" ] && rss="NA"

    local tver
    tver=$("$TAMARIN" --version 2>&1 | grep -o 'tamarin-prover [0-9.]*' | head -1 | awk '{print $2}')

    echo "   $tag: $outcome wall=${wall}s rss=${rss}kB rc=${rc}" | tee -a "$LOG"
    printf "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" \
        "$variant" "$heur" "$rep" "$outcome" "$wall" "$rss" "$rc" "$tver" >> "$SUMMARY"
}

# ------------------------------------------------------------------
# Schedule: counter-balanced by rep parity
# ------------------------------------------------------------------
for rep in $(seq 1 "$REPS"); do
    for heur in "${HEURISTICS[@]}"; do
        if [ $((rep % 2)) -eq 1 ]; then
            run_cell C "$heur" "$rep"
            run_cell A "$heur" "$rep"
        else
            run_cell A "$heur" "$rep"
            run_cell C "$heur" "$rep"
        fi
    done
done

echo "-- all runs complete, finished_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "$LOG"

# ------------------------------------------------------------------
# B2: extract derivation-check phase timing from stderr
# ------------------------------------------------------------------
python3 "$(dirname "$0")/extract_phase_timing.py" \
    --runs-dir "$OUT_DIR" \
    --output   "$PHASE_TIMING" \
    2>&1 | tee -a "$LOG"

echo ""                                 | tee -a "$LOG"
echo "=== Battery summary ==="          | tee -a "$LOG"
column -t -s $'\t' "$SUMMARY"           | tee -a "$LOG"
echo ""                                 | tee -a "$LOG"
echo "=== Phase timing ==="             | tee -a "$LOG"
column -t -s $'\t' "$PHASE_TIMING"      | tee -a "$LOG"

echo ""
echo "Output files:"
echo "  $SUMMARY"
echo "  $PHASE_TIMING"
echo "  $LOG"
echo "  $OUT_DIR/<variant>_h<heur>_r<rep>.{stdout,stderr,meta}"
