from calivision import banco
def test_fluxo():
    con = banco.conectar(":memory:"); u = banco.cadastrar(con, "Zé", "a@b.com", "senha1234")
    assert banco.login(con, "a@b.com", "senha1234") == u and banco.login(con, "a@b.com", "errada") is None
    t, et = banco.iniciar_treino(con, u, "agachamento", 1, 5)
    banco.registrar_serie(con, et, 1, 5, 30.0, [("valida", .9, None)]); banco.finalizar_treino(con, t, 40)
    assert con.execute("SELECT SUM(reps_validadas) FROM series").fetchone()[0] == 5
