#!/usr/bin/env bash

# ============================================================
# KATANA NORMAL SYSTEM WORKLOAD GENERATOR
# ============================================================
#
# Generates normal Linux desktop activity for KATANA training:
#
# - Terminal processes
# - Common shell commands
# - Python processes
# - File operations in /tmp
# - Editor processes
# - Browser processes
# - File manager processes
# - Process creation and termination
# - Random pauses
#
# Nothing destructive is performed.
#
# Usage:
#   ./normal_workload.sh
#
#   ./normal_workload.sh 3
#
# ============================================================


set -u


# ============================================================
# CONFIGURATION
# ============================================================

ROUNDS="${1:-2}"

WORK_DIR="/tmp/katana_normal_workload"

MIN_SLEEP=2
MAX_SLEEP=6


# ============================================================
# COLORS
# ============================================================

RED="\033[0;31m"
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
CYAN="\033[0;36m"
RESET="\033[0m"


# ============================================================
# HELPER FUNCTIONS
# ============================================================

log() {
    echo -e "${CYAN}[KATANA WORKLOAD]${RESET} $1"
}


success() {
    echo -e "${GREEN}[DONE]${RESET} $1"
}


warn() {
    echo -e "${YELLOW}[SKIP]${RESET} $1"
}


pause_random() {
    local seconds

    seconds=$(
        shuf \
            -i "${MIN_SLEEP}-${MAX_SLEEP}" \
            -n 1
    )

    log "Waiting ${seconds}s..."
    sleep "$seconds"
}


command_exists() {
    command -v "$1" \
        >/dev/null 2>&1
}


# ============================================================
# FIND TERMINAL
# ============================================================

find_terminal() {

    if command_exists kitty; then
        echo "kitty"

    elif command_exists foot; then
        echo "foot"

    elif command_exists alacritty; then
        echo "alacritty"

    elif command_exists wezterm; then
        echo "wezterm"

    elif command_exists xterm; then
        echo "xterm"

    else
        echo ""
    fi
}


TERMINAL="$(find_terminal)"


# ============================================================
# TEMP WORKSPACE
# ============================================================

prepare_workspace() {

    mkdir \
        -p \
        "$WORK_DIR"

    echo \
        "KATANA normal workload data" \
        > "$WORK_DIR/sample.txt"

    for i in {1..5}; do

        echo \
            "Sample data $i" \
            > "$WORK_DIR/file_$i.txt"

    done

    success \
        "Workspace prepared"

}


# ============================================================
# TERMINAL ACTIVITY
# ============================================================

terminal_activity() {

    if [ -z "$TERMINAL" ]; then

        warn \
            "No supported terminal found"

        return

    fi


    log \
        "Opening terminal activity"

    case "$TERMINAL" in

        kitty)

            kitty \
                bash \
                -lc "
                    echo 'KATANA normal workload'
                    pwd
                    whoami
                    uname -a
                    echo
                    ls
                    echo
                    ps aux | head -10
                    echo
                    free -h
                    echo
                    sleep 5
                " \
                >/dev/null 2>&1 &

            ;;


        foot)

            foot \
                bash \
                -lc "
                    echo 'KATANA normal workload'
                    pwd
                    whoami
                    ls
                    ps aux | head -10
                    sleep 5
                " \
                >/dev/null 2>&1 &

            ;;


        alacritty)

            alacritty \
                -e \
                bash \
                -lc "
                    pwd
                    whoami
                    uname -a
                    ls
                    sleep 5
                " \
                >/dev/null 2>&1 &

            ;;


        wezterm)

            wezterm \
                start \
                -- \
                bash \
                -lc "
                    pwd
                    whoami
                    ls
                    sleep 5
                " \
                >/dev/null 2>&1 &

            ;;


        xterm)

            xterm \
                -e \
                bash \
                -lc "
                    pwd
                    whoami
                    ls
                    sleep 5
                " \
                >/dev/null 2>&1 &

            ;;

    esac


    success \
        "Terminal process created"

}


# ============================================================
# SHELL COMMAND ACTIVITY
# ============================================================

shell_activity() {

    log \
        "Running normal shell commands"

    pwd \
        >/dev/null

    whoami \
        >/dev/null

    uname \
        -a \
        >/dev/null

    ls \
        -la \
        "$WORK_DIR" \
        >/dev/null

    find \
        "$WORK_DIR" \
        -type f \
        >/dev/null

    ps \
        aux \
        >/dev/null

    free \
        -h \
        >/dev/null 2>&1 || true

    uptime \
        >/dev/null

    df \
        -h \
        >/dev/null

    success \
        "Shell activity completed"

}


# ============================================================
# FILE ACTIVITY
# ============================================================

file_activity() {

    log \
        "Performing normal file activity"

    local round_file

    round_file="$WORK_DIR/round_$(date +%s).txt"

    echo \
        "KATANA training activity" \
        > "$round_file"

    cp \
        "$round_file" \
        "${round_file}.backup"

    cat \
        "$round_file" \
        >/dev/null

    wc \
        -l \
        "$round_file" \
        >/dev/null

    mv \
        "${round_file}.backup" \
        "${round_file}.copy"

    rm \
        -f \
        "${round_file}.copy"

    success \
        "File activity completed"

}


