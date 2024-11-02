from ultralytics import YOLO
model = YOLO('yolov11n.pt')
results = model.train(data='data.yaml', epochs=100, imgsz=640);
