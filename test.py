import os,sys 
file =os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0,file)
file = os.path.join(file,'core')
sys.path.insert(1,file)
print(os.path.dirname(os.path.realpath(__file__)))
from camera import Camera


cam = Camera (1,'keras') 

cam.configure()

cam.process_stream()
 