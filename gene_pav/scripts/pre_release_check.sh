#!/bin/bash
#
# pre_release_check.sh - Automated pre-release verification for PAVprot pipeline
#
# Usage:
#   ./scripts/pre_release_check.sh           # Quick check (linter + tests)
#   ./scripts/pre_release_check.sh --full    # Full check (includes venv test)
#   ./scripts/pre_release_check.sh --help    # Show help
#
# Created: 2026-01-26
#

set -e  # Exit on first error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Timestamp for logs
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="${PROJECT_ROOT}/scripts/pre_release_${TIMESTAMP}.log"

# --------------------------------------------------------------------------
# Helper functions
# --------------------------------------------------------------------------

print_header() {
    echo -e "\n${BLUE}════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}\n"
}

print_step() {
    echo -e "${YELLOW}▶ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

show_help() {
    cat << EOF
PAVprot Pre-Release Check Script

Usage:
    ./scripts/pre_release_check.sh [OPTIONS]

Options:
    --full      Run full checks including clean venv test
    --lint      Run only linting checks
    --test      Run only pytest
    --cli       Run only CLI help checks
    --help      Show this help message

Examples:
    ./scripts/pre_release_check.sh           # Quick check
    ./scripts/pre_release_check.sh --full    # Complete verification
    ./scripts/pre_release_check.sh --lint    # Just linting

Log files saved to: scripts/pre_release_*.log
EOF
}

# --------------------------------------------------------------------------
# Check functions
# --------------------------------------------------------------------------

check_flake8_installed() {
    if ! command -v flake8 &> /dev/null; then
        print_error "flake8 not installed"
        print_info "Install with: pip install flake8"
        return 1
    fi
    return 0
}

run_linter() {
    print_header "Phase 1.1: Code Quality - Linting"

    cd "$PROJECT_ROOT"

    if ! check_flake8_installed; then
        return 1
    fi

    print_step "Running flake8 on Python files..."

    # Count errors (don't exit on error for this check)
    set +e
    LINT_OUTPUT=$(flake8 *.py plot/*.py --count --select=E9,F63,F7,F82 --show-source --statistics 2>&1)
    CRITICAL_ERRORS=$?

    LINT_WARNINGS=$(flake8 *.py plot/*.py --count --exit-zero --max-complexity=10 --max-line-length=120 --statistics 2>&1)
    set -e

    if [ $CRITICAL_ERRORS -ne 0 ]; then
        print_error "Critical linting errors found:"
        echo "$LINT_OUTPUT"
        return 1
    else
        print_success "No critical linting errors"
    fi

    # Show warnings count
    WARNING_COUNT=$(echo "$LINT_WARNINGS" | tail -1)
    if [ -n "$WARNING_COUNT" ] && [ "$WARNING_COUNT" != "0" ]; then
        print_info "Warnings/style issues: $WARNING_COUNT"
        echo "$LINT_WARNINGS" | head -20
    else
        print_success "No style warnings"
    fi

    return 0
}

run_tests() {
    print_header "Phase 1.1: Code Quality - Tests"

    cd "$PROJECT_ROOT"

    print_step "Running pytest..."

    if python -m pytest test/ -v --tb=short 2>&1 | tee -a "$LOG_FILE"; then
        print_success "All tests passed"
        return 0
    else
        print_error "Some tests failed"
        return 1
    fi
}

run_cli_checks() {
    print_header "Phase 3: CLI Help Checks"

    cd "$PROJECT_ROOT"

    MODULES=(
        "pavprot.py"
        "gsmc.py"
        "mapping_multiplicity.py"
        "bidirectional_best_hits.py"
        "pairwise_align_prot.py"
        "parse_interproscan.py"
        "synonym_mapping_summary.py"
    )

    FAILED=0

    for module in "${MODULES[@]}"; do
        print_step "Testing $module --help"
        if python "$module" --help > /dev/null 2>&1; then
            print_success "$module --help works"
        else
            print_error "$module --help failed"
            FAILED=$((FAILED + 1))
        fi
    done

    if [ $FAILED -eq 0 ]; then
        print_success "All CLI modules pass --help check"
        return 0
    else
        print_error "$FAILED module(s) failed --help check"
        return 1
    fi
}

run_integration_test() {
    print_header "Phase 3: Integration Test"

    cd "$PROJECT_ROOT"

    if [ -f "test/run_integration_test.sh" ]; then
        print_step "Running integration test..."
        if bash test/run_integration_test.sh 2>&1 | tee -a "$LOG_FILE"; then
            print_success "Integration test passed"
            return 0
        else
            print_error "Integration test failed"
            return 1
        fi
    else
        print_info "Integration test script not found, skipping"
        return 0
    fi
}

run_venv_test() {
    print_header "Phase 3: Clean Virtual Environment Test"

    VENV_DIR="/tmp/pavprot_venv_test_${TIMESTAMP}"

    print_step "Creating fresh virtual environment at $VENV_DIR"
    python -m venv "$VENV_DIR"

    print_step "Activating venv and installing dependencies..."
    source "$VENV_DIR/bin/activate"

    pip install --upgrade pip > /dev/null 2>&1
    pip install -r "$PROJECT_ROOT/requirements.txt" 2>&1 | tee -a "$LOG_FILE"

    print_step "Running tests in clean venv..."
    cd "$PROJECT_ROOT"

    if python -m pytest test/ -v --tb=short 2>&1 | tee -a "$LOG_FILE"; then
        print_success "Tests pass in clean venv"
        RESULT=0
    else
        print_error "Tests fail in clean venv"
        RESULT=1
    fi

    deactivate

    print_step "Cleaning up test venv..."
    rm -rf "$VENV_DIR"

    return $RESULT
}

# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

main() {
    print_header "PAVprot Pre-Release Check"
    print_info "Project: $PROJECT_ROOT"
    print_info "Log file: $LOG_FILE"
    print_info "Started: $(date)"

    echo "Started: $(date)" > "$LOG_FILE"

    FULL_CHECK=false
    LINT_ONLY=false
    TEST_ONLY=false
    CLI_ONLY=false

    # Parse arguments
    for arg in "$@"; do
        case $arg in
            --full)
                FULL_CHECK=true
                ;;
            --lint)
                LINT_ONLY=true
                ;;
            --test)
                TEST_ONLY=true
                ;;
            --cli)
                CLI_ONLY=true
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                echo "Unknown option: $arg"
                show_help
                exit 1
                ;;
        esac
    done

    ERRORS=0

    # Run selected checks
    if [ "$LINT_ONLY" = true ]; then
        run_linter || ERRORS=$((ERRORS + 1))
    elif [ "$TEST_ONLY" = true ]; then
        run_tests || ERRORS=$((ERRORS + 1))
    elif [ "$CLI_ONLY" = true ]; then
        run_cli_checks || ERRORS=$((ERRORS + 1))
    else
        # Default: run quick checks
        run_linter || ERRORS=$((ERRORS + 1))
        run_tests || ERRORS=$((ERRORS + 1))
        run_cli_checks || ERRORS=$((ERRORS + 1))

        if [ "$FULL_CHECK" = true ]; then
            run_integration_test || ERRORS=$((ERRORS + 1))
            run_venv_test || ERRORS=$((ERRORS + 1))
        fi
    fi

    # Summary
    print_header "Summary"

    if [ $ERRORS -eq 0 ]; then
        print_success "All checks passed!"
        print_info "Ready for Phase 4 (Push & Merge)"
        echo ""
        echo "Next steps:"
        echo "  1. git tag -a v0.2.0 -m \"Release v0.2.0\""
        echo "  2. git push origin dev"
        echo "  3. gh pr create --base main --head dev"
    else
        print_error "$ERRORS check(s) failed"
        print_info "Fix issues before proceeding to Phase 4"
    fi

    print_info "Log saved to: $LOG_FILE"
    print_info "Finished: $(date)"

    exit $ERRORS
}

main "$@"
