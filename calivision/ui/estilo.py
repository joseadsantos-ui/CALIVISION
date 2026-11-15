"""Tema escuro com ciano e azul elétrico."""
G = "qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 %s, stop:1 %s)"
QSS = """
* { font-family: 'Segoe UI','Inter','Helvetica Neue',Arial; color:#E8F1FA; }
QWidget { background: transparent; }
QWidget#raiz { background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #0D1320, stop:1 #090D14); }
QFrame#card { background:#151C28; border:1px solid #222D3E; border-radius:20px; }
QLabel#titulo { font-size:30px; font-weight:800; color:#00D9FF; letter-spacing:6px; }
QLabel#marca { font-size:18px; font-weight:800; color:#00D9FF; letter-spacing:4px; }
QLabel#sub { color:#AAB6C8; font-size:13px; }
QLabel#h2 { font-size:16px; font-weight:700; }
QLabel#rotulo { color:#AAB6C8; font-size:12px; font-weight:600; }
QLabel#statn { font-size:38px; font-weight:800; color:#00D9FF; }
QLabel#statl { color:#AAB6C8; font-size:12px; }
QLabel#contador { font-size:120px; font-weight:800; color:#00D9FF; }
QLabel#meta { color:#AAB6C8; font-size:18px; font-weight:600; }
QLabel#msg { font-size:15px; font-weight:600; color:#7CF3FF; background:#0A2230; border-radius:14px; padding:14px; }
QLabel#erro { color:#FF6B81; font-size:12px; }
QLabel#item { font-size:13px; padding:10px 4px; border-bottom:1px solid #16212E; }
QLabel#cam { background:#000; border:1px solid #222D3E; border-radius:20px; }
QLineEdit, QComboBox { background:#0A1118; border:1px solid #223246; border-radius:12px; padding:11px 14px; font-size:14px; selection-background-color:#1677FF; }
QLineEdit:focus, QComboBox:focus { border:1px solid #00D9FF; }
QComboBox::drop-down { border:none; width:28px; }
QComboBox QAbstractItemView { background:#151C28; border:1px solid #223246; selection-background-color:#16324A; outline:0; }
QPushButton { background:#121C28; border:1px solid #223246; border-radius:12px; padding:12px 20px; font-weight:600; font-size:14px; }
QPushButton:hover { border:1px solid #00D9FF; }
QPushButton#primario { background:%s; border:none; color:#021018; font-weight:800; font-size:15px; padding:14px 20px; }
QPushButton#primario:hover { background:%s; }
QPushButton#link { background:transparent; border:none; color:#00D9FF; padding:6px; }
QPushButton#perigo { color:#FF6B81; border:1px solid #3A2230; }
QProgressBar { background:#0A1118; border:none; border-radius:6px; max-height:12px; min-height:12px; text-align:center; color:transparent; }
QProgressBar::chunk { border-radius:6px; background:%s; }
QListWidget { background:#151C28; border:1px solid #222D3E; border-radius:20px; padding:10px; outline:0; font-size:14px; }
QListWidget::item { padding:12px 10px; border-radius:10px; color:#E8F1FA; }
QListWidget::item:selected { background:#16324A; color:#00D9FF; }
QListWidget::item:hover { background:#101C28; }
""" % (G % ("#00D9FF", "#1677FF"), G % ("#5CF0FF", "#5B9BFF"), G % ("#00D9FF", "#1677FF"))
