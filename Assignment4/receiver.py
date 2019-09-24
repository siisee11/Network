from socket import *
from random import *
import time

# socket infomations.
recvIP = '127.0.0.1'
recvPort = 10080
recvAddr = (recvIP, recvPort)
recvSocket = socket(AF_INET, SOCK_DGRAM)

# global variables.
packet = []


def recv_and_ack(p):

    flog = None
    cum_Ack = -1

    while True:
        msg, sendAddr = recvSocket.recvfrom(4096)

        if msg[:1].decode() == '0':				# set-up message.
            msg = msg.decode()
            file_name = msg.split("|")[2]
            flog = open(file_name + "_receiving_log.txt", "w+")
            flog = open(file_name + "_receiving_log.txt", "a")

            num_of_packets = int(msg.split('|')[3])
            print("%s is ready to received" % file_name)
            print("Num of Packets : %d" % num_of_packets)

            start_time = time.time()
            packet = [None] * (num_of_packets + 1)
            all_accept = False

        elif msg[:1].decode() == '1':
            info = msg[:19].decode()
            n_port = info.split("|")[1]
            seq = int(info.split('|')[2])
            data = msg[19:]
        
            f = random()

            if f < p:		# the packet unfortunnatly dropped, so do nothing.
                print("%.3f pkt: %d\t| received" % (time.time()-start_time, seq), file=flog, flush=True)
                print("%.3f pkt: %d\t| dropped" % (time.time()-start_time, seq), file=flog, flush=True)
                continue
                    
            else:			# packet reached.
                if cum_Ack == seq-1 :			# It's OK.

                    packet[seq] = data
                    cum_Ack = packet.index(None) - 1
                                    
                    print("%.3f pkt: %d\t| received" % (time.time()-start_time, seq), file=flog, flush=True)

                    print("%.3f ACK: %d\t| sent" % (time.time()-start_time, cum_Ack), file=flog, flush=True)
                    recvSocket.sendto(str(cum_Ack).encode(), sendAddr)


                elif cum_Ack <= seq :		# It's not in order packet, save it and send missed packet.
                    packet[seq] = data

                    print("%.3f pkt: %d\t| received" % (time.time()-start_time, seq), file=flog, flush=True)
                    print("%.3f ACK: %d\t| sent" % (time.time()-start_time, cum_Ack), file=flog, flush=True)
                    recvSocket.sendto(str(cum_Ack).encode(), sendAddr)


            if cum_Ack == num_of_packets-1:
                all_accept = True

        elif msg[:1].decode() == '2':		# file transmittion completely.
            if all_accept:
                print()
                with open("../"+file_name, 'wb') as f:
                        for i in range(num_of_packets):
                            f.write(packet[i])
                print("File transfer is finished.", file=flog)
                print("Throughput: %.2f pkts / sec" % (num_of_packets/(time.time()-start_time)),file=flog, flush=True)
                return


if __name__ == "__main__":
	p = float(input('packet loss (0.02): ') or 0.02)
	
	buf_size = recvSocket.getsockopt(SOL_SOCKET, SO_RCVBUF)
	print("socket recv buffer size: %d" % buf_size)
	recvSocket.setsockopt(SOL_SOCKET, SO_RCVBUF, 10000000)
	buf_size = recvSocket.getsockopt(SOL_SOCKET, SO_RCVBUF)
	print("socket recv buffer size updated: %d" % buf_size)
	print()
	print("receiver program starts...")
		
	recvSocket.bind(recvAddr)
	while True:
		try:
			print("receiver wait...")
			recv_and_ack(p)
		except KeyboardInterrupt:
			break
			

