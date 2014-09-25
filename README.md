remote pudb
===========
Runs a telnet server and allows controlling the pudb from a remote computer.


How to install
--------------

    pip install rpudb


How to use
----------
In the server:

    import rpudb
	rpudb.set_trace(addr='0.0.0.0', port=4444)

In your computer:

    telnet localhost 4444


How it works
------------
It runs pudb in a pseudo-terminal. You connect to this pseudo-terminal through a telnet server.


License
-------
Released under the MIT license. Read LICENSE.md for more information.
