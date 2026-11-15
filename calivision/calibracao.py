"""Ferramenta de calibração: grava só ângulos (sem vídeo) e resume por exercício e rótulo."""
import csv, glob, os, time
PASTA = os.path.expanduser("~/.calivision/calibracao")

def gravar(exercicio, rotulo, segundos=40):
    import cv2
    from .pose import Pose, angulo_joelho, angulo_cotovelo_e_alinhamento, alinhamento_corpo
    cap = cv2.VideoCapture(0)
    if not cap.isOpened(): raise SystemExit("Não foi possível abrir a câmera.")
    pose, t0 = Pose(), time.time()
    os.makedirs(PASTA, exist_ok=True)
    arq = os.path.join(PASTA, f"{exercicio}_{rotulo}_{int(t0)}.csv")
    with open(arq, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["t", "angulo", "visibilidade", "postura_ok"])
        while time.time() - t0 < segundos:
            ok, frame = cap.read()
            if not ok: continue
            frame = cv2.flip(frame, 1); lm = pose.processar(frame)
            if lm is not None:
                if exercicio == "agachamento": ang, vis = angulo_joelho(lm); pok = True
                elif exercicio == "prancha": ang, vis = alinhamento_corpo(lm); pok = ang >= 165
                else: ang, vis, pok = angulo_cotovelo_e_alinhamento(lm)
                w.writerow([round(time.time() - t0, 3), round(ang, 1), round(vis, 2), int(pok)]); pose.desenhar(frame, lm)
            cv2.putText(frame, f"gravando {exercicio} ({rotulo}) {segundos-(time.time()-t0):.0f}s  [q] sair", (10, 30), 0, 0.7, (255, 229, 0), 2)
            cv2.imshow("CALIVISION - calibracao", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"): break
    cap.release(); pose.fechar(); cv2.destroyAllWindows()
    return arq

def resumir(pasta=PASTA):
    """Retorna [(exercicio, rotulo, n_quadros, p5, mediana, p95)] só com quadros de visibilidade >= 0.6."""
    grupos = {}
    for arq in glob.glob(os.path.join(pasta, "*.csv")):
        ex, rot = os.path.basename(arq).split("_")[:2]
        with open(arq, newline="") as f:
            angs = [float(r["angulo"]) for r in csv.DictReader(f) if float(r["visibilidade"]) >= 0.6]
        grupos.setdefault((ex, rot), []).extend(angs)
    saida = []
    for (ex, rot), a in sorted(grupos.items()):
        a.sort()
        if len(a) >= 10: saida.append((ex, rot, len(a), a[int(.05*(len(a)-1))], a[len(a)//2], a[int(.95*(len(a)-1))]))
    return saida
