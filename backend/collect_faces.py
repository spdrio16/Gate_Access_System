import cv2
import os

# Your name label
person_name = "Ayush"

# Path to save images
dataset_path = f"data/faces/{person_name}"
os.makedirs(dataset_path, exist_ok=True)

# Load face detector
face_cascade = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")

if face_cascade.empty():
    print("Errot Loading Haar Cascade file")
    exit()
cap = cv2.VideoCapture(0)

count = 0
max_samples = 100
frame_skip = 5
save_every_n_frames = 5
print("Collecting face samples... Look at the camera");
while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame")
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.3,
        minNeighbors=5
    )

    for (x, y, w, h) in faces:
        frame_skip+=1
        if frame_skip % save_every_n_frames != 0:
            continue
        count+=1

        face = gray[y:y+h, x:x+w]
        face = cv2.resize(face, (200, 200))

        file_path = os.path.join(dataset_path, f"{count}.jpg")
        cv2.imwrite(file_path, face)

        cv2.rectangle(frame, (x, y), (x+w, y+h), (0,255,0), 2)
        print(f"Saved image {count}")

    cv2.imshow("Collecting Faces - Press Q to stop", frame)

    if cv2.waitKey(1) & 0xFF == ord('q') or count >= max_samples:
        break

cap.release()
cv2.destroyAllWindows()

print(f"Collected {count} images.")