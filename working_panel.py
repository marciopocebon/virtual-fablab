bl_info = {"name": "control object","category": "User"}

import bpy
import serial
import time
import queue
import serial.tools.list_ports
import threading
import sys
import ctypes
from ctypes import *
from bpy.app.handlers import persistent
from bpy.props import EnumProperty

class SerialLink(threading.Thread):
    # Thread for reading the usb port and adding to the queue 
    _ser = None
    _open = None
    def __init__(self,name,q, qlock):
        threading.Thread.__init__(self)
        self.name = name
        self.q = q
        self.qlock = qlock
    def addBuffer1(self):
        try:
            #print("add buffer")
            quit = 0
            ctr = 0
            tempB = 0
            tempC = 0
            defA, defB, defC = None, None, None
            s = threading.currentThread()
            connection = self.openConnection()
            if not connection:
                bpy.context.scene.enable_prop = '0'    
            while getattr(s,"do_run", True) and connection: # waits for the event for the blender window
                try:
                    #print("print asd")
                    line = self._ser.readline()
                    #print("add buffer mk2")
                    line = line.decode('utf-8')
                    if not line.find("demo") == -1:
                        self._ser.write(str.encode("a"))
                        defA = None
                        ctr = 0
                        continue
                    else:
                        line = line.strip('\r\n')
                        line = line.split('\t')
                        print(line)
                        if len(line) == 6:
                            self.qlock.acquire()
                            a = float(line[1])
                            b = float(line[2])
                            c = float(line[3])
                            zoom1 = line[4]
                            zoom2 = line[5]
                            if (zoom1 == "0" and float(zoom2) > 55):
                                ctr_zoom += 1
                                if (ctr_zoom % 2 == 1):
                                    zoom(-1)
                            elif (zoom1 == "0"):
                                ctr_zoom += 1
                                if (ctr_zoom % 2 == 1):
                                    zoom(1)   
                            else:
                                ctr_zoom = 0
                            if ctr < 5:
                                #print("aasi")
                                if (c == tempC and b == tempB):
                                    ctr += 1
                                    print(ctr)
                                else:
                                    #print("else ctr")
                                    ctr = 0
                                tempC = c
                                tempB = b
                                if ctr == 3:
                                    defA, defB, defC = float(a), float(b), float(c)
                                    ctr = 6
                                    print("YAW alustettu")
                            
                            if defA:
                                if a > defA + 30 or a < defA - 30 or b > defB + 30 or b < defB - 30 or c > defC + 30 or c < defC - 30:
                                    #print(line)
                                    line.append(defB)
                                    line.append(defC)
                                    self.q.put(line)
                            
                            #q.put(line)
                        #print(line)
                        #q.put(line)
                            self.qlock.release()
                except TypeError:
                    pass
                    #print("type error")
                except UnicodeError:
                    pass
                except ValueError:
                    pass
                except KeyboardInterrupt:
                    pass
        except serial.serialutil.SerialException: # FileNotFoundError
            print("Serial error!!")

    def openConnection(self):
        """Opens the connection to the arduino device and returns TRUE if successful"""
        ports = []
        port = None
        ctr = 0
        while port == None:
            if  bpy.context.scene.enable_prop == '0':
                return False    
            ctr += 1
            if (ctr > 4):
                print("Couldn't find arduino in reasonable time exiting program")
                return False
            time.sleep(5)
            print("checking for arduino connected to a usb port")
            ports = list(serial.tools.list_ports.comports())
            if sys.platform.startswith('win'):
                for a in ports:
                    if "Arduino" in a[1]:
                        port = a[0]
                if port == None:
                    print("Arduino not found retrying in 5 seconds")
                    continue
            elif sys.platform.startswith('linux'):
                if len(ports) > 0:
                    for b in ports:
                        port = b[0]
        closed = False
        ctr = 0
        while not closed:
            if  bpy.context.scene.enable_prop == '0':
                return False
            try:
                self._ser = serial.Serial(port,115200, write_timeout=5) # opens the serial connection
                closed = True
            except SerialException:
                print("problem opening connection retrying in 5 seconds")
                ctr += 1
                if (ctr > 4):
                    print("Couldn't find open serial port in reasonable time exiting program")
                    return False
                time.sleep(5)
        write = False
        ctr = 0
        while not write: # tries to write to the arduino so that the arduino knows to start sending data
            if  bpy.context.scene.enable_prop == '0':
                return False
            try:
                self._ser.write(str.encode('A')) # the arduino waits for a character to start sending data
                print("Sent character to arduino")
                print("calibrating")
                time.sleep(10) # waits for 10 seconds so that the accelerometer values normalise
                print("done calibrating")
                write =  True
            except:
                print("Couldn't write to the serial port\nRetrying in 5 seconds")
                ctr += 1
                if (ctr > 4):
                    print("Couldn't find write to the serial port in reasonable time exiting program")
                    return False
        return True

    def closeSerial(self):
        self._ser.close()

    def run(self):
        time.sleep(3)
        print("slept")
        self.addBuffer1()

