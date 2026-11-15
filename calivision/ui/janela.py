import os, sys, time, sqlite3
from datetime import date, timedelta
import cv2
from PySide6.QtCore import Qt, QTimer, Signal, QRectF
from PySide6.QtGui import QImage, QPixmap, QColor, QPainter, QLinearGradient
from PySide6.QtWidgets import (QApplication, QComboBox, QGraphicsDropShadowEffect, QListWidget, QFrame, QHBoxLayout, QLabel, QLineEdit, QMainWindow,
                               QMessageBox, QProgressBar, QPushButton, QStackedWidget, QVBoxLayout, QWidget)
from .. import banco
from ..sessao import Sessao
from ..biblioteca import BIBLIOTECA
from .. import conquistas
from .estilo import QSS

ASSETS = os.path.join(os.path.dirname(__file__), "..", "..", "assets")
EXERCICIOS = [("Flexão", "flexao"), ("Paralelas", "paralelas"), ("Prancha", "prancha"), ("Agachamento", "agachamento")]
NOMES = {s: n for n, s in EXERCICIOS}

def rotulo(t, nome=""):
    l = QLabel(t); l.setObjectName(nome); return l

def logo(altura):
    l = QLabel(); l.setAlignment(Qt.AlignCenter)
    pm = QPixmap(os.path.join(ASSETS, "logo_ui.png"))
    if not pm.isNull(): l.setPixmap(pm.scaledToHeight(altura, Qt.SmoothTransformation))
    return l

def card(layout):
    f = QFrame(); f.setObjectName("card"); f.setLayout(layout)
    sombra = QGraphicsDropShadowEffect(f); sombra.setBlurRadius(40); sombra.setOffset(0, 10); sombra.setColor(QColor(0, 229, 255, 28))
    f.setGraphicsEffect(sombra); return f

def vbox(*itens, m=24, esp=12):
    v = QVBoxLayout(); v.setContentsMargins(m, m, m, m); v.setSpacing(esp)
    for i in itens: v.addWidget(i) if isinstance(i, QWidget) else v.addLayout(i)
    return v

class Barras(QWidget):
    """Gráfico de barras desenhado à mão (sem dependências extras)."""
    def __init__(self):
        super().__init__(); self.dados = []; self.setMinimumHeight(150)
    def definir(self, dados): self.dados = dados; self.update()
    def paintEvent(self, e):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height(); n = len(self.dados) or 1
        mx = max([v for _, v in self.dados] + [1]); larg, area = w / n, h - 46
        for i, (rot, v) in enumerate(self.dados):
            bh = max(area * v / mx, 4) if v else 4; x, y = i * larg + larg * 0.2, 16 + area - bh
            g = QLinearGradient(0, y, 0, y + bh); g.setColorAt(0, QColor("#00D9FF")); g.setColorAt(1, QColor("#1677FF"))
            p.setBrush(g if v else QColor("#16212E")); p.setPen(Qt.NoPen); p.drawRoundedRect(QRectF(x, y, larg * 0.6, bh), 6, 6)
            p.setPen(QColor("#AAB6C8")); p.drawText(QRectF(i * larg, h - 22, larg, 18), Qt.AlignCenter, rot)
            if v: p.setPen(QColor("#E8F1FA")); p.drawText(QRectF(i * larg, y - 18, larg, 16), Qt.AlignCenter, str(v))

