#!/bin/sh
### BEGIN INIT INFO
# Provides:          Polyptyque
# Required-Start:    $all
# Required-Stop:
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Start polyptyque slave-module python3 app
### END INIT INFO

DAEMON_SBIN=/home/pi/slave-module/app.py
NAME=polyptyque-slave-module
DESC="Polyptyque slave-module"
PIDFILE=/var/run/polyptyque-slave-module.pid

[ -x "$DAEMON_SBIN" ] || exit 0

DAEMON_OPTS="-B -P $PIDFILE $DAEMON_OPTS"

. /lib/lsb/init-functions

case "$1" in
  start)
        log_daemon_msg "Starting $DESC" "$NAME"
        start-stop-daemon --start --oknodo --quiet --exec "$DAEMON_SBIN" \
                --pidfile "$PIDFILE" -- $DAEMON_OPTS >/dev/null
        log_end_msg "$?"
        ;;
  stop)
        log_daemon_msg "Stopping $DESC" "$NAME"
        start-stop-daemon --stop --oknodo --quiet --exec "$DAEMON_SBIN" \
                --pidfile "$PIDFILE"
        log_end_msg "$?"
        ;;
  reload)
        log_daemon_msg "Reloading $DESC" "$NAME"
        start-stop-daemon --stop --signal HUP --exec "$DAEMON_SBIN" \
                --pidfile "$PIDFILE"
        log_end_msg "$?"
        ;;
  restart|force-reload)
        $0 stop
        sleep 8
        $0 start
        ;;
  status)
        status_of_proc "$DAEMON_SBIN" "$NAME"
        exit $?
        ;;
  *)
        N=/etc/init.d/$NAME
        echo "Usage: $N {start|stop|restart|force-reload|reload|status}" >&2
        exit 1
        ;;
esac

exit 0

