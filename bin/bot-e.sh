#!/bin/sh
#
# rc script for node.js primary webserver
#

. /etc/rc.subr

name="bot-e"
rcvar="bot-e_enable"

pidfile="/var/run/${name}.pid"
command="/usr/local/bin/node"
command_args="/usr/local/bot-e/web/app.js"
start_cmd="node_start"
stop_cmd="node_stop"

node_start() {
  if [ -n "$rc_pid" ]; then
    echo "$name is already running."
  else
    echo "Starting $name..."
    /usr/sbin/daemon -r -P "$pidfile" -o /var/log/${name}.log -u www -c "exec $command $command_args"
  fi
}

node_stop() {
  if [ -n "$rc_pid" ]; then
    echo "Stopping $name..."
    kill -TERM "$rc_pid"
    wait "$rc_pid"
    rm -f "$pidfile"
    echo "$name stopped."
  else
    echo "$name is not running."
  fi
}

load_rc_config $name
run_rc_command "$1"