class Login(QWidget):
    def __init__(self, con, ao_entrar):
        super().__init__(); self.con, self.ao_entrar, self.cadastro = con, ao_entrar, False
        self.nome = QLineEdit(placeholderText="Nome"); self.email = QLineEdit(placeholderText="E-mail")
        self.senha = QLineEdit(placeholderText="Senha (mín. 8 caracteres)"); self.senha.setEchoMode(QLineEdit.Password)
        self.erro = rotulo("", "erro"); self.erro.setWordWrap(True)
        self.botao = QPushButton("Entrar"); self.botao.setObjectName("primario"); self.botao.clicked.connect(self.enviar)
        self.alternar = QPushButton("Não tem conta? Criar conta"); self.alternar.setObjectName("link"); self.alternar.clicked.connect(self.trocar)
        for c in (self.nome, self.email, self.senha): c.returnPressed.connect(self.enviar)
        t = rotulo("CALIVISION", "titulo"); t.setAlignment(Qt.AlignCenter)
        s = rotulo("TREINE. EXECUTE. EVOLUA.", "sub"); s.setAlignment(Qt.AlignCenter)
        c = card(vbox(logo(190), t, s, self.nome, self.email, self.senha, self.erro, self.botao, self.alternar, m=36, esp=12))
        c.setFixedWidth(430); self.nome.hide(); self.erro.hide()
        meio = QHBoxLayout(); meio.addStretch(); meio.addWidget(c); meio.addStretch()
        ext = QVBoxLayout(); ext.addStretch(); ext.addLayout(meio); ext.addStretch(); self.setLayout(ext)

    def mostrar_erro(self, texto):
        self.erro.setText(texto); self.erro.setVisible(bool(texto))

    def trocar(self):
        self.cadastro = not self.cadastro; self.nome.setVisible(self.cadastro); self.mostrar_erro("")
        self.botao.setText("Criar conta" if self.cadastro else "Entrar")
        self.alternar.setText("Já tenho conta" if self.cadastro else "Não tem conta? Criar conta")

    def enviar(self):
        email, senha = self.email.text().strip(), self.senha.text()
        try:
            if self.cadastro:
                if not self.nome.text().strip() or not email: self.mostrar_erro("Preencha nome e e-mail."); return
                uid = banco.cadastrar(self.con, self.nome.text().strip(), email, senha)
            else:
                uid = banco.login(self.con, email, senha)
                if not uid: self.mostrar_erro("E-mail ou senha incorretos."); return
        except ValueError as e: self.mostrar_erro(str(e)); return
        except sqlite3.IntegrityError: self.mostrar_erro("Este e-mail já está cadastrado."); return
        self.mostrar_erro(""); self.senha.clear(); self.ao_entrar(uid)

