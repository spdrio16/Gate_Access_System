import cv2
import numpy as np
import os
import time
from datetime import datetime

# ============================
# Paths
# ============================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UNKNOWN_FOLDER = os.path.join(BASE_DIR, "data", "unknown")
LOG_FILE = os.path.join(BASE_DIR, "logs.txt")

os.makedirs(UNKNOWN_FOLDER, exist_ok=True)

# ============================
# Logging Function
# ============================
def log_event(name, status):
    with open(LOG_FILE, "a") as f:
        time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"{name} - {time_now} - {status}\n")


# ============================
# Load Model
# ============================
model = cv2.face.LBPHFaceRecognizer_create()
model.read(os.path.join(BASE_DIR, "face_model.yml"))

label_map = np.load(
    os.path.join(BASE_DIR, "label_map.npy"),
    allow_pickle=True
).item()

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
)

cap = cv2.VideoCapture(0)

# ============================
# Control variables
# ============================
last_person_time = 0
SAVE_INTERVAL = 5   # seconds (new person)
SAVE_IMAGE_INTERVAL = 0.5  # seconds (same person images)
last_image_save = 0

current_person_folder = None

while True:
    ret, frame = cap.read()
    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    gate_status = "LOCKED"

    for (x, y, w, h) in faces:
        face = gray[y:y+h, x:x+w]
        face = cv2.resize(face, (200, 200))

        label, confidence = model.predict(face)
        current_time = time.time()

        # ============================
        # KNOWN PERSON
        # ============================
        if confidence < 60:
            name = label_map[label]
            gate_status = "UNLOCKED"
            color = (0, 255, 0)
            text = f"{name} - ACCESS GRANTED"

            # Log once every 5 sec
            if current_time - last_person_time > 5:
                log_event(name, "ACCESS GRANTED")
                last_person_time = current_time

            current_person_folder = None

        # ============================
        # UNKNOWN PERSON
        # ============================
        else:
            gate_status = "LOCKED"
            color = (0, 0, 255)
            text = "UNKNOWN"

            # Create NEW person folder
            if current_time - last_person_time > SAVE_INTERVAL:
                person_id = f"person_{int(current_time)}"
                current_person_folder = os.path.join(UNKNOWN_FOLDER, person_id)

                os.makedirs(current_person_folder, exist_ok=True)

                print("Created folder:", current_person_folder)

                log_event("Unknown", "DETECTED")

                last_person_time = current_time

            # Save images (controlled rate)
            if current_person_folder and (current_time - last_image_save > SAVE_IMAGE_INTERVAL):
                filename = os.path.join(
                    current_person_folder,
                    f"{int(time.time()*1000)}.jpg"
                )
                cv2.imwrite(filename, face)
                last_image_save = current_time

        # Draw rectangle
        cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)

        # Put text
        cv2.putText(frame, text, (x, y-10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8, color, 2)

    # Gate status display
    cv2.putText(frame, f"GATE: {gate_status}", (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1, (255, 255, 255), 3)

    cv2.imshow("Gate Access System", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()