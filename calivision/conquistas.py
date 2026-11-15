"""Conquistas calculadas só a partir dos registros reais do banco."""
_BASE = ("SELECT COUNT(*) FROM series s JOIN exercicios_treino et ON et.id=s.exercicio_treino_id "
         "JOIN treinamentos t ON t.id=et.treinamento_id JOIN exercicios e ON e.id=et.exercicio_id WHERE t.usuario_id=?")
DEFINICOES = [  # (nome, consulta com ? = usuario_id, mínimo)
    ("Primeira repetição validada", _BASE + " AND e.nome!='prancha' AND s.reps_validadas>=1", 1),
    ("Primeiro treinamento concluído", "SELECT COUNT(*) FROM treinamentos WHERE usuario_id=? AND situacao='concluido'", 1),
    ("Primeira série de flexões", _BASE + " AND e.nome='flexao' AND s.reps_validadas>=et.reps_plan", 1),
    ("Primeira prancha validada", _BASE + " AND e.nome='prancha' AND s.reps_validadas>=et.reps_plan", 1),
    ("3 dias diferentes de treino", "SELECT COUNT(DISTINCT date(inicio,'localtime')) FROM treinamentos WHERE usuario_id=? AND situacao='concluido'", 3),
]

def listar(con, uid):
    return {r[0] for r in con.execute("SELECT nome FROM conquistas WHERE usuario_id=?", (uid,))}

def verificar(con, uid):
    """Registra as conquistas recém-atingidas e devolve seus nomes."""
    ja, novas = listar(con, uid), []
    for nome, sql, minimo in DEFINICOES:
        if nome not in ja and (con.execute(sql, (uid,)).fetchone()[0] or 0) >= minimo:
            con.execute("INSERT INTO conquistas(usuario_id,nome) VALUES(?,?)", (uid, nome)); novas.append(nome)
    con.commit(); return novas
