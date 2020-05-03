"""People Counter."""
"""
 Copyright (c) 2018 Intel Corporation.
 Permission is hereby granted, free of charge, to any person obtaining
 a copy of this software and associated documentation files (the
 "Software"), to deal in the Software without restriction, including
 without limitation the rights to use, copy, modify, merge, publish,
 distribute, sublicense, and/or sell copies of the Software, and to
 permit person to whom the Software is furnished to do so, subject to
 the following conditions:
 The above copyright notice and this permission notice shall be
 included in all copies or substantial portions of the Software.
 THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
 MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
 NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
 LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
 OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
 WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""


import os
import sys
import time
import socket
import json
import cv2

import logging as log
import paho.mqtt.client as mqtt

from argparse import ArgumentParser
from inference import Network

# Variables
CPU_EXTENSION = "/opt/intel/openvino/deployment_tools/inference_engine/lib/intel64/libcpu_extension_sse4.so"
# SDD_MODEL = "/home/workspace/ssd_mobilenet_v1_coco_2018_01_28/frozen_inference_graph.xml"
SDD_MODEL = "/home/workspace/ssd_mobilenet_v2_coco_2018_03_29/frozen_inference_graph.xml"


# MQTT server environment variables
HOSTNAME = socket.gethostname()
IPADDRESS = socket.gethostbyname(HOSTNAME)
MQTT_HOST = IPADDRESS
MQTT_PORT = 3001
MQTT_KEEPALIVE_INTERVAL = 60


def build_argparser():
    """
    Parse command line arguments.

    :return: command line arguments
    """
    parser = ArgumentParser()
    parser.add_argument("-m", "--model", required=False, type=str,
                        help="Path to an xml file with a trained model.")
    parser.add_argument("-i", "--input", required=True, type=str,
                        help="Path to image or video file")
    parser.add_argument("-l", "--cpu_extension", required=False, type=str,
                        default=None,
                        help="MKLDNN (CPU)-targeted custom layers."
                             "Absolute path to a shared library with the"
                             "kernels impl.")
    parser.add_argument("-d", "--device", type=str, default="CPU",
                        help="Specify the target device to infer on: "
                             "CPU, GPU, FPGA or MYRIAD is acceptable. Sample "
                             "will look for a suitable plugin for device "
                             "specified (CPU by default)")
    parser.add_argument("-pt", "--prob_threshold", type=float, default=0.5,
                        help="Probability threshold for detections filtering"
                        "(0.5 by default)")
    return parser


def connect_mqtt():
    ### TODO: Connect to the MQTT client ###
    client = mqtt.Client()
	client.connect(MQTT_HOST, MQTT_PORT, MQTT_KEEPALIVE_INTERVAL)
    return client


def infer_on_stream(model, args, client):
    """
    Initialize the inference network, stream video to network,
    and output stats and video.

    :param args: Command line arguments parsed by `build_argparser()`
    :param client: MQTT client
    :return: None
    """
    # Initialise the class (Inference engine)
    infer_network = Network()
	
    # Set Probability threshold for detections
    prob_threshold = args.prob_threshold

    ### TODO: Load the model through `infer_network` into IE ###
	infer_network.load_model(model, args.device, CPU_EXTENSION)
	net_input_shape = infer_network.get_input_shape()

    ### TODO: Handle the input stream ###
	# Get and open ideo capture
	cap = cv2.VideoCapture(args.input)
	cap.open(args.input)
	
	#Grab the shape of the input
	width = int(cap.get(3))
	height = int(cap.get(4))

    ### TODO: Loop until stream is over ###
	while cap.isOpened():
        ### TODO: Read from the video capture ###
		flag, frame = cap.read()
		if not flag:
			break
		key_pressed = cv2.waitKey(60)

        ### TODO: Pre-process the image as needed ###
		p_frame = cv2.resize(frame, (net_input_shape[2], net_input_shape[3]))
		p_frame = p_frame.transpose((2,0,1))
		p_frame = p_frame.reshape(1, *p_frame.shape)

        ### TODO: Start asynchronous inference for specified request ###
		infer_network.exec_net(p_frame)

        ### TODO: Wait for the result ###
		if infer_network.wait == 0:
			
            ### TODO: Get the results of the inference request ###
			result = infer_network.get_output

            ### TODO: Extract any desired stats from the results ###
			# Dummy vars
			current_count = 3
			total_count = 5
			duration = randint(50,70)			

            ### TODO: Calculate and send relevant information on ###
            ### current_count, total_count and duration to the MQTT server ###
            ### Topic "person": keys of "count" and "total" ###
            ### Topic "person/duration": key of "duration" ###
			client.publish("person", json.dumps({"count": current_count}), json.dumps({"total": total_count}))
			client.publish("person/duration", json.dumps({"duration": duration}))

        ### TODO: Send the frame to the FFMPEG server ###
		sys.stdout.buffer.write(frame)
		sys.stdout.flush()
		
		if key_pressed == 27:
			break

        ### TODO: Write an output image if `single_image_mode` ###
		
	# Release the capture and destroy any OpenCV windows
    cap.release()
    cv2.destroyAllWindows()    
    client.disconnect()	


def main():
    """
    Load the network and parse the output.

    :return: None
    """
    # Grab command line args
    args = build_argparser().parse_args()
    # Connect to the MQTT server
    client = connect_mqtt()
    # Perform inference on the input stream
	model = SDD_MODEL
    infer_on_stream(model, args, client)


if __name__ == '__main__':
    main()