class ModalTimerOperator(bpy.types.Operator):
    """Operator which runs its self from a timer"""
    bl_idname = "wm.modal_timer_operator"
    bl_label = "Modal Timer Operator"
    _timer = None
    
    def rotateObject(self):
        #try:
        obj = bpy.context.active_object
        #print("rota")
        if not p.q.empty():
            #print("ting")
            p.qlock.acquire()
            line = p.q.get();
            a = float(line[1])
            b = float(line[2])
            c = float(line[3])
            defB = float(line[6])#  when button has been added 
            defC = float(line[7])# 
            pi = 3.14159265358979
            p.qlock.release()
            #obj.rotation_euler = (b , c , a)
            
            """Determines the object rotation directions and if the sensor has moved enough to rotate the object"""
            if a > obj.rotation_euler.z + 30:
     #           rotation.append("+a")
                #obj.rotation_euler.z -= pi/16
                pass
                           
            if a < obj.rotation_euler.z - 30:
    #            rotation.append("-a")       
                #obj.rotation_euler.z += pi/16
                pass
                    
            if c > defC + 30: # c < obj.rotation_euler.y + 30
                #rotation.append("+b") 
                obj.rotation_euler.y += pi/16
                #pass     
            if c < defC - 30: # c > obj.rotation_euler.y
                #rotation.append("-b")
                obj.rotation_euler.y -= pi/16
                #pass
                    
            if b > defB + 30: # b > obj.rotation_euler.x
                #rotation.append("+c") 
                obj.rotation_euler.x += pi/16     
                #pass
            if b < defB - 30: # b > obj.rotation_euler.x
                #rotation.append("-c")
                obj.rotation_euler.x -= pi/16
                #pass
            
            #time.sleep(0.1)
        #bpy.ops.transform.rotate(value=0.283/8, axis=(0,0,1))
        #except KeyboardInterrupt:

    def modal(self, context, event):
        
        if event.type in {'RIGHTMOUSE', 'ESC'} or context.scene.enable_prop == '0':
            self.cancel(context)
            print("Exiting program")
            p.do_run = False
            try:
                p.closeSerial() # try to close the serial
            except:
                pass
            try:
                p.qlock.release() # release the queue lock if it is locked
            except RuntimeError:
                pass
                #print("runtime error")
            p.join()
            
            # Updating panel once after program has stopped            
            context.scene.enable_prop = '0'
            for area in bpy.context.screen.areas:
                if area.type == 'VIEW_3D':
                    area.tag_redraw()
            return {'FINISHED'}

        if event.type == 'TIMER':
            self.rotateObject()

        return {'PASS_THROUGH'}

    def execute(self, context):
        wm = context.window_manager
        self._timer = wm.event_timer_add(time_step=0.01, window=context.window)
        #rotateCamera()
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)
    
