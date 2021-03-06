import cv2
import numpy as np
from elements.yolo_pc import OBJ_DETECTION
from email_sender import send_email
import requests
import time
from check_internet_connectivity import is_connected
#from pyembedded.raspberry_pi_tools.raspberrypi import PI
#pi = PI()

prev_time = 0
new_time = time.time()
record_time = time.time()

video_sent_status = False
number_of_person_detected = 0
previous_number_of_person_detected = {}
previous_number_of_person_detected = {'Number' : 0 , 'Time' : time.time()}
meta_of_number_of_person_detected = {'Number' : 0 , 'frame_number' : 0}
frames_counter = 0
frames = []
not_detected_frames_thresh = 10
number_of_frames_not_detected = 0

Object_classes = ['person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat', 'traffic light',
                'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse', 'sheep', 'cow',
                'elephant', 'bear', 'zebra', 'giraffe', 'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee',
                'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard',
                'tennis racket', 'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple',
                'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch',
                'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse', 'remote', 'keyboard', 'cell phone',
                'microwave', 'oven', 'toaster', 'sink', 'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear',
                'hair drier', 'toothbrush' ]

#Object_colors = list(np.random.rand(80,3)*255)
Object_detector = OBJ_DETECTION('./yolov5n-fp16.tflite', Object_classes)
# Return true if line segments AB and CD intersect
# To flip the image, modify the flip_method parameter (0 and 2 are the most common)
#print(gstreamer_pipeline(flip_method=0))
#cap = cv2.VideoCapture(gstreamer_pipeline(flip_method=0), cv2.CAP_GSTREAMER)
cap = cv2.VideoCapture('./person.mp4')
#serial = getserial()
#registration_status = register(serial)
#if(registration_status == "Device id written to file"):
#    #read the device id from the text file
#    with open('device_id.txt', 'r') as f:
#        device_id = f.read()
#        f.close()

if(prev_time == 0):

    #status_of_device = request_status(device_id)
    #status_of_device = 'false'

    prev_time = new_time
    new_time = time.time()


while cap.isOpened():

    REMOTE_SERVER = "www.google.com"
    if is_connected(REMOTE_SERVER):
        print("connected")
        cache = False

    else:
        print("not connected")
        cache = True
    
    #window_handle = cv2.namedWindow("CSI Camera", cv2.WINDOW_AUTOSIZE)
    # Window
    #while cv2.getWindowProperty("CSI Camera", 0) >= 0 :
    ret, frame = cap.read()
    new_time = time.time()
    #print("Previous Time", prev_time)
    #print("New Time", new_time)

    if((new_time - prev_time) >= 10):

        #status_of_device = request_status(device_id)
        #print(status_of_device)
        #status_of_device = 'true'

        prev_time = new_time
        new_time = time.time()

    if ret:
        # detection process
        objs = Object_detector.detect(frame)
        dets = []
        # plotting
        
        number_of_person_detected = 0

        for obj in objs:
            # print(obj)
            label = obj['label']
            if((label == 'person')):
                number_of_frames_not_detected = 0
                number_of_person_detected +=1
                #print(label)
                score = obj['score']
                [(xmin,ymin),(xmax,ymax)] = obj['bbox']
                #print(xmin,ymin,xmax,ymax)
                (x, y) = (xmin, ymin)
                (w, h) = ((xmax-xmin),(ymax-ymin))
                #color = Object_colors[Object_classes.index(label)]
                frame = cv2.rectangle(frame, (xmin,ymin), (xmax,ymax), (255,0,0), 2) 
                frame = cv2.putText(frame, f'{label} ({str(score)})', (xmin,ymin), cv2.FONT_HERSHEY_SIMPLEX , 0.75, (0,255,255), 1, cv2.LINE_AA)


            


        frames_counter = frames_counter + 1
        frames.append(frame)
        if(frames_counter < 100):
            frames_counter = frames_counter + 1
            frames.append(frame)
        elif(frames_counter >= 100):
            #write a list of frames in a video
            out = cv2.VideoWriter('output.mp4',cv2.VideoWriter_fourcc(*'mp4v'), 60, (frame.shape[1],frame.shape[0]))
            for i in range(len(frames)):
                out.write(frames[i])
            out.release()
        
        if(number_of_person_detected > meta_of_number_of_person_detected['Number'] or number_of_person_detected < meta_of_number_of_person_detected['Number']):
            meta_of_number_of_person_detected['Number'] = number_of_person_detected
            meta_of_number_of_person_detected['frame_number'] = 1


        if(number_of_person_detected == meta_of_number_of_person_detected['Number']):
            meta_of_number_of_person_detected['frame_number'] += 1
        
        print("Frames Counter", frames_counter)
        print("Number of person detected:", meta_of_number_of_person_detected, "Previous number of person detected:", previous_number_of_person_detected)
        if((meta_of_number_of_person_detected['Number'] > previous_number_of_person_detected['Number']) and meta_of_number_of_person_detected['frame_number'] > 10):
            print("New Person Detected")
            previous_number_of_person_detected['Number'] = meta_of_number_of_person_detected['Number']
            #previous_number_of_person_detected['Time'] = number_of_person_detected['Time']
            if(video_sent_status == True):
                video_sent_status = False
                #frames_counter = 0


        elif((meta_of_number_of_person_detected['Number'] < previous_number_of_person_detected['Number']) and meta_of_number_of_person_detected['frame_number'] > 10):
            print("Person Detected Reduced")
            previous_number_of_person_detected['Number'] = meta_of_number_of_person_detected['Number']
            #previous_number_of_person_detected['Time'] = number_of_person_detected['Time']
            if(video_sent_status == True):
                video_sent_status = False
                frames_counter = 0


        if(video_sent_status == False and previous_number_of_person_detected['Number'] > 0):

            if is_connected(REMOTE_SERVER):
                print("connected")
                cache = False

            else:
                print("not connected")
                cache = True

            


            if(frames_counter < 100):
                frames_counter = frames_counter + 1
                frames.append(frame)
            elif(frames_counter >= 100):
                #write a list of frames in a video
                out = cv2.VideoWriter('output.mp4',cv2.VideoWriter_fourcc(*'h264'), 60, (frame.shape[1],frame.shape[0]))
                for i in range(len(frames)):
                    out.write(frames[i])
                out.release()
                video_sent_status = True
                if video_sent_status == True:
                    print("Video sent")
                frames = []

        print("Number of Frames not detected" , number_of_frames_not_detected)
        if(number_of_frames_not_detected < not_detected_frames_thresh and number_of_person_detected == 0):
                number_of_frames_not_detected = number_of_frames_not_detected + 1
        elif(number_of_frames_not_detected >= not_detected_frames_thresh and number_of_person_detected == 0):
                video_sent_status = False
                frames_counter = 0
                frames = []
                number_of_person_detected = 0
                previous_number_of_person_detected['Number'] = 0


            #previous_number_of_person_detected = number_of_person_detected
        

        

    if(time.time() - record_time >= 1):
        record_time = time.time()
        #write_log(number_of_person_detected)

    cv2.imshow("CSI Camera", frame)
    keyCode = cv2.waitKey(30)
    if keyCode == ord('q'):
        break      
cap.release()
cv2.destroyAllWindows()