import io
import picamera
import threading
import time

class Frame:
    def __init__(self):
        self.frame = None

class SplitFrames(object):
    def __init__(self,frame,reset_message):
        self.output = None
        self.frame = frame
        self.reset_message = reset_message

    def write(self, buf):
        if buf.startswith(b'\xff\xd8'):
            # Start of new frame; close the old one (if any) and
            # open a new output
            if self.output:
                self.frame.frame = self.output.getvalue()
                with self.reset_message:
                        self.reset_message.notifyAll()
            # reset stream for next frame
            self.output =io.BytesIO()
        self.output.write(buf)

class Camera(object):

    def __init__(self):
        self.frame =  Frame()
        self.reset_message = threading.Condition()
        self.camera = picamera.PiCamera()
        self.state  = -1

    def start_camera(self):
        if self.state < 1:
            self.camera.resolution = (800, 600)
            self.camera.framerate = 30
            output = SplitFrames(self.frame,self.reset_message)
            self.camera.start_recording(output, format='mjpeg')
            self.state = 1
    
    def get_frame(self):
        with self.reset_message:
            self.reset_message.wait()
        return self.frame.frame
    
    def stop_camera(self):
        if self.state == 1:
            print("stopping recording")
            self.camera.stop_recording()
            self.state = 0

def gen(camera):
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

if __name__ == '__main__':
    camera = Camera()
    camera.start_camera()
    cnt = 0
    start =time.time()
    for frame in gen(camera):
        print(len(frame))
        cnt+=1
        if cnt==120:
            break
    end = time.time()
    print(end-start)
    camera.stop_camera()