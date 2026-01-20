#!/bin/bash
#
# sync_to_github.sh - Sync dev gene_pav code to GitHub repository
#
# Usage:
#   ./sync_to_github.sh [--dry-run] [--push]
#
# Options:
#   --dry-run   Show what would be copied without actually copying
#   --push      Push to remote after syncing (requires confirmation)
#

set -e

# Directories
DEV_DIR="/Users/sadik/projects/github_prj/uolismib/uolocal/fungidb/dev/gene_pav"
GITHUB_DIR="/Users/sadik/projects/github_prj/uolismib/gene_pav"

# Parse arguments
DRY_RUN=false
DO_PUSH=false
for arg in "$@"; do
    case $arg in
        --dry-run) DRY_RUN=true ;;
        --push) DO_PUSH=true ;;
    esac
done

echo "========================================"
echo "  gene_pav Sync Script"
echo "========================================"
echo "Source:      $DEV_DIR"
echo "Destination: $GITHUB_DIR"
echo "Dry run:     $DRY_RUN"
echo "Push:        $DO_PUSH"
echo "========================================"
echo ""

# Files and directories to sync (CORE PIPELINE ONLY - no project-specific scripts)
SYNC_ITEMS=(
    # Core pipeline scripts
    "analysis/pavprot.py:pavprot.py"
    "analysis/parse_interproscan.py:parse_interproscan.py"
    "analysis/bidirectional_best_hits.py:bidirectional_best_hits.py"
    "analysis/detect_one2many_mappings.py:mapping_multiplicity.py"
    "analysis/detect_advanced_scenarios.py:gsmc.py"
    "analysis/pariwise_align_prot.py:pairwise_align_prot.py"
    "analysis/inconsistent_genes_transcript_IPR_PAV.py:inconsistent_genes_transcript_IPR_PAV.py"
    "analysis/synonym_mapping_summary.py:synonym_mapping_summary.py"

    # Utilities
    "utils/parse_liftover_extra_copy_number.py:parse_liftover_extra_copy_number.py"
    "utils/synonym_mapping_parse.py:synonym_mapping_parse.py"

    # Documentation
    "README.md:README.md"
    ".gitignore:.gitignore"

)

# Project-specific scripts -> go to project_scripts/ folder as templates
PROJECT_SCRIPTS=(
    "run_pipeline.py:project_scripts/run_pipeline.py"
    "run_emckmnje1_analysis.py:project_scripts/run_emckmnje1_analysis.py"
    "analyze_fungidb_species.py:project_scripts/analyze_fungidb_species.py"
    "plot_oldvsnew_psauron_plddt.py:project_scripts/plot_oldvsnew_psauron_plddt.py"
    "plot_ipr_1to1_comparison.py:project_scripts/plot_ipr_1to1_comparison.py"
    "plot_psauron_distribution.py:project_scripts/plot_psauron_distribution.py"
    "project_scripts_README.md:project_scripts/README.md"
)

# Directories to copy entirely
SYNC_DIRS=(
    "plot"
    "test"
    "docs"
)

echo "Syncing core pipeline files..."
for item in "${SYNC_ITEMS[@]}"; do
    src="${item%%:*}"
    dst="${item##*:}"
    src_path="$DEV_DIR/$src"
    dst_path="$GITHUB_DIR/$dst"

    if [ -f "$src_path" ]; then
        if $DRY_RUN; then
            echo "[dry-run] $src -> $dst"
        else
            cp "$src_path" "$dst_path"
            echo "[copied] $src -> $dst"
        fi
    else
        echo "[skip] $src (not found)"
    fi
done

echo ""
echo "Syncing project-specific scripts to project_scripts/..."
# Create project_scripts directory if it doesn't exist
if ! $DRY_RUN; then
    mkdir -p "$GITHUB_DIR/project_scripts"
fi

for item in "${PROJECT_SCRIPTS[@]}"; do
    src="${item%%:*}"
    dst="${item##*:}"
    src_path="$DEV_DIR/$src"
    dst_path="$GITHUB_DIR/$dst"

    if [ -f "$src_path" ]; then
        if $DRY_RUN; then
            echo "[dry-run] $src -> $dst"
        else
            cp "$src_path" "$dst_path"
            echo "[copied] $src -> $dst"
        fi
    else
        echo "[skip] $src (not found)"
    fi
done

echo ""
echo "Syncing directories..."
for dir in "${SYNC_DIRS[@]}"; do
    src_path="$DEV_DIR/$dir"
    dst_path="$GITHUB_DIR/$dir"

    if [ -d "$src_path" ]; then
        if $DRY_RUN; then
            echo "[dry-run] $dir/ ($(find "$src_path" -type f | wc -l | tr -d ' ') files)"
        else
            # Remove destination directory first to avoid stale files
            rm -rf "$dst_path"
            cp -r "$src_path" "$dst_path"
            echo "[copied] $dir/ ($(find "$dst_path" -type f | wc -l | tr -d ' ') files)"
        fi
    else
        echo "[skip] $dir/ (not found)"
    fi
done

# Clean up unwanted files in destination
if ! $DRY_RUN; then
    echo ""
    echo "Cleaning up..."
    find "$GITHUB_DIR" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    find "$GITHUB_DIR" -name "*.pyc" -delete 2>/dev/null || true
    find "$GITHUB_DIR" -name ".DS_Store" -delete 2>/dev/null || true
    echo "[cleaned] Removed __pycache__, *.pyc, .DS_Store"
fi

echo ""
echo "========================================"
echo "  Sync Complete"
echo "========================================"

# Show git status
echo ""
echo "Git status in $GITHUB_DIR:"
cd "$GITHUB_DIR"
git status --short

# Push if requested
if $DO_PUSH && ! $DRY_RUN; then
    echo ""
    read -p "Push to remote? (y/N): " confirm
    if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
        git add -A
        git commit -m "Sync from dev: $(date +%Y-%m-%d)"
        git push origin dev
        echo "[pushed] Changes pushed to origin/dev"
    else
        echo "[skipped] Push cancelled"
    fi
fi

echo ""
echo "Next steps:"
echo "  1. Review changes: cd $GITHUB_DIR && git diff"
echo "  2. Stage changes:  git add -A"
echo "  3. Commit:         git commit -m 'Sync from dev'"
echo "  4. Push to dev:    git push origin dev"
echo "  5. When ready:     git checkout main && git merge dev"
