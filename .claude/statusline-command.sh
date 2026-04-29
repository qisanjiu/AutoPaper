#!/bin/bash
# Claude Code status line - Context Monitor
# Displays context window usage information

input=$(cat)

# Extract context usage info
used_pct=$(echo "$input" | jq -r '.context_window.used_percentage // empty')
remaining_pct=$(echo "$input" | jq -r '.context_window.remaining_percentage // empty')
total_input=$(echo "$input" | jq -r '.context_window.total_input_tokens // empty')
total_output=$(echo "$input" | jq -r '.context_window.total_output_tokens // empty')
model_name=$(echo "$input" | jq -r '.model.display_name // empty')
session_name=$(echo "$input" | jq -r '.session_name // empty')

# Build output parts
parts=()

# Session name (if set)
if [ -n "$session_name" ] && [ "$session_name" != "null" ]; then
    parts+=("$session_name")
fi

# Context usage
if [ -n "$used_pct" ] && [ "$used_pct" != "null" ]; then
    used_int=$(printf '%.0f' "$used_pct")
    if [ -n "$remaining_pct" ] && [ "$remaining_pct" != "null" ]; then
        remain_int=$(printf '%.0f' "$remaining_pct")
        parts+=("ctx:${used_int}% remain:${remain_int}%")
    else
        parts+=("ctx:${used_int}%")
    fi
elif [ -n "$remaining_pct" ] && [ "$remaining_pct" != "null" ]; then
    remain_int=$(printf '%.0f' "$remaining_pct")
    parts+=("ctx remain:${remain_int}%")
fi

# Token counts (compact format)
if [ -n "$total_input" ] && [ "$total_input" != "null" ] && [ "$total_input" != "0" ]; then
    parts+=("in:${total_input}")
fi
if [ -n "$total_output" ] && [ "$total_output" != "null" ] && [ "$total_output" != "0" ]; then
    parts+=("out:${total_output}")
fi

# Model name
if [ -n "$model_name" ] && [ "$model_name" != "null" ]; then
    parts+=("$model_name")
fi

# Join with separator
IFS=' | '
echo "${parts[*]}"
