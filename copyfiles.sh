#!/bin/bash

{
  find . -type f \
    \( -name '*.py' -o -name '*.html' -o -name '*.css' -o -name '*.js' \) \
    -not -path "./.venv/*" \
    -not -path "*/migrations/*" \
  | while read -r f; do
      echo "===== $f ====="
      cat "$f"
      echo -e "\n"
    done
} | xclip -selection clipboard

echo "Copied to clipboard!"
