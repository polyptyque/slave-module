#!/bin/sh
### BEGIN INIT INFO
# Provides:          Polyptyque
# Required-Start:    $all
# Required-Stop:
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Start polyptyque slave-module python3 app
### END INIT INFO

echo "init polyptyque..."
/home/pi/slave-module/app.py