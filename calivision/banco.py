import sqlite3, os, hashlib, secrets, hmac
CAMINHO = os.path.expanduser("~/.calivision/calivision.db")
SCHEMA = """
CREATE TABLE IF NOT EXISTS usuarios(id INTEGER PRIMARY KEY, nome TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL, senha_hash TEXT NOT NULL, criado_em TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS exercicios(id INTEGER PRIMARY KEY, nome TEXT UNIQUE NOT NULL,
  categoria TEXT, descricao TEXT, criterios TEXT);
CREATE TABLE IF NOT EXISTS treinamentos(id INTEGER PRIMARY KEY,
  usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
  inicio TEXT DEFAULT CURRENT_TIMESTAMP, fim TEXT, duracao_s REAL, situacao TEXT DEFAULT 'em_andamento');
CREATE TABLE IF NOT EXISTS exercicios_treino(id INTEGER PRIMARY KEY,
  treinamento_id INTEGER NOT NULL REFERENCES treinamentos(id) ON DELETE CASCADE,
  exercicio_id INTEGER NOT NULL REFERENCES exercicios(id), series_plan INTEGER, reps_plan INTEGER);
CREATE TABLE IF NOT EXISTS series(id INTEGER PRIMARY KEY,
  exercicio_treino_id INTEGER NOT NULL REFERENCES exercicios_treino(id) ON DELETE CASCADE,
  numero INTEGER, reps_validadas INTEGER DEFAULT 0, duracao_s REAL);
CREATE TABLE IF NOT EXISTS validacoes(id INTEGER PRIMARY KEY,
  serie_id INTEGER NOT NULL REFERENCES series(id) ON DELETE CASCADE,
  horario TEXT DEFAULT CURRENT_TIMESTAMP, resultado TEXT, confianca REAL, motivo_rejeicao TEXT);
CREATE TABLE IF NOT EXISTS configuracoes(usuario_id INTEGER REFERENCES usuarios(id) ON DELETE CASCADE,
  chave TEXT, valor TEXT, PRIMARY KEY(usuario_id, chave));
"""
EXERCICIOS = [("prancha","core","Prancha isométrica","Ombro-quadril-tornozelo >=165°, tempo mantido com postura válida"),
              ("paralelas","peito","Mergulho nas paralelas","Cotovelo <=90° embaixo, >=155° em cima"),
              ("agachamento","pernas","Agachamento livre","Joelho <=100° no fundo, >=160° no topo"),
              ("flexao","peito","Flexão tradicional","Cotovelo <=90° embaixo, >=155° em cima, corpo alinhado")]

def conectar(caminho=CAMINHO):
    if caminho != ":memory:": os.makedirs(os.path.dirname(caminho), exist_ok=True)
    con = sqlite3.connect(caminho); con.execute("PRAGMA foreign_keys=ON")
    con.executescript(SCHEMA)
    con.executemany("INSERT OR IGNORE INTO exercicios(nome,categoria,descricao,criterios) VALUES(?,?,?,?)", EXERCICIOS)
    con.commit(); return con

def _hash(senha, sal=None):
    sal = sal or secrets.token_bytes(16)
    return sal.hex()+"$"+hashlib.pbkdf2_hmac("sha256", senha.encode(), sal, 200_000).hex()

def cadastrar(con, nome, email, senha):
    if len(senha) < 8: raise ValueError("Senha deve ter ao menos 8 caracteres")
    cur = con.execute("INSERT INTO usuarios(nome,email,senha_hash) VALUES(?,?,?)", (nome, email.lower(), _hash(senha)))
    con.commit(); return cur.lastrowid

def login(con, email, senha):
    r = con.execute("SELECT id,senha_hash FROM usuarios WHERE email=?", (email.lower(),)).fetchone()
    if not r: return None
    sal, h = r[1].split("$")
    return r[0] if hmac.compare_digest(_hash(senha, bytes.fromhex(sal)).split("$")[1], h) else None

def iniciar_treino(con, uid, exercicio, series, reps):
    t = con.execute("INSERT INTO treinamentos(usuario_id) VALUES(?)", (uid,)).lastrowid
    ex = con.execute("SELECT id FROM exercicios WHERE nome=?", (exercicio,)).fetchone()[0]
    et = con.execute("INSERT INTO exercicios_treino(treinamento_id,exercicio_id,series_plan,reps_plan) VALUES(?,?,?,?)",
                     (t, ex, series, reps)).lastrowid
    con.commit(); return t, et

def registrar_serie(con, et, numero, reps, duracao, validacoes):
    s = con.execute("INSERT INTO series(exercicio_treino_id,numero,reps_validadas,duracao_s) VALUES(?,?,?,?)",
                    (et, numero, reps, duracao)).lastrowid
    con.executemany("INSERT INTO validacoes(serie_id,resultado,confianca,motivo_rejeicao) VALUES(?,?,?,?)",
                    [(s, *v) for v in validacoes])
    con.commit(); return s

def finalizar_treino(con, t, duracao, situacao="concluido"):
    con.execute("UPDATE treinamentos SET fim=CURRENT_TIMESTAMP,duracao_s=?,situacao=? WHERE id=?", (duracao, situacao, t))
    con.commit()
