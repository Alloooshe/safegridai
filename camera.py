'''
file contains camera  class, which perform face detection and mask detection on a stream 
'''
import tensorflow as tf
from keras.models import model_from_json
import cv2
import numpy as np 
from utils.anchor_generator import generate_anchors
from utils.anchor_decode import decode_bbox
from utils.nms import single_class_non_max_suppression
import os 
import time 
from tracking.sort import Sort

class Camera():
    
    
    def __init__(self,cam_id,model_name="keras"): 
        self.camera_id=cam_id 
        self.model = None 
        self.model_name= model_name
        self.stream_string = 0
        self.anchors = None 
        self.id2class = {0: 'Mask', 1: 'NoMask'}
        self.models_dir = os.path.dirname(os.path.realpath(__file__))
        self.models_dir =os.path.join(self.models_dir,'core')
        self.models_dir =os.path.join(self.models_dir,'models')
        self.tflite_input_details =None
        self.tflite_output_details =None
        self.track_model = Sort()
        
    def configure(self):
        #loading inference model 
        if self.model_name == 'tflite': 
            filename =os.path.join(self.models_dir,'face_mask_detection.tflite')
            self.model= tf.lite.Interpreter(model_path=filename)
            self.model.allocate_tensors()
            self.tflite_input_details =  self.model.get_input_details()
            self.tflite_output_details =  self.model.get_output_details()
            
        else : 
            filename =os.path.join(self.models_dir,'face_mask_detection.json')
            self.model = model_from_json(open(filename).read())
            filename =os.path.join(self.models_dir,'face_mask_detection.hdf5')
            self.model.load_weights(filename)
        # anchor configuration
        feature_map_sizes = [[33, 33], [17, 17], [9, 9], [5, 5], [3, 3]]
        anchor_sizes = [[0.04, 0.056], [0.08, 0.11], [0.16, 0.22], [0.32, 0.45], [0.64, 0.72]]
        anchor_ratios = [[1, 0.62, 0.42]] * 5
        # generate anchors
        self.anchors = generate_anchors(feature_map_sizes, anchor_sizes, anchor_ratios)
        self.anchors = np.expand_dims(self.anchors, axis=0)
        
        return 0 
    
    
    
    def process_stream(self):
        cap = cv2.VideoCapture(self.stream_string)
        if not cap.isOpened():
            raise ValueError("Video open failed.")
            return
        status = True
        while status:
            if cv2.waitKey(1) & 0xFF == ord("q"):
                 print('breaking ..')
                 print('breaking processing on camera #',self.camera_id)
                 cap.release()
                 cv2.destroyAllWindows()
                 break
            status, img_raw = cap.read()
      
            if (status):
                s=time.time()
                output_info,image = self.inference(img_raw,target_shape=(260, 260))
                e=time.time()
                print('frame time '+str(round(e-s,2)))
                cv2.imshow('feed', image)
        cap.release()
        cv2.destroyAllWindows()
        return 0 
    
    def inference (self,image ,target_shape=(260, 260), conf_thresh=0.5,iou_thresh=0.4):
        output_info = []
        height, width, _ = image.shape
        image_resized = cv2.resize(image, target_shape)
        image_np = image_resized / 255.0
        image_exp = np.expand_dims(image_np, axis=0)
        image_exp=np.array(image_exp,dtype=np.float32)
        if self.model_name =="keras" : 
            result = self.model.predict(image_exp)
            y_bboxes_output= result[0]
            y_cls_output = result[1]
        elif self.model_name =="tflite":
          
            self.model.set_tensor(self.tflite_input_details[0]['index'], image_exp)
            self.model.invoke()
            y_bboxes_output= self.model.get_tensor(self.tflite_output_details[0]['index'] )
            y_cls_output = self.model.get_tensor(self.tflite_output_details[1]['index'] )
            
        # remove the batch dimension, for batch is always 1 for inference.
        y_bboxes = decode_bbox(self.anchors, y_bboxes_output)[0]
        y_cls = y_cls_output[0]
        # To speed up, do single class NMS, not multiple classes NMS.
        bbox_max_scores = np.max(y_cls, axis=1)
        bbox_max_score_classes = np.argmax(y_cls, axis=1)
    
        # keep_idx is the alive bounding box after nms.
        keep_idxs = single_class_non_max_suppression(y_bboxes,
                                                     bbox_max_scores,
                                                     conf_thresh=conf_thresh,
                                                     iou_thresh=iou_thresh,
                                                     )
        
        
        for idx in keep_idxs:
            conf = float(bbox_max_scores[idx])
            class_id = bbox_max_score_classes[idx]
            bbox = y_bboxes[idx]
            # clip the coordinate, avoid the value exceed the image boundary.
            xmin = max(0, int(bbox[0] * width))
            ymin = max(0, int(bbox[1] * height))
            xmax = min(int(bbox[2] * width), width)
            ymax = min(int(bbox[3] * height), height)
            if class_id == 0:
                color = (0, 255, 0)
            else:
                color = (255, 0, 0)
            cv2.rectangle(image, (xmin, ymin), (xmax, ymax), color, 2)
            cv2.putText(image, "%s: %.2f" % (self.id2class[class_id], conf), (xmin + 2, ymin - 2),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, color)
            output_info.append([ xmin, ymin, xmax, ymax,conf,class_id])
        output_info = np.array(output_info)
        print('output info ',output_info)
      #  boxes = self.track_model.update(output_info)
      #  print('boxes shape ', boxes.shape)
      #  print('boxes ', boxes)
        return output_info,image 
    
   
        
    def clean(self):
        return 0 