import sys
import time
import zmq

context = zmq.Context()

work = context.socket(zmq.PULL)
work.connect("tcp://localhost:5557")

# Socket to send messages to
sink = context.socket(zmq.PUSH)
sink.connect("tcp://localhost:5558")

# Process tasks forever
tasks = 0
while True:
    s = work.recv()
    tasks += 1
    # Do the work
    time.sleep(int(s)*0.001)
 
    # Send results to sink
    sink.send(b'')

    print(f"I do {tasks} tasks")