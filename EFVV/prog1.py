import time
import os
import signal

def sigterm_handler(signum, frame):
    print("Got SIGTERM, but I REFUSE TO DIE!")
# signal.signal(signal.SIGTERM, signal.SIG_IGN)
signal.signal(signal.SIGTERM, sigterm_handler)

print(os.getpid())

# x = 1. / 0

# print(x)

i = 0
while True:
	try:
		print("hello " + str(i))
		i += 1
		time.sleep(1)
	except:
		print("EXCEPTION\n")
		break









