# ============================================================
# PYTHON ACTIVITY
# ============================================================

python_activity() {

    if ! command_exists python; then

        warn \
            "Python not found"

        return

    fi


    log \
        "Starting normal Python process"

    python \
        -c "
import os
import platform
import time

data = [i * i for i in range(10000)]

print('Python workload')
print(platform.system())
print(os.getpid())

time.sleep(3)

print(sum(data))
" \
        >/dev/null 2>&1 &


    local pid=$!

    wait \
        "$pid" \
        2>/dev/null || true


    success \
        "Python process completed"

}


# ============================================================
# SHORT-LIVED BACKGROUND PROCESSES
# ============================================================

background_process_activity() {

    log \
        "Creating normal background processes"

    sleep 3 &
    local pid1=$!

    sleep 5 &
    local pid2=$!

    bash \
        -c "
            for i in {1..100000}; do
                :
            done
        " \
        >/dev/null 2>&1 &

    local pid3=$!


    wait \
        "$pid1" \
        2>/dev/null || true

    wait \
        "$pid2" \
        2>/dev/null || true

    wait \
        "$pid3" \
        2>/dev/null || true


    success \
        "Background processes completed"

}


# ============================================================
# PROCESS MONITORING COMMANDS
# ============================================================

process_monitor_activity() {

    log \
        "Running process inspection commands"

    ps \
        -eo \
        pid,ppid,comm,%cpu,%mem \
        >/dev/null

    top \
        -b \
        -n 1 \
        >/dev/null 2>&1 || true

    success \
        "Process inspection completed"

}


# ============================================================
# OPEN FILE MANAGER
# ============================================================

file_manager_activity() {

    local manager=""

    if command_exists thunar; then

        manager="thunar"

    elif command_exists dolphin; then

        manager="dolphin"

    elif command_exists nautilus; then

        manager="nautilus"

    fi


    if [ -z "$manager" ]; then

        warn \
            "No supported file manager found"

        return

    fi


    log \
        "Opening file manager"

    "$manager" \
        "$WORK_DIR" \
        >/dev/null 2>&1 &


    success \
        "File manager launched"

}


# ============================================================
# OPEN CODE EDITOR
# ============================================================

editor_activity() {

    local editor=""

    if command_exists code; then

        editor="code"

    elif command_exists codium; then

        editor="codium"

    elif command_exists nvim; then

        editor="nvim"

    fi


    if [ -z "$editor" ]; then

        warn \
            "No supported editor found"

        return

    fi


    log \
        "Starting editor activity"

    if [ "$editor" = "nvim" ]; then

        "$editor" \
            "$WORK_DIR/sample.txt" \
            >/dev/null 2>&1 &

        sleep 3

        pkill \
            -f \
            "nvim.*sample.txt" \
            2>/dev/null || true

    else

        "$editor" \
            "$WORK_DIR/sample.txt" \
            >/dev/null 2>&1 &

    fi


    success \
        "Editor activity generated"

}


# ============================================================
# BROWSER ACTIVITY
# ============================================================

browser_activity() {

    local browser=""

    if command_exists firefox; then

        browser="firefox"

    elif command_exists brave; then

        browser="brave"

    elif command_exists chromium; then

        browser="chromium"

    fi


    if [ -z "$browser" ]; then

        warn \
            "No supported browser found"

        return

    fi


    log \
        "Opening browser activity"

    "$browser" \
        "about:blank" \
        >/dev/null 2>&1 &


    success \
        "Browser launched"

}


# ============================================================
# CLEANUP
# ============================================================

cleanup() {

    log \
        "Cleaning temporary files"

    rm \
        -rf \
        "$WORK_DIR"

    success \
        "Temporary workspace removed"

}


# ============================================================
# MAIN
# ============================================================

main() {

    echo

    echo \
        "===================================================="

    echo \
        "       KATANA NORMAL WORKLOAD GENERATOR"

    echo \
        "===================================================="

    echo

    echo \
        "Rounds: $ROUNDS"

    echo \
        "Terminal: ${TERMINAL:-Not found}"

    echo


    prepare_workspace

    pause_random


    for ((round=1; round<=ROUNDS; round++)); do

        echo

        echo \
            "----------------------------------------------------"

        log \
            "STARTING ROUND $round / $ROUNDS"

        echo \
            "----------------------------------------------------"

        echo


        # Randomize activity order slightly.

        shell_activity

        pause_random

        background_process_activity

        pause_random

        python_activity

        pause_random

        file_activity

        pause_random

        process_monitor_activity

        pause_random

        terminal_activity

        pause_random

        file_manager_activity

        pause_random

        editor_activity

        pause_random

        browser_activity

        pause_random


        log \
            "ROUND $round COMPLETED"

    done


    echo

    echo \
        "===================================================="

    success \
        "NORMAL WORKLOAD GENERATION COMPLETE"

    echo \
        "===================================================="

    echo


    cleanup

}


main
