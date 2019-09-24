from socket import *
from random import *
import threading
import time

# socket infomations.
recvIP = ''
recvPort = 10080
recvAddr = (recvIP, recvPort)
recvSocket = socket(AF_INET, SOCK_DGRAM)

# global variables.
packet = []
message = []
nem_queue = []
port = []
cum = []

nem_incoming_packet = 0
nem_forwarding_packet = 0
rm_received_packet = []
queue_util = []
queue_utilization = 0

# global time.
start_time = 0.0

#time
#incoming_rate
#forwarding_rate
#avg_queue_utilization
#jain_fairness_index
#port_number
#receiving_rate


def RM():
	global message

	while True:
		
		if len(message) > 0:
			tmp = message.pop(0)
			msg = tmp[0]
			sendAddr = tmp[1]
			port_index = port.index(sendAddr)
			rm_received_packet[port_index] += 1

			if msg[:1].decode() == '0':				# set-up message.
				cum_Ack=1

			elif msg[:1].decode() == '1':			# processing message.
				info = msg[:19].decode()
				n_port = info.split("|")[1]
				seq = int(info.split('|')[2])
#				print(seq, sendAddr)

				cum_Ack = cum[port_index]

				if cum_Ack == seq-1 :			# It's OK.

					cum[port_index] = cum_Ack + 1
					recvSocket.sendto(str(cum_Ack+1).encode(), sendAddr)


				elif cum_Ack <= seq :		# It's not in order packet, save it and send missed packet.
					recvSocket.sendto(str(cum_Ack).encode(), sendAddr)


#				if cum_Ack == num_of_packets-1:

			elif msg[:1].decode() == '2':		# file transmittion completely.
				print("file transfer finished")


def write_log(queue_size, i):
	global start_time, nem_incoming_packet, nem_forwarding_packet, rm_received_packet, queue_utilization

	fnem = open("NEM.log", "w+")
	frm = open("RM.log", "w+")

	print("time\t\t|  incoming rate\t|  forwarding rate\t|  avg_queue_utilization", file=fnem, flush=True)

	while True:
		time.sleep(2)

		# Print to NEM.log file
		print("%.3f\t\t|  %.3f\t\t\t|  %.3f\t\t\t|  %.3f" % (time.time()-start_time, nem_incoming_packet/2, nem_forwarding_packet/2, 
					queue_utilization/20/queue_size), file=fnem, flush=True)
		nem_incoming_packet=0
		nem_forwarding_packet=0

		# Calculate Jain's fairness index
		n = len(port)
		sum = 0
		for i in range(n):
			sum += rm_received_packet[i]/2
		numerator = sum * sum
		denominator = 0
		for i in range(n):
			denominator += rm_received_packet[i] * rm_received_packet[i] /4
		try :
			jain_fairness_index = numerator / (n * denominator)
		except :
			jain_fairness_index = 1.000

		# Print to RM.log file
		print("%.3f\t\t|  %.3f" %(time.time()-start_time, jain_fairness_index), file=frm, flush=True)
		i = 0
		for addr in port :
			print("\t\t|  sender IP : %d\t|  %.3f" %(addr[1], rm_received_packet[i]/2), file=frm, flush=True)
			rm_received_packet[i] = 0
			i += 1
		

def NEM(BLR, queue_size):
	global nem_incoming_packet, nem_forwarding_packet, isdeled

	while True :

		msg, sendAddr = recvSocket.recvfrom(4096)
		nem_incoming_packet += 1
		if len(nem_queue) <= queue_size : 
			if sendAddr not in port :
				port.append(sendAddr)
				cum.append(-1)
				rm_received_packet.append(0)

			nem_queue.append([msg, sendAddr]);


def NEMtoRM(BLR, i):
	global nem_queue, message, nem_forwarding_packet

	time_interval = 1/float(BLR)
	timestamp = 0.0
	print("time interval : %.4f" %time_interval)

	while True :
		if len(nem_queue) > 0 and time.time() - timestamp > time_interval:
#	if len(nem_queue) > 0 :
			timestamp = time.time()
			message.append(nem_queue[0])
			nem_forwarding_packet += 1
			del nem_queue[0]


def QueueUtil() :
	global queue_util, nem_queue, queue_utilization

	queue_util.append(0)
	while True:
		time.sleep(0.1)
		del queue_util[0]	
		queue_util.append(len(nem_queue))
		queue_utilization = sum(queue_util)


if __name__ == "__main__":
	configure = input("configure>>") or "100 10"
	BLR = int(configure.split(' ')[0])
	queue_size = int(configure.split(' ')[1])

	buf_size = recvSocket.getsockopt(SOL_SOCKET, SO_RCVBUF)
	print("socket recv buffer size: %d" % buf_size)
	recvSocket.setsockopt(SOL_SOCKET, SO_RCVBUF, 1000000)
	recvSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
	buf_size = recvSocket.getsockopt(SOL_SOCKET, SO_RCVBUF)
	print("socket recv buffer size updated: %d" % buf_size)
	print()
	print("receiver program starts...")

		
	recvSocket.bind(recvAddr)
#	try:
	print("receiver wait...")
	t_RM = threading.Thread(target = RM, args=())
	t_NEM = threading.Thread(target = NEM, args=(BLR, queue_size))
	t_NEMtoRM = threading.Thread(target = NEMtoRM, args=(BLR, 1))
	t_QueueUtil = threading.Thread(target = QueueUtil, args=())
	t_log = threading.Thread(target = write_log, args=(queue_size, 1))

	start_time = time.time()
	
	t_RM.start()
	t_NEM.start()
	t_NEMtoRM.start()
	t_QueueUtil.start()
	t_log.start()


	t_RM.join()
	t_NEM.join()
	t_NEMtoRM.join()
	t_QueueUtil.join()
	t_log.join()
#	except KeyboardInterrupt:

