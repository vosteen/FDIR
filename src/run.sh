#!/bin/bash

source ../venv/bin/activate

# Starte eine neue tmux-Session namens "mosquitto_and_python"
tmux new-session -d -s mosquitto_and_python

# Teile das Fenster in acht Panes auf
tmux split-window -h
tmux split-window -v
tmux select-pane -t 0
tmux split-window -v
tmux select-pane -t 2
tmux split-window -v
tmux select-pane -t 4
tmux split-window -v
tmux select-pane -t 6
tmux split-window -v

# Starte die spezifischen Befehle in jedem Pane
tmux send-keys -t mosquitto_and_python:0.0 'python identification.py' C-m
tmux send-keys -t mosquitto_and_python:0.1 'python monitor.py' C-m
tmux send-keys -t mosquitto_and_python:0.2 'python simulation.py' C-m
tmux send-keys -t mosquitto_and_python:0.3 'python controller_simulation.py' C-m
tmux send-keys -t mosquitto_and_python:0.4 'python plot.py' C-m
tmux send-keys -t mosquitto_and_python:0.5 'python dtdl2graph.py' C-m
tmux send-keys -t mosquitto_and_python:0.6 'sleep 1;python controller.py' C-m

# Wechsel zurück zu Pane 0
tmux select-pane -t 0.4

# Anhängen an die tmux-Session
tmux attach-session -t mosquitto_and_python
