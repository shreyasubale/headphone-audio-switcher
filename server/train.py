from ultralytics import YOLO
model = YOLO('yolov11n.pt')
results = model.train(data='./dataset/data.yaml', epochs=100, imgsz=640);
