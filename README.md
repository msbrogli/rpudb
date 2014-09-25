remote pudb
===========
Runs a telnet server and allows controlling the pudb from a remote computer.

How to use
----------
In the server:

    import rpudb
	rpudb.set_trace(addr='0.0.0.0', port=4444)

In your computer:

    telnet localhost 4444