class Home(QWidget):
    def __init__(self, con, ao_iniciar, ao_sair, ao_biblioteca):
        super().__init__(); self.con, self.ao_iniciar = con, ao_iniciar; self.uid = None
        self.ola = rotulo("", "h2")
        sair = QPushButton("Sair"); sair.clicked.connect(ao_sair)
        bib = QPushButton("Biblioteca"); bib.clicked.connect(ao_biblioteca)
        topo = QHBoxLayout(); topo.addWidget(logo(46)); topo.addWidget(rotulo("CALIVISION", "marca")); topo.addStretch()
        topo.addWidget(self.ola); topo.addSpacing(16); topo.addWidget(bib); topo.addSpacing(8); topo.addWidget(sair)
        self.stats = {}
        linha = QHBoxLayout(); linha.setSpacing(16)
        for k, t in (("treinos", "Treinos"), ("reps", "Repetições validadas"), ("prancha", "Segundos de prancha validados")):
            n = rotulo("0", "statn"); self.stats[k] = n
            linha.addWidget(card(vbox(n, rotulo(t, "statl"), m=22, esp=2)))
        self.ex = QComboBox(); [self.ex.addItem(n, s) for n, s in EXERCICIOS]; self.ex.currentIndexChanged.connect(self.atualiza_meta)
        self.series = QComboBox(); [self.series.addItem(f"{n} série{'s' if n > 1 else ''}", n) for n in (1, 2, 3, 4, 5)]; self.series.setCurrentIndex(2)
        self.meta = QComboBox(); self.atualiza_meta()
        ini = QPushButton("Iniciar treino com câmera"); ini.setObjectName("primario"); ini.clicked.connect(self.iniciar)
        self.novo = card(vbox(rotulo("Novo treino", "h2"), rotulo("EXERCÍCIO", "rotulo"), self.ex, rotulo("SÉRIES", "rotulo"), self.series,
                              rotulo("META POR SÉRIE", "rotulo"), self.meta, ini,
                              rotulo("Só conta o que a câmera validar.", "sub"), m=26, esp=8))
        self.novo.setFixedWidth(400)
        self.lista = QVBoxLayout(); self.lista.setSpacing(0)
        self.grafico = Barras()
        self.conq = QLabel(); self.conq.setTextFormat(Qt.RichText)
        cl = vbox(rotulo("Repetições validadas nos últimos 7 dias", "h2"), self.grafico, rotulo("Últimos treinos", "h2"), self.lista, rotulo("Conquistas", "h2"), self.conq, m=26, esp=10); cl.addStretch()
        corpo = QHBoxLayout(); corpo.setSpacing(16); corpo.addWidget(self.novo); corpo.addWidget(card(cl), 1)
        raiz = QVBoxLayout(); raiz.setContentsMargins(36, 28, 36, 28); raiz.setSpacing(20)
        raiz.addLayout(topo); raiz.addLayout(linha); raiz.addLayout(corpo, 1); self.setLayout(raiz)

    def atualiza_meta(self):
        iso = self.ex.currentData() == "prancha"; self.meta.clear()
        for n in ((15, 20, 30, 45, 60, 90) if iso else (5, 8, 10, 12, 15, 20)):
            self.meta.addItem(f"{n} {'segundos' if iso else 'repetições'}", n)
        self.meta.setCurrentIndex(2)

    def iniciar(self):
        self.ao_iniciar(self.uid, self.ex.currentData(), self.series.currentData(), self.meta.currentData())

    def atualizar(self, uid):
        self.uid = uid; c = self.con
        self.ola.setText("Olá, " + c.execute("SELECT nome FROM usuarios WHERE id=?", (uid,)).fetchone()[0].split()[0])
        q = lambda sql: c.execute(sql, (uid,)).fetchone()[0] or 0
        base = "FROM series s JOIN exercicios_treino et ON et.id=s.exercicio_treino_id JOIN treinamentos t ON t.id=et.treinamento_id JOIN exercicios e ON e.id=et.exercicio_id WHERE t.usuario_id=?"
        self.stats["treinos"].setText(str(q("SELECT COUNT(*) FROM treinamentos WHERE usuario_id=?")))
        self.stats["reps"].setText(str(q("SELECT SUM(s.reps_validadas) " + base + " AND e.nome!='prancha'")))
        self.stats["prancha"].setText(str(q("SELECT SUM(s.reps_validadas) " + base + " AND e.nome='prancha'")))
        d = dict(c.execute("SELECT date(t.inicio,'localtime'), SUM(s.reps_validadas) " + base + " AND e.nome!='prancha' GROUP BY 1", (uid,)).fetchall())
        hoje = date.today(); dias = [hoje - timedelta(days=i) for i in range(6, -1, -1)]
        self.grafico.definir([(x.strftime('%d/%m'), d.get(str(x), 0)) for x in dias])
        conquistas.verificar(c, uid); ganhas = conquistas.listar(c, uid)
        self.conq.setText("<br>".join(f"<span style='color:#00D9FF'>✓ {n}</span>" if n in ganhas else f"<span style='color:#5C6B80'>○ {n}</span>"
                                       for n, _, _ in conquistas.DEFINICOES))
        while self.lista.count(): self.lista.takeAt(0).widget().deleteLater()
        linhas = c.execute("""SELECT strftime('%d/%m %H:%M', t.inicio, 'localtime'), e.nome, COALESCE(SUM(s.reps_validadas),0), t.situacao FROM treinamentos t
            JOIN exercicios_treino et ON et.treinamento_id=t.id JOIN exercicios e ON e.id=et.exercicio_id
            LEFT JOIN series s ON s.exercicio_treino_id=et.id WHERE t.usuario_id=? GROUP BY et.id ORDER BY t.id DESC LIMIT 6""", (uid,)).fetchall()
        if not linhas: self.lista.addWidget(rotulo("Nenhum treino validado ainda. Comece o primeiro!", "sub"))
        for ini, nome, v, sit in linhas:
            un = "s" if nome == "prancha" else " reps"
            self.lista.addWidget(rotulo(f"{ini}   •   {NOMES.get(nome, nome)}   •   {v}{un}   •   {sit}", "item"))