class TestPanel(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    
    bl_category = "Edit Object"  # name seen in tab
    bl_label = "Edit Object" # caption of the opened panel
    bl_idname = "test_panel"  # unique hidden name of each panel
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_context = "objectmode"  # sculpt?           
 
    def draw(self, context):
        scene = context.scene
                       
        layout = self.layout
        layout.label("Status")

        layout.prop(scene, 'enable_prop', expand=True)
        
        row = layout.row()
        layout.label("Toggle this to run the program", icon='INFO')
                       
        # Using property and number of threads to run actual program       
        t = threading.enumerate()
        if scene.enable_prop == '1' and len(t) == 1:
            #print("Enabled")
            run()  # Launch the main program

# Definition of point structure - Windows
class POINT(Structure):
    _fields_ = [("x", c_ulong), ("y", c_ulong)]

# Get cursor position - Windows
def getCursorPosition():
   point = POINT()
   windll.user32.GetCursorPos(byref(point))
   return point.x, point.y

# Set cursor position - Windows
def setCursorPosition(x, y):
   windll.user32.SetCursorPos(x, y)

# Left mouse button click - Windows
def click():
    ctypes.windll.user32.mouse_event(0x2, 0,0,0,0)    # MouseLeft clicked Down
    ctypes.windll.user32.mouse_event(0x4, 0,0,0,0)    # MouseLeft clicked Up
    
# Get coordinates for center of screen - Windows
def getScreenCenter():
    user32 = ctypes.windll.user32
    x = int(user32.GetSystemMetrics(0)/2)
    y = int(user32.GetSystemMetrics(1)/2)
    return x, y
       
def zoom(value):
    # can cause blender to crash
    #value = 1 #If value > 0 = zoom in, value < 0 = zoom out
    for window in bpy.context.window_manager.windows:
        screen = window.screen
        for area in screen.areas: 
            if area.type == 'VIEW_3D':
                #bpy.ops.object.mode_set(mode = 'EDIT')
                for region in area.regions:
                    if region.type == 'WINDOW':
                        override = {'blend_data': bpy.context.blend_data,'mode': 'SCULPT','active_object': bpy.context.scene.objects.active,'scene': bpy.context.scene,'window': window, 'screen': screen, 'area': area, 'region': region}
                        bpy.ops.view3d.zoom(override, delta=value, mx=0, my=0)
                        #bpy.ops.object.mode_set(mode='SCULPT')
                        break

def rotateCamera():
    #bpy.ops.object.delete(use_global=False)
    #bpy.ops.mesh.primitive_cube_add()
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            override = bpy.context.copy()
            override['area'] = area
            bpy.ops.view3d.viewnumpad(override, type = 'FRONT')
            #bpy.ops.view3d.view_orbit(type = 'ORBITUP')
            bpy.ops.object.mode_set(mode = 'EDIT')
            #bpy.ops.mesh.subdivide(number_cuts = 20)
            bpy.ops.object.mode_set(mode='SCULPT')
            bpy.ops.screen.screen_full_area(override, use_hide_panels=True)
            break

"""https://blenderartists.org/forum/showthread.php?340820-How-to-start-a-Modal-Timer-at-launch-in-an-addon
was used as a guideline how to implement modal timer operator in a blender addon"""
@persistent
def my_handler2(scene):
    bpy.ops.wm.modal_timer_operator()
    bpy.app.handlers.frame_change_post.remove(my_handler2)

@persistent
def my_handler(scene):
    bpy.app.handlers.frame_change_post.append(my_handler2)
    bpy.context.scene.frame_current=bpy.context.scene.frame_current            
    bpy.app.handlers.scene_update_post.remove(my_handler)


def run():
    global p
    qlock = threading.Lock() # thread lock
    q = queue.Queue() # the queue
    p = SerialLink('serial thread',q, qlock) # create the thread
    p.start()
    
    bpy.app.handlers.scene_update_post.append(my_handler)
    print("Thread made and establishing connecion with arduino device")

    #rotateCamera()
    if sys.platform.startswith('win'):
        width, height = getScreenCenter()
        setCursorPosition(width, height)

def register():
    bpy.types.Scene.enable_prop = bpy.props.EnumProperty(items = (('0','Stop', ''),('1','Run','')))
    bpy.utils.register_module(__name__)  
     
def unregister():
    bpy.utils.unregister_module(__name__)   
    del bpy.types.Scene.enable_prop


if __name__ == "__main__":
    register() #  running from text editor