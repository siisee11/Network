from socket import *
import os
from threading import Thread
import threading
import time

# file segment size per packet.
SEG_SIZE = 1300

# server information.
sendIP = ''
sendPort = 0
sendAddr = (sendIP, sendPort)
sendSocket = socket(AF_INET, SOCK_DGRAM)

# global time.
start_time = time.time()

# global flag.
is_stopped = False

# lock variables.
lock = threading.Lock()

# global variables.
window_size = 0
ack = -1
packet = []
timer = []
rtt_timer = []
pkt_to_send = 0
sendbase = 0
finished = False
window = []
avg_rtt = 0
send_first_pkt = 0
recv_last_pkt = 0
send_packet_cnt = 0
recv_packet_cnt = 0

# log file
flog = None


def prepare_packets(file_name):
	with open(file_name, 'rb') as f:
		fdata = f.read(SEG_SIZE)
		while fdata:
			packet.append(fdata)
			fdata = f.read(SEG_SIZE)
	return len(packet)

def make_setup_message(file_name, num_of_packet, n_thread):
	msg = "0|"+ str(n_thread) + "|" + file_name + "|" + str(num_of_packet)
	return msg

def make_send_bmessage(n_seq, n_thread):
	bar = "|"
	msg = "1|"
	msg = msg.encode() + b'%5d'%(n_thread)
	msg = msg + bar.encode()
	msg = msg + b'%10d'%(n_seq)
	msg = msg + bar.encode()
	return msg

def make_end_message(n_thread):
	msg = "2|" + str(n_thread)
	return msg

def send_packet(file_name, num_of_packets, recvAddr):
	global in_flight, timer, window_size, pkt_to_send, finished, window, sendbase, send_packet_cnt
	timer = [None] * num_of_packets
	pkt_to_send = 0
	index = 0

	while True and not is_stopped:
		
		with lock:
			try :
				index = window.index(0)
				pkt_to_send = sendbase + index
				if window[index] == 0 and pkt_to_send < num_of_packets :
					msg = make_send_bmessage(pkt_to_send, 10080)
					sendSocket.sendto(msg+packet[pkt_to_send], recvAddr)
#					print("S[%d]/W[%d]"%(pkt_to_send,len(window)))
					timer[pkt_to_send] = time.time()
					window[index] = 1
					send_packet_cnt += 1			# increase packet count
			except:
				continue

		if finished:								# sender can die after receive last Ack.
			print("send finish")
			return


def recv_ack(file_name, num_of_packets, recvAddr):
	global timer, pkt_to_send, finished, window, sendbase, recv_last_pkt, recv_packet_cnt, rtt_timer
	rtt_timer = [None] * num_of_packets

	dup_cnt = 0
	Ack = 0
	expected_Ack = 0
	while True and not is_stopped:
		try:
			ack, recvAddr = sendSocket.recvfrom(4096)
			recv_packet_cnt += 1
			Ack = int(ack.decode())
#			print("\t\tA[%d]/EA[%d]"%(Ack,expected_Ack))

			if expected_Ack <= Ack:			# It's OK.
				rtt_timer[Ack] =  time.time() - timer[Ack] 
				recv_last_pkt = Ack

				dist = Ack - expected_Ack +1
				expected_Ack = Ack+1
				dup_cnt = 0
			
				with lock:
					for i in range(0,dist):
						sendbase += 1
						del window[0]
						window.append(0)
						window.append(0)

			elif expected_Ack > Ack:		# That Ack is duplicated.
				if dup_cnt == 0:
					rtt_timer[Ack] = time.time() - timer[Ack]
				dup_cnt += 1
				if dup_cnt == 3:			# 3 duplicates
					with lock:
						window.clear()
						window.append(0)
#window[0] = 0
						

			if Ack == num_of_packets-1:		# last packet is accepted.
				msg = make_end_message(10080)	# make end message start with 2.
				sendSocket.sendto(msg.encode(), recvAddr)
				finished = True
				time.sleep(1)
				return

		except timeout:
			with lock:
				sendbase = Ack+1
				window.clear()
				window.append(0)
#window.append(0)
			

def write_log():
	global flog, pkt_to_send, finished, rtt_timer, send_packet_cnt, recv_packet_cnt, recv_last_pkt

	print("time\t\t|  avg rtt\t\t|  send rate\t|  goodput" , file=flog, flush=True)
	send_first_pkt = 0
	while True and not is_stopped :
		rtt_sum = 0
		time.sleep(2)
		cnt = 0
		for rtt in rtt_timer[send_first_pkt:recv_last_pkt] :
			if rtt is not None :
				rtt_sum += rtt
				cnt += 1
		try :
			avg_rtt = rtt_sum/cnt
		except :
			avg_rtt = 1

		print("%.3f\t\t|  %.3f\t\t|  %.3f\t\t|  %.3f" %(time.time()-start_time, avg_rtt, send_packet_cnt/2, recv_packet_cnt/2) , file=flog, flush=True)
		send_packet_cnt = 0
		recv_packet_cnt = 0
		send_first_pkt = recv_last_pkt+1

def cmd():
	global is_stopped
	cmd = input('command>>')
	is_stopped = True
	print('Sender finished')

if __name__ == "__main__" :
	recvIP = input('Receiver IP address (127.0.0.1): ') or '127.0.0.1'
	file_name = input('file name (hotel.jpg): ') or 'hotel.jpg'

	command = input('command>>') or 'start 5'
	window_size = int(command.split(' ')[1])

	num_of_packets = prepare_packets(file_name)
	window = [0] * window_size

	sendSocket.settimeout(0.1)
	sendSocket.bind(sendAddr)
	port_name = str(sendSocket.getsockname()[1])

	flog = open(port_name+ "_log.txt", 'w+')
	flog = open(port_name+ "_log.txt", 'a+')

	print("number of packets to send : %d" %num_of_packets , file=flog, flush=True)

	send_thread = Thread(target=send_packet, args=(file_name, num_of_packets, (recvIP, 10080)))
	recv_thread = Thread(target=recv_ack, args=(file_name, num_of_packets, (recvIP, 10080)))
	log_thread = Thread(target=write_log, args=())
	cmd_thread = Thread(target=cmd, args=())

	start_time = time.time()

	send_thread.start()
	recv_thread.start()
	log_thread.start()
	cmd_thread.start()

	send_thread.join()
	recv_thread.join()
	log_thread.join()
	cmd_thread.join()
				  
	sendSocket.close() 
#================================================#
