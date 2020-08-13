import cv2
import pandas as pd
import numpy as np
from PyQt5 import QtCore
from PyQt5.QtCore import Qt

yolo_weight = "yolov3/yolov3.weights"
yolo_config = "yolov3/yolov3.cfg"
labelsPath = "yolov3/coco.names"
LABELS = open(labelsPath).read().strip().split("\n")
np.random.seed(42)
COLORS = np.random.randint(0,255,size=(len(LABELS),3),dtype="uint8")
var_confidence = 0.8
var_threshold = 0.5

net = cv2.dnn.readNetFromDarknet(yolo_config,yolo_weight)
ln = net.getLayerNames()
ln = [ln[i[0]-1] for i in net.getUnconnectedOutLayers()]

def check_result(trays,recipe,MainWindow2):
    tempmatch=0
    tempmis=0
    result = ""
    if(trays.__len__()==0):
        result="no tray"
        MainWindow2.ui.lb_result.setStyleSheet("background-color: gray;")
        
    else:
        for i in trays:
            if(i==recipe):
                tempmatch=tempmatch+1
            elif(i!=recipe):
                tempmis=tempmis+1
        if(tempmis>0):
            result="mis match"
            MainWindow2.ui.lb_result.setStyleSheet("background-color: red;")
        elif(tempmis==0):
            result="match"
            MainWindow2.ui.lb_result.setStyleSheet("background-color: green;")

    return result  

class TableModel(QtCore.QAbstractTableModel):

    def __init__(self, data):
        super(TableModel, self).__init__()
        self._data = data

    def data(self, index, role):
        if role == Qt.DisplayRole:
            value = self._data.iloc[index.row(), index.column()]
            return str(value)

    def rowCount(self, index):
        return self._data.shape[0]

    def columnCount(self, index):
        return self._data.shape[1]
    
    def headerData(self, section, orientation, role):
        # section is the index of the column/row.
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return str(self._data.columns[section])

            if orientation == Qt.Vertical:
                return str(self._data.index[section])

def tray_reader(frame):
    frame_drawed = frame
    (H,W) = frame.shape[:2]
    blob = cv2.dnn.blobFromImage(frame,1/255.0,(416,416),swapRB = True,crop=False)
    net.setInput(blob)
    layerOutputs = net.forward(ln)
    yolo_native=[]
    boxes = []
    confidences = []
    classIDs = []
    for output in layerOutputs:
        for detection in output:
            scores = detection[5:]
            classID = np.argmax(scores)
            confidence = scores[classID]
            
            if confidence > var_confidence:
                box=detection[0:4]*np.array([W,H,W,H])
                (centerX,centerY,width,height) = box.astype("int")
                x=int(centerX-(width/2))
                y=int(centerY-(height/2))
                
                # update our list of bounding box coordinates,
                # confidences, and class IDs
                boxes.append([x, y, int(width), int(height)])
                confidences.append(float(confidence))
                classIDs.append(classID)
                yolo_native.append([classID,detection[0],detection[1],detection[2],detection[3],confidence,x,y,width,height])
    
    idxs = cv2.dnn.NMSBoxes(boxes, confidences, var_confidence,var_threshold)
    
    columns_of_df = ["class","x","y","w","h","confidence","xpix","ypix","wpix","hpix"]
    df = pd.DataFrame(yolo_native,columns = columns_of_df)
    df_final=pd.DataFrame(data=None,columns = columns_of_df)
    temp=[]
    traysstr=[]
    if len(idxs) > 0:
        df = df.iloc[idxs.transpose().tolist()[0]]
        df02 = df[df["class"]==10]
        df_final=df02
        df03 = df[df["class"]!=10]
        
        for i,v in df02.iterrows():
            xbox=   int(v["xpix"])
            ybox=   int(v["ypix"])
            wbox =  int(v["wpix"])
            hbox=   int(v["hpix"])
            # box_center_x = v["x"]
            box_center_y = v["y"]
            # box_w = v["w"]
            box_h = v["h"]
            
            # box_xmin = float(box_center_x - float(box_w/2))
            # box_xmax = float(box_center_x + float(box_w/2))
            
            box_ymin = float(box_center_y - float(box_h/2))
            box_ymax = float(box_center_y + float(box_h/2))
            
            df_temp = df03.query(f"y>{box_ymin} & y<{box_ymax}")            
            df_temp= df_temp.sort_values(by=["x"])
            df_final = df_final.append(df_temp)
            
            list_temp = df_temp["class"].tolist()
            temp.append(list_temp)  
            traysstr.append(''.join([str(i) for i in list_temp]))

            tempclassID = int(v["class"])
            color = [int(c) for c in COLORS[tempclassID]]
            cv2.rectangle(frame_drawed, (xbox, ybox), (xbox + wbox, ybox + hbox), color, 2) 
            cv2.putText(frame_drawed,f"{tempclassID}",(xbox,ybox-5),cv2.FONT_HERSHEY_SIMPLEX,0.5,color,2)
                
            for ii,vv in df_temp.iterrows():
                x=int(vv["xpix"])
                y=int(vv["ypix"])
                w = int(vv["wpix"])
                h= int(vv["hpix"])
                tempclassID = int(vv["class"])
                color = [int(c) for c in COLORS[tempclassID]]
                cv2.rectangle(frame_drawed, (x, y), (x + w, y + h), color, 2) 
                cv2.putText(frame_drawed,f"{tempclassID}",(x,y-5),cv2.FONT_HERSHEY_SIMPLEX,0.5,color,2)
    traysdf=pd.DataFrame(traysstr,columns=["trayid"])
    return  df_final,temp,traysstr,traysdf,frame_drawed
