import math

def angulo(a, b, c):
    """Ângulo em graus no ponto b, formado por a-b-c. Pontos são (x, y)."""
    ang = abs(math.degrees(math.atan2(c[1]-b[1], c[0]-b[0]) - math.atan2(a[1]-b[1], a[0]-b[0])))
    return 360 - ang if ang > 180 else ang
