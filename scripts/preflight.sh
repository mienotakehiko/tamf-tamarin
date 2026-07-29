#!/bin/bash
# Preflight: verify environment before running run_battery.sh.
# Prints PASS / FAIL for each critical check.
# Exit code 0 = ready to run, non-zero = missing prerequisite.

set -u

KIT_DIR="${KIT_DIR:-$(cd "$(dirname "$0")/.." && pwd)}"
FAIL=0

check() {
    local label=$1
    local ok=$2
    local detail=${3:-}
    if [ "$ok" = "PASS" ]; then
        printf "  [ %s ] %s %s\n" "$ok" "$label" "$detail"
    else
        printf "  [ %s ] %s %s\n" "$ok" "$label" "$detail"
        FAIL=$((FAIL + 1))
    fi
}

echo "=== Robustness Battery preflight ==="
echo "Kit dir: $KIT_DIR"
echo ""

# 1. tamarin-prover
if command -v tamarin-prover >/dev/null 2>&1; then
    TVER=$(tamarin-prover --version 2>&1 | grep -o 'tamarin-prover [0-9.]*' | head -1)
    if echo "$TVER" | grep -qE "1\.(10|12)\.0"; then
        check "tamarin-prover 1.10.0 or 1.12.0"  PASS  "($TVER)"
    else
        check "tamarin-prover 1.10.0 or 1.12.0"  WARN  "(found $TVER, frozen baseline used 1.12.0)"
    fi
else
    check "tamarin-prover on PATH" FAIL "(not found)"
fi

# 2. maude
if command -v maude >/dev/null 2>&1; then
    MVER=$(maude --version 2>&1 | head -1)
    check "maude on PATH" PASS "($MVER)"
else
    check "maude on PATH" FAIL "(not found)"
fi

# 3. /usr/bin/time -v
if /usr/bin/time -v true 2>/dev/null; then
    check "/usr/bin/time -v (GNU time)" PASS ""
else
    # Some distros only ship the shell builtin
    if /usr/bin/time --version 2>&1 | grep -q "GNU"; then
        check "/usr/bin/time -v (GNU time)" PASS "(GNU time detected)"
    else
        check "/usr/bin/time -v (GNU time)" FAIL "(needed for peak RSS)"
    fi
fi

# 4. Python 3
if command -v python3 >/dev/null 2>&1; then
    PYVER=$(python3 --version 2>&1)
    check "python3" PASS "($PYVER)"
else
    check "python3" FAIL "(needed by extract_phase_timing.py)"
fi

# 5. Physical memory (must be > 7 GiB to fit A_raw's peak RSS ~6.2 GiB)
MEM_TOTAL_KB=$(awk '/MemTotal/ {print $2}' /proc/meminfo)
MEM_TOTAL_GIB=$(awk -v k="$MEM_TOTAL_KB" 'BEGIN{printf "%.1f", k/1048576}')
if [ "$MEM_TOTAL_KB" -ge 7340032 ]; then   # 7 GiB
    check "physical memory >= 7 GiB" PASS "($MEM_TOTAL_GIB GiB)"
elif [ "$MEM_TOTAL_KB" -ge 4194304 ]; then # 4 GiB
    check "physical memory >= 7 GiB" WARN "($MEM_TOTAL_GIB GiB found; A_raw peaks ~6.2 GiB in the frozen baseline, OOM risk)"
else
    check "physical memory >= 7 GiB" FAIL "($MEM_TOTAL_GIB GiB found; certainly OOM)"
fi

# 6. Swap disabled (recommended) or generous
SWAP_TOTAL_KB=$(awk '/SwapTotal/ {print $2}' /proc/meminfo)
if [ "$SWAP_TOTAL_KB" -eq 0 ]; then
    check "swap disabled (recommended for stable RSS reading)" PASS ""
else
    check "swap present" WARN "($((SWAP_TOTAL_KB/1024)) MiB swap; peak RSS reading may include swap)"
fi

# 7. Cores
CORES=$(nproc)
if [ "$CORES" -ge 2 ]; then
    check "cores >= 2 (matches +RTS -N2)" PASS "($CORES cores available)"
else
    check "cores >= 2" WARN "($CORES core only; +RTS -N2 may oversubscribe)"
fi

# 8. Model files present
for m in A_raw.spthy B_raw_priority.spthy C_state_carrier.spthy D_state_priority.spthy; do
    if [ -f "$KIT_DIR/models/$m" ]; then
        check "model file $m" PASS ""
    else
        check "model file $m" FAIL "(missing under $KIT_DIR/models/)"
    fi
done

# 9. Disk space for logs (30 runs × up to 20 MB each)
FREE_KB=$(df -Pk "$KIT_DIR" | awk 'NR==2 {print $4}')
FREE_MB=$((FREE_KB / 1024))
if [ "$FREE_MB" -ge 1024 ]; then
    check "free disk >= 1 GiB in kit dir" PASS "($FREE_MB MB)"
else
    check "free disk >= 1 GiB in kit dir" WARN "($FREE_MB MB only)"
fi

echo ""
if [ "$FAIL" -eq 0 ]; then
    echo "PREFLIGHT: OK ready to run scripts/run_battery.sh"
else
    echo "PREFLIGHT: $FAIL check(s) failed. Fix them before running the battery."
fi
exit "$FAIL"
