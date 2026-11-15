from calivision import banco
def test_fluxo():
    con = banco.conectar(":memory:"); u = banco.cadastrar(con, "Zé", "a@b.com", "senha1234")
    assert banco.login(con, "a@b.com", "senha1234") == u and banco.login(con, "a@b.com", "errada") is None
    t, et = banco.iniciar_treino(con, u, "agachamento", 1, 5)
    banco.registrar_serie(con, et, 1, 5, 30.0, [("valida", .9, None)]); banco.finalizar_treino(con, t, 40)
    assert con.execute("SELECT SUM(reps_validadas) FROM series").fetchone()[0] == 5

def test_conquistas_reais_e_idempotentes():
    from calivision import conquistas
    con = banco.conectar(":memory:"); u = banco.cadastrar(con, "Zé", "c@d.com", "senha1234")
    assert conquistas.verificar(con, u) == []                     # sem treino, sem conquista
    t, et = banco.iniciar_treino(con, u, "flexao", 1, 10)
    banco.registrar_serie(con, et, 1, 4, 20.0, []); banco.finalizar_treino(con, t, 30, "interrompido")
    assert conquistas.verificar(con, u) == ["Primeira repetição validada"]   # série incompleta não conta como série de flexões
    t, et = banco.iniciar_treino(con, u, "flexao", 1, 10)
    banco.registrar_serie(con, et, 1, 10, 20.0, []); banco.finalizar_treino(con, t, 30)
    novas = conquistas.verificar(con, u)
    assert "Primeira série de flexões" in novas and "Primeiro treinamento concluído" in novas
    assert conquistas.verificar(con, u) == []                     # não repete
