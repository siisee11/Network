from socket import *
import os
from threading import Thread
import threading
import time

# file segment size per packet.
SEG_SIZE = 1300

# server information.
sendIP = '127.0.0.1'
sendPort = 0
sendAddr = (sendIP, sendPort)
sendSocket = socket(AF_INET, SOCK_DGRAM)

# global time.
start_time = time.time()

# lock variables.
lock = threading.Lock()

# global variables.
window_size = 0
ack = -1
packet = []
timer = []
pkt_to_send = 0
sendbase = 0
finished = False
window = []

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
    global in_flight, timer, window_size, pkt_to_send, finished, window, sendbase
    timer = [None] * num_of_packets
    flog = open(file_name + "_sending_log.txt", 'a+')
    pkt_to_send = 0
    index = 0

    while True:
        
        with lock:
            try :
                index = window.index(0)
                for i in range(index, len(window)):
                    pkt_to_send = sendbase + i
                    if window[i] == 0 and pkt_to_send < num_of_packets :
                        send_time = time.time() - start_time
                        timer[pkt_to_send] = send_time
                        print("%.3f pkt: %d\t| Sent  | (sb,i) (%d,%d)" % (send_time, pkt_to_send, sendbase, i), file=flog, flush=True)
                        
                        msg = make_send_bmessage(pkt_to_send, 10080)
                        sendSocket.sendto(msg+packet[pkt_to_send], recvAddr)
                        window[i] = 1
                        
                        pkt_to_send += 1				# next packet number.
            except:
                continue

        if finished:          # sender can die after receive last Ack.
            print("send finish")
            return


def recv_ack(file_name, num_of_packets, recvAddr):
    global timer, pkt_to_send, finished, window, sendbase

    flog = open(file_name + "_sending_log.txt", 'a+')

    dup_cnt = 0
    Ack = 0
    expected_Ack = 0
    while True:
        try:
            ack, recvAddr = sendSocket.recvfrom(4096)
            Ack = int(ack.decode())
            print("%.3f ACK: %d\t| received | expected Ack : %d" % (time.time() - start_time, Ack, expected_Ack), file=flog, flush=True)

            if expected_Ack <= Ack:			# It's OK.
                dist = Ack - expected_Ack +1
                expected_Ack = Ack+1
                dup_cnt = 0
            
                with lock:
                    for i in range(0,dist):
                        sendbase += 1
                        del window[0]
                        window.append(0)

            elif expected_Ack > Ack:		# That Ack is duplicated.
                dup_cnt += 1
                if dup_cnt == 3:			# 3 duplicates
                    with lock:
                        retrans_time = time.time() - start_time
                        print("%.3f pkt: %d\t| 3 duplicated ACKs" % (retrans_time, Ack), file=flog, flush=True)
                        window[0] = 0
                        

            if Ack == num_of_packets-1:		# last packet is accepted.
                msg = make_end_message(10080)	# make end message start with 2.
                sendSocket.sendto(msg.encode(), recvAddr)
                finished = True
                time.sleep(1)
                print()
                print()
                print("File transfer is finished.", file=flog, flush=True)
                print("Throughput: %.2f pkts / sec" % (num_of_packets/(time.time() - start_time)), file=flog, flush=True)
                return

        except timeout:
            with lock:
                time_out_time = time.time() - start_time
                print("%.3f pkt: %d\t| timeout since %.3f" %(time_out_time, expected_Ack, timer[expected_Ack]), file=flog, flush=True)
                msg = make_send_bmessage(expected_Ack, 10080)
                sendSocket.sendto(msg + packet[expected_Ack], recvAddr)
                timer[expected_Ack] = time_out_time
                print("%.3f pkt: %d\t| retransmitted" % (time_out_time, expected_Ack), file=flog, flush=True)
            

if __name__ == "__main__" :
    recvIP = input('Receiver IP address (127.0.0.1): ') or '127.0.0.1'
    window_size = int(input('window size (8): ') or 8)
    time_out = float(input('time out (0.05): ') or 0.05)
    print()
    file_name = input('file name (hotel.jpg): ') or 'hotel.jpg'

    sendSocket.settimeout(time_out)
    num_of_packets = prepare_packets(file_name)
    window = [0] * window_size

    sendSocket.bind(sendAddr)
    message = make_setup_message(file_name, num_of_packets, 10080)
    sendSocket.sendto(message.encode(), (recvIP, 10080))  # send 0 setup message

    open(file_name+"_sending_log.txt", "w+")	# to clear data if it exist.

    send_thread = Thread(target=send_packet, args=(file_name, num_of_packets, (recvIP, 10080)))
    recv_thread = Thread(target=recv_ack, args=(file_name, num_of_packets, (recvIP, 10080)))


    start_time = time.time()

    send_thread.start()
    recv_thread.start()
    send_thread.join()
    recv_thread.join()
                  
    sendSocket.close() 
    #================================================#
