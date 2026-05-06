import cv2
import numpy as np
import os
import time

# ============================
# Setup Paths
# ============================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UNKNOWN_FOLDER = os.path.join(BASE_DIR, "data", "unknown")

os.makedirs(UNKNOWN_FOLDER, exist_ok=True)

# ============================
# Load Model
# ============================
model = cv2.face.LBPHFaceRecognizer_create()
model.read(os.path.join(BASE_DIR, "face_model.yml"))

label_map = np.load(os.path.join(BASE_DIR, "label_map.npy"), allow_pickle=True).item()

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
)

cap = cv2.VideoCapture(0)

# ============================
# Control variables
# ============================
last_saved_time = 0
SAVE_INTERVAL = 5
person_folder = None

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

        # Known
        if confidence < 50:
            name = label_map[label]
            gate_status = "UNLOCKED"
            color = (0, 255, 0)
            text = f"{name} - ACCESS GRANTED"
            person_folder = None  # reset

        # Unknown
        else:
            gate_status = "LOCKED"
            color = (0, 0, 255)
            text = "UNKNOWN - SENT TO ADMIN"

            # New person (after cooldown)
            if current_time - last_saved_time > SAVE_INTERVAL:
                person_id = f"person_{int(current_time)}"
                person_folder = os.path.join(UNKNOWN_FOLDER, person_id)
                os.makedirs(person_folder, exist_ok=True)
                last_saved_time = current_time

            # Save multiple images
            if person_folder:
                file_name = os.path.join(
                    person_folder,
                    f"{int(time.time()*1000)}.jpg"
                )
                cv2.imwrite(file_name, face)

        # Draw box
        cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)

        cv2.putText(frame, text, (x, y-10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8, color, 2)

    cv2.putText(frame, f"GATE: {gate_status}", (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1, (255, 255, 255), 3)

    cv2.imshow("Gate Access System", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()