class Biblioteca(QWidget):
    def __init__(self, ao_voltar):
        super().__init__()
        voltar = QPushButton("← Voltar"); voltar.clicked.connect(ao_voltar)
        topo = QHBoxLayout(); topo.addWidget(voltar); topo.addSpacing(12); topo.addWidget(rotulo("Biblioteca de exercícios", "h2")); topo.addStretch()
        self.lista = QListWidget(); self.lista.setFixedWidth(360); self.lista.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        for ex in BIBLIOTECA: self.lista.addItem(f"{ex['nome']}    {'● câmera' if ex['validado'] else '○ em breve'}")
        self.lista.currentRowChanged.connect(self.mostrar)
        self.det = QLabel(); self.det.setTextFormat(Qt.RichText); self.det.setWordWrap(True); self.det.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        corpo = QHBoxLayout(); corpo.setSpacing(16); corpo.addWidget(self.lista); corpo.addWidget(card(vbox(self.det, m=30)), 1)
        raiz = QVBoxLayout(); raiz.setContentsMargins(36, 28, 36, 28); raiz.setSpacing(20); raiz.addLayout(topo); raiz.addLayout(corpo, 1)
        self.setLayout(raiz); self.lista.setCurrentRow(0)

    def mostrar(self, i):
        if i < 0: return
        ex = BIBLIOTECA[i]; li = lambda xs: "".join(f"<li>{x}</li>" for x in xs)
        sel = ("Validação por câmera: <b style='color:#00D9FF'>disponível</b>" if ex["validado"]
               else "Validação por câmera: <b style='color:#FFB020'>em breve</b> (o app ainda não valida este exercício)")
        self.det.setText(f"<h1 style='color:#00D9FF'>{ex['nome']}</h1><p style='color:#AAB6C8'>{ex['categoria']} · {ex['musculos']}</p><p>{sel}</p>"
                         f"<h3>Posição inicial</h3><p>{ex['inicio']}</p><h3>Execução</h3><ol>{li(ex['passos'])}</ol>"
                         f"<h3>Critério de validação</h3><p>{ex['criterio']}</p><h3>Segurança</h3><p>{ex['seguranca']}</p>")

