import cv2
import numpy as np
import os

# === CONFIGURATION ===
CHECKERBOARD = (8, 6)  # Number of inner corners (columns, rows)
VIDEO_PATH = 'data/chessboard.avi'
OUTPUT_FOLDER = 'output'
UNDISTORTED_FOLDER = 'undistorted'
CALIBRATION_FILE = 'calibration_data.npz'

# === CREATE FOLDERS ===
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(UNDISTORTED_FOLDER, exist_ok=True)

# === PREPARE OBJECT POINTS ===
objp = np.zeros((CHECKERBOARD[0] * CHECKERBOARD[1], 3), np.float32)
objp[:, :2] = np.mgrid[0:CHECKERBOARD[0], 0:CHECKERBOARD[1]].T.reshape(-1, 2)

objpoints = []
imgpoints = []

# === OPEN VIDEO ===
cap = cv2.VideoCapture(VIDEO_PATH)
frame_id = 0
corner_detected_count = 0

print("[INFO] Detecting chessboard corners...")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Improve corner detection with flags
    flags = cv2.CALIB_CB_ADAPTIVE_THRESH + cv2.CALIB_CB_NORMALIZE_IMAGE
    ret_corners, corners = cv2.findChessboardCorners(gray, CHECKERBOARD, flags)

    if ret_corners:
        corner_detected_count += 1
        objpoints.append(objp)
        corners2 = cv2.cornerSubPix(
            gray, corners, (11,11), (-1,-1),
            (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
        )
        imgpoints.append(corners2)
        cv2.drawChessboardCorners(frame, CHECKERBOARD, corners2, ret_corners)
        cv2.imwrite(f'{OUTPUT_FOLDER}/frame_{frame_id:03d}.png', frame)

    frame_id += 1

cap.release()
print(f"[INFO] Chessboard corners detected in {corner_detected_count} frames")

# === CALIBRATION ===
if corner_detected_count == 0:
    print("[ERROR] No chessboard corners were detected. Please check the video or checkerboard size.")
    exit()

print("[INFO] Performing camera calibration...")
ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)

# Save calibration
np.savez(CALIBRATION_FILE, mtx=mtx, dist=dist, rvecs=rvecs, tvecs=tvecs, error=ret)

print("\n✅ Calibration Complete:")
print("Camera Matrix:\n", mtx)
print("Distortion Coefficients:\n", dist.ravel())
print("Reprojection Error (RMSE):", ret)

# === UNDISTORT VIDEO ===
print("\n[INFO] Undistorting video using calibration data...")
cap = cv2.VideoCapture(VIDEO_PATH)
frame_id = 0

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    h, w = frame.shape[:2]
    new_camera_mtx, roi = cv2.getOptimalNewCameraMatrix(mtx, dist, (w, h), 1, (w, h))
    dst = cv2.undistort(frame, mtx, dist, None, new_camera_mtx)

    # Crop
    x, y, w, h = roi
    dst = dst[y:y+h, x:x+w]
    cv2.imwrite(f'{UNDISTORTED_FOLDER}/frame_{frame_id:03d}.png', dst)

    frame_id += 1

cap.release()
print(f"\n✅ Undistorted frames saved to '{UNDISTORTED_FOLDER}/'")
