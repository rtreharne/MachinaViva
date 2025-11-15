#!/bin/bash

set -e

# ---------------------------------------------------------------------
#  ARGUMENT PARSING
# ---------------------------------------------------------------------

if [ "$#" -lt 2 ] || [ "$#" -gt 3 ]; then
    echo "Usage: $0 <old_app_name> <new_app_name> [--dry-run]"
    exit 1
fi

OLD=$1
NEW=$2
DRY_RUN=false

if [ "$3" = "--dry-run" ]; then
    DRY_RUN=true
fi

echo "=== Django App Rename: '$OLD' → '$NEW' ==="
echo "Dry run: $DRY_RUN"
echo ""

# ---------------------------------------------------------------------
#  PRE-CHECKS
# ---------------------------------------------------------------------

if [ ! -d "$OLD" ]; then
    echo "ERROR: App directory '$OLD' does not exist."
    exit 1
fi

if [ -d "$NEW" ]; then
    echo "ERROR: Target directory '$NEW' already exists."
    exit 1
fi


# Helper for dry-run echo vs actual exec
run() {
    if [ "$DRY_RUN" = true ]; then
        echo "[dry-run] $*"
    else
        eval "$@"
    fi
}


# ---------------------------------------------------------------------
# 1. Rename folder
# ---------------------------------------------------------------------

echo "→ Step 1: Renaming folder"
run mv "$OLD" "$NEW"
echo ""


# ---------------------------------------------------------------------
# 2. Update settings.py (INSTALLED_APPS)
# ---------------------------------------------------------------------

SETTINGS_FILE="lti/settings.py"
if [ -f "$SETTINGS_FILE" ]; then
    echo "→ Step 2: Updating INSTALLED_APPS in $SETTINGS_FILE"
    run "sed -i \"s/'$OLD'/'$NEW'/g\" \"$SETTINGS_FILE\""
else
    echo "WARNING: $SETTINGS_FILE not found"
fi
echo ""


# ---------------------------------------------------------------------
# 3. Update root URL include
# ---------------------------------------------------------------------

URLS_FILE="lti/urls.py"
if [ -f "$URLS_FILE" ]; then
    echo "→ Step 3: Updating include() in $URLS_FILE"
    run "sed -i \"s/include(\\\"$OLD.urls\\\")/include(\\\"$NEW.urls\\\")/g\" \"$URLS_FILE\""
    run "sed -i \"s/include('$OLD.urls')/include('$NEW.urls')/g\" \"$URLS_FILE\""
fi
echo ""


# ---------------------------------------------------------------------
# 4. Update apps.py
# ---------------------------------------------------------------------

APPS_FILE="$NEW/apps.py"
if [ -f "$APPS_FILE" ]; then
    echo "→ Step 4: Updating $APPS_FILE"

    OLD_CLASS=$(grep -oP 'class\s+\K\w+(?=Config)' "$APPS_FILE" || echo "")
    NEW_CLASS="$(echo "$NEW" | sed 's/.*/\u&/')Config"

    if [ "$OLD_CLASS" != "" ]; then
        run "sed -i \"s/class $OLD_CLASS/class $(echo "$NEW" | sed 's/.*/\u&/')/\" \"$APPS_FILE\""
    fi

    run "sed -i \"s/name = '$OLD'/name = '$NEW'/\" \"$APPS_FILE\""
else
    echo "WARNING: $APPS_FILE not found"
fi
echo ""


# ---------------------------------------------------------------------
# 5. Replace imports everywhere
# ---------------------------------------------------------------------

echo "→ Step 5: Updating imports project-wide"
ALL_FILES=$(grep -rl "$OLD" . --include="*.py" --exclude-dir=".git" --exclude-dir=".venv" --exclude-dir="venv")

for file in $ALL_FILES; do
    echo "   updating: $file"
    run "sed -i \"s/\\b$OLD\\b/$NEW/g\" \"$file\""
done
echo ""


# ---------------------------------------------------------------------
# 6. Reset migrations
# ---------------------------------------------------------------------

MIGR_DIR="$NEW/migrations"

echo "→ Step 6: Resetting migrations"

run "rm -rf \"$MIGR_DIR\""
run "mkdir -p \"$MIGR_DIR\""
run "touch \"$MIGR_DIR/__init__.py\""

echo ""


# ---------------------------------------------------------------------
# 7. Ask about db reset (disabled in dry-run)
# ---------------------------------------------------------------------

if [ "$DRY_RUN" = true ]; then
    echo "→ Step 7: Skipping DB reset (dry run)"
else
    echo ""
    read -p "Do you want to delete db.sqlite3 and run fresh migrations? (y/N): " confirm
    if [[ "$confirm" =~ ^[Yy]$ ]]; then
        rm -f db.sqlite3
        echo "db.sqlite3 removed."
        echo "Running migrations..."
        python manage.py migrate
    else
        echo "Skipping DB reset."
        echo "You may need:"
        echo "  python manage.py makemigrations"
        echo "  python manage.py migrate"
    fi
fi

echo ""
echo "=== App rename complete! ==="
if [ "$DRY_RUN" = true ]; then
    echo "(dry run — no files were modified)"
fi
