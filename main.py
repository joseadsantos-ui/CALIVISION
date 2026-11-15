import argparse, getpass, time, cv2
from calivision import banco, validador as v

def treinar(con, uid, exercicio, series, reps):
    from calivision.pose import Pose, angulo_joelho, angulo_cotovelo_e_alinhamento
    cap = cv2.VideoCapture(0)
    if not cap.isOpened(): raise SystemExit("Não foi possível abrir a câmera.")
    pose = Pose()
    cfg = {"agachamento": v.AGACHAMENTO, "flexao": v.FLEXAO, "paralelas": v.PARALELAS}[exercicio]
    t, et = banco.iniciar_treino(con, uid, exercicio, series, reps)
    t0, msg = time.time(), "Posicione-se diante da câmera"
    for n in range(1, series+1):
        val, log, ts, pausado = v.Validador(cfg), [], time.time(), False
        while val.reps < reps:
            ok, frame = cap.read()
            if not ok: msg = "Falha na câmera"; continue
            lm = pose.processar(frame)
            if lm is None: val.atualizar(None, 0); msg = "Corpo não detectado"
            elif not pausado:
                if exercicio == "agachamento": ang, vis = angulo_joelho(lm); ok_p = True
                else:
                    ang, vis, ok_p = angulo_cotovelo_e_alinhamento(lm)
                    ok_p = ok_p or exercicio == "paralelas"
                r = val.atualizar(ang, vis, ok_p)
                if r == v.Resultado.VALIDA: log.append(("valida", vis, None)); msg = "Repetição validada"
                elif r == v.Resultado.REJEITADA: log.append(("rejeitada", vis, val.motivo)); msg = val.motivo
                elif val.estado == v.Estado.DETECCAO_INSUFICIENTE: msg = "Ajuste seu posicionamento"
                pose.desenhar(frame, lm)
            cv2.putText(frame, f"{exercicio} S{n}/{series}  {val.reps}/{reps}", (10, 30), 0, 0.9, (255, 200, 0), 2)
            cv2.putText(frame, msg, (10, 65), 0, 0.7, (255, 255, 0), 2)
            cv2.putText(frame, "[p] pausa  [q] encerrar", (10, frame.shape[0]-10), 0, 0.5, (255, 255, 255), 1)
            cv2.imshow("CALIVISION", frame)
            k = cv2.waitKey(1) & 0xFF
            if k == ord("p"): pausado = not pausado
            if k == ord("q"):
                banco.registrar_serie(con, et, n, val.reps, time.time()-ts, log)
                banco.finalizar_treino(con, t, time.time()-t0, "interrompido")
                cap.release(); pose.fechar(); cv2.destroyAllWindows(); return
        banco.registrar_serie(con, et, n, val.reps, time.time()-ts, log)
    banco.finalizar_treino(con, t, time.time()-t0)
    cap.release(); pose.fechar(); cv2.destroyAllWindows()

def prancha(con, uid, series, segundos):
    from calivision.pose import Pose, alinhamento_corpo
    cap = cv2.VideoCapture(0)
    if not cap.isOpened(): raise SystemExit("Não foi possível abrir a câmera.")
    pose = Pose(); t, et = banco.iniciar_treino(con, uid, "prancha", series, segundos); t0 = time.time()
    for n in range(1, series+1):
        iso, log, ts = v.Isometrico(segundos), [], time.time()
        while not iso.concluido:
            ok, frame = cap.read()
            if not ok: continue
            lm = pose.processar(frame)
            if lm is None: iso.atualizar(time.time(), False, 0)
            else:
                ang, vis = alinhamento_corpo(lm); iso.atualizar(time.time(), ang >= 165, vis); pose.desenhar(frame, lm)
            cv2.putText(frame, f"prancha S{n}/{series}  {iso.segundos:.0f}/{segundos}s", (10, 30), 0, 0.9, (255, 200, 0), 2)
            cv2.putText(frame, iso.motivo, (10, 65), 0, 0.7, (255, 255, 0), 2)
            cv2.imshow("CALIVISION", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                banco.registrar_serie(con, et, n, int(iso.segundos), time.time()-ts, [("parcial", 1.0, None)])
                banco.finalizar_treino(con, t, time.time()-t0, "interrompido"); cap.release(); pose.fechar(); cv2.destroyAllWindows(); return
        banco.registrar_serie(con, et, n, int(iso.segundos), time.time()-ts, [("valida", 1.0, None)])
    banco.finalizar_treino(con, t, time.time()-t0); cap.release(); pose.fechar(); cv2.destroyAllWindows()

def main():
    ap = argparse.ArgumentParser(); sp = ap.add_subparsers(dest="cmd")
    c = sp.add_parser("cadastrar"); c.add_argument("nome"); c.add_argument("email")
    t = sp.add_parser("treinar"); t.add_argument("email")
    t.add_argument("--exercicio", choices=["flexao", "paralelas", "prancha", "agachamento"], default="flexao")
    t.add_argument("--series", type=int, default=3); t.add_argument("--reps", type=int, default=10)
    g = sp.add_parser("gravar"); g.add_argument("--exercicio", choices=["flexao", "paralelas", "prancha", "agachamento"], required=True)
    g.add_argument("--rotulo", required=True, help="ex.: boa, incompleta, quadril-caido (sem underscore)"); g.add_argument("--segundos", type=int, default=40)
    sp.add_parser("analisar")
    a = ap.parse_args()
    if a.cmd == "gravar":
        from calivision import calibracao; return print("Salvo em", calibracao.gravar(a.exercicio, a.rotulo, a.segundos))
    if a.cmd == "analisar":
        from calivision import calibracao; r = calibracao.resumir()
        if not r: return print("Nenhuma gravação encontrada. Use: python main.py gravar --exercicio flexao --rotulo boa")
        print(f"{'exercicio':<12}{'rotulo':<16}{'quadros':>8}{'p5':>8}{'mediana':>9}{'p95':>8}")
        for ex, rot, n, p5, med, p95 in r: print(f"{ex:<12}{rot:<16}{n:>8}{p5:>8.0f}{med:>9.0f}{p95:>8.0f}")
        return print("\nSugestão para rótulo 'boa': fundo ≈ p5 + 10 e topo ≈ p95 - 10 (compare com 'incompleta').")
    if not a.cmd:
        from calivision.ui.janela import executar; return executar()
    con = banco.conectar()
    if a.cmd == "cadastrar":
        banco.cadastrar(con, a.nome, a.email, getpass.getpass("Senha (min. 8): ")); print("Cadastrado.")
    else:
        uid = banco.login(con, a.email, getpass.getpass("Senha: "))
        if not uid: raise SystemExit("Login inválido.")
        from calivision.abertura import mostrar_abertura
        mostrar_abertura()
        input("A câmera será usada só localmente, sem gravar vídeo. Enter para consentir... ")
        if a.exercicio == "prancha": prancha(con, uid, a.series, a.reps)   # --reps = segundos
        else: treinar(con, uid, a.exercicio, a.series, a.reps)

if __name__ == "__main__": main()