class Treino(QWidget):
    terminou = Signal(str)
    def __init__(self, con):
        super().__init__(); self.con, self.cap, self.timer = con, None, QTimer(self); self.timer.timeout.connect(self.tick)
        self.cam = rotulo("", "cam"); self.cam.setMinimumSize(640, 480); self.cam.setAlignment(Qt.AlignCenter)
        self.nome, self.serie_l = rotulo("", "h2"), rotulo("", "sub")
        self.cont, self.meta_l = rotulo("0", "contador"), rotulo("", "meta"); self.cont.setAlignment(Qt.AlignCenter); self.meta_l.setAlignment(Qt.AlignCenter)
        self.msg = rotulo("", "msg"); self.msg.setAlignment(Qt.AlignCenter); self.msg.setWordWrap(True)
        self.barra = QProgressBar(); self.barra.setTextVisible(False)
        self.pausa = QPushButton("Pausar"); self.pausa.clicked.connect(self.alternar_pausa)
        enc = QPushButton("Encerrar treino"); enc.setObjectName("perigo"); enc.clicked.connect(lambda: self.parar("interrompido"))
        corpo = vbox(self.nome, self.serie_l, self.cont, self.meta_l, self.barra, self.msg, self.pausa, enc, m=26, esp=12)
        corpo.insertStretch(5); corpo.insertStretch(2)
        lado = card(corpo); lado.setFixedWidth(360)
        h = QHBoxLayout(); h.setContentsMargins(36, 28, 36, 28); h.setSpacing(20); h.addWidget(self.cam, 1); h.addWidget(lado); self.setLayout(h)

    def iniciar(self, uid, ex, series, meta):
        cap = cv2.VideoCapture(0)
        if not cap.isOpened(): QMessageBox.warning(self, "Câmera", "Não foi possível abrir a câmera."); return False
        from ..pose import Pose
        self.cap, self.pose, self.ex, self.series, self.meta = cap, Pose(), ex, series, meta
        self.t, self.et = banco.iniciar_treino(self.con, uid, ex, series, meta)
        self.n, self.t0, self.pausado, self.total = 1, time.time(), False, 0
        self.pausa.setText("Pausar"); self.nova_serie(); self.timer.start(25); return True

    def nova_serie(self):
        self.s, self.ts = Sessao(self.ex, self.meta), time.time()
        self.nome.setText(NOMES[self.ex]); self.serie_l.setText(f"SÉRIE {self.n} DE {self.series}")
        self.meta_l.setText(f"de {self.meta} {'segundos' if self.ex == 'prancha' else 'repetições'}"); self.barra.setMaximum(self.meta)

    def alternar_pausa(self):
        self.pausado = not self.pausado; self.pausa.setText("Retomar" if self.pausado else "Pausar")

    def mostrar(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB); h, w, _ = rgb.shape
        pm = QPixmap.fromImage(QImage(rgb.data, w, h, 3 * w, QImage.Format_RGB888))
        self.cam.setPixmap(pm.scaled(self.cam.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def tick(self):
        ok, frame = self.cap.read()
        if not ok: self.msg.setText("Falha na câmera — verifique a conexão"); return
        frame = cv2.flip(frame, 1); lm = self.pose.processar(frame)
        if not self.pausado: self.s.processar(lm, time.time())
        if lm is not None: self.pose.desenhar(frame, lm)
        self.mostrar(frame)
        self.cont.setText(str(self.s.valor)); self.barra.setValue(min(self.s.valor, self.meta))
        self.msg.setText("Treino pausado" if self.pausado else self.s.msg)
        if self.s.concluida:
            self.registrar(); self.n += 1
            if self.n > self.series: self.parar("concluido")
            else: self.nova_serie()

    def registrar(self):
        self.total += self.s.valor
        banco.registrar_serie(self.con, self.et, self.n, self.s.valor, time.time() - self.ts, self.s.log)

    def parar(self, situacao):
        if not self.timer.isActive(): return
        self.timer.stop()
        if situacao == "interrompido" and self.s.valor > 0: self.registrar()
        banco.finalizar_treino(self.con, self.t, time.time() - self.t0, situacao)
        self.cap.release(); self.pose.fechar()
        un = "segundos validados" if self.ex == "prancha" else "repetições validadas"
        self.terminou.emit(f"{'Treino concluído!' if situacao == 'concluido' else 'Treino encerrado.'}\n\n{self.total} {un}.")

class Janela(QMainWindow):
    def __init__(self, con=None):
        super().__init__(); self.setWindowTitle("CALIVISION"); self.con = con or banco.conectar()
        self.pilha = QStackedWidget(); self.pilha.setObjectName("raiz"); self.setCentralWidget(self.pilha)
        self.login = Login(self.con, self.entrar)
        self.biblioteca = Biblioteca(lambda: self.pilha.setCurrentWidget(self.home))
        self.home = Home(self.con, self.comecar, lambda: self.pilha.setCurrentWidget(self.login), lambda: self.pilha.setCurrentWidget(self.biblioteca))
        self.treino = Treino(self.con); self.treino.terminou.connect(self.fim)
        for p in (self.login, self.home, self.treino, self.biblioteca): self.pilha.addWidget(p)

    def entrar(self, uid): self.uid = uid; self.home.atualizar(uid); self.pilha.setCurrentWidget(self.home)

    def comecar(self, uid, ex, series, meta):
        r = QMessageBox.question(self, "Uso da câmera", "A câmera será usada somente neste computador. O vídeo não é gravado nem enviado.\n\nPermitir?")
        if r == QMessageBox.Yes and self.treino.iniciar(uid, ex, series, meta): self.pilha.setCurrentWidget(self.treino)

    def fim(self, resumo):
        novas = conquistas.verificar(self.con, self.uid)
        if novas: resumo += "\n\nNova conquista: " + ", ".join(novas)
        QMessageBox.information(self, "CALIVISION", resumo); self.home.atualizar(self.uid); self.pilha.setCurrentWidget(self.home)

    def closeEvent(self, e): self.treino.parar("interrompido"); super().closeEvent(e)

def executar():
    app = QApplication(sys.argv); app.setStyleSheet(QSS)
    j = Janela(); j.resize(1180, 760); j.show(); sys.exit(app.exec())
