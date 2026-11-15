"""Wrapper do MediaPipe Pose (API 'solutions', sem download de modelo)."""
import cv2, mediapipe as mp
from .geometria import angulo
P = mp.solutions.pose.PoseLandmark

class Pose:
    def __init__(self):
        self._p = mp.solutions.pose.Pose(model_complexity=1, min_detection_confidence=0.6, min_tracking_confidence=0.6)
    def processar(self, frame_bgr):
        return self._p.process(cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)).pose_landmarks
    def desenhar(self, frame, lm):
        d = mp.solutions.drawing_utils
        d.draw_landmarks(frame, lm, mp.solutions.pose.POSE_CONNECTIONS,
                         d.DrawingSpec(color=(255, 217, 0), thickness=3, circle_radius=4),   # ciano
                         d.DrawingSpec(color=(255, 119, 22), thickness=3))                  # azul
    def fechar(self): self._p.close()

def _lado(lm, a, b, c):
    pts = [lm.landmark[i] for i in (a, b, c)]
    return angulo(*[(p.x, p.y) for p in pts]), min(p.visibility for p in pts)

def angulo_joelho(lm):
    e = _lado(lm, P.LEFT_HIP, P.LEFT_KNEE, P.LEFT_ANKLE)
    d = _lado(lm, P.RIGHT_HIP, P.RIGHT_KNEE, P.RIGHT_ANKLE)
    return max((e, d), key=lambda x: x[1])

def angulo_cotovelo_e_alinhamento(lm):
    e = _lado(lm, P.LEFT_SHOULDER, P.LEFT_ELBOW, P.LEFT_WRIST)
    d = _lado(lm, P.RIGHT_SHOULDER, P.RIGHT_ELBOW, P.RIGHT_WRIST)
    ang, vis = max((e, d), key=lambda x: x[1])
    lado = (P.LEFT_SHOULDER, P.LEFT_HIP, P.LEFT_ANKLE) if e[1] >= d[1] else (P.RIGHT_SHOULDER, P.RIGHT_HIP, P.RIGHT_ANKLE)
    corpo, _ = _lado(lm, *lado)
    return ang, vis, corpo >= 160

def alinhamento_corpo(lm):
    """Ângulo ombro-quadril-tornozelo do lado mais visível (prancha). Retorna (ângulo, visibilidade)."""
    e = _lado(lm, P.LEFT_SHOULDER, P.LEFT_HIP, P.LEFT_ANKLE)
    d = _lado(lm, P.RIGHT_SHOULDER, P.RIGHT_HIP, P.RIGHT_ANKLE)
    return max((e, d), key=lambda x: x[1])
