from calivision.validador import *
def rodar(angs, cfg=AGACHAMENTO, vis=0.9, ok=True):
    val = Validador(cfg); rs = [val.atualizar(a, vis, ok) for a in angs]; return val, rs
def ciclo(fundo=90): return [170]*5 + list(range(170, fundo, -10)) + [fundo]*5 + list(range(fundo, 171, 10)) + [170]*5
def test_rep_completa(): assert rodar(ciclo())[0].reps == 1
def test_incompleta_rejeitada():
    v, _ = rodar(ciclo(fundo=130)); assert v.reps == 0 and v.rejeitadas == 1
def test_duas_reps_sem_duplicar(): assert rodar(ciclo()+ciclo())[0].reps == 2
def test_oscilacao_nao_conta(): assert rodar([170]*5+[150,170]*20)[0].reps == 0
def test_visibilidade_baixa(): assert rodar(ciclo(), vis=0.3)[0].reps == 0
def test_flexao_postura_ruim():
    v, _ = rodar(ciclo(), FLEXAO, ok=False); assert v.reps == 0 and v.rejeitadas == 1

def test_prancha_acumula_so_com_postura():
    iso = Isometrico(meta_s=5)
    for i in range(0, 40): iso.atualizar(i*0.1, True, 0.9)      # 4s válidos (1s estabiliza)
    assert 2.5 < iso.segundos < 3.2 and not iso.concluido
def test_prancha_quebra_zera_bloco():
    iso = Isometrico(meta_s=60)
    for i in range(0, 30): iso.atualizar(i*0.1, True, 0.9)
    for i in range(30, 50): iso.atualizar(i*0.1, False, 0.9)    # 2s fora: quebra
    assert iso.melhor_bloco > 1.5 and iso._bloco == 0
def test_prancha_conclui():
    iso = Isometrico(meta_s=3)
    for i in range(0, 60): iso.atualizar(i*0.1, True, 0.9)
    assert iso.concluido

def test_abertura_monta_tela():
    from calivision.abertura import montar_abertura
    t = montar_abertura(); assert t.shape == (700, 900, 3) and t.max() > 0

def test_biblioteca_consistente_com_validadores():
    from calivision.biblioteca import BIBLIOTECA
    from calivision.sessao import CFG
    ativos = {e["nome"] for e in BIBLIOTECA if e["validado"]}
    assert len(ativos) == len(CFG) + 1          # validadores de repetição + prancha
    assert all(e["criterio"] and e["seguranca"] for e in BIBLIOTECA)

def test_calibracao_resumo(tmp_path):
    from calivision import calibracao
    linhas = "t,angulo,visibilidade,postura_ok\n" + "".join(f"{i},{70+i%100},0.9,1\n" for i in range(200))
    (tmp_path / "flexao_boa_1.csv").write_text(linhas)
    r = calibracao.resumir(str(tmp_path))
    assert r[0][0] == "flexao" and r[0][1] == "boa" and r[0][3] < r[0][5]
