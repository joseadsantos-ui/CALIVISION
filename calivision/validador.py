"""Máquina de estados de validação de repetições, independente de câmera (testável)."""
from dataclasses import dataclass
from enum import Enum, auto

class Estado(Enum):
    DETECCAO_INSUFICIENTE = auto()
    POSICAO_INICIAL = auto()
    DESCENDO = auto()
    NO_FUNDO = auto()
    SUBINDO = auto()

class Resultado(Enum):
    NADA = auto()
    VALIDA = auto()
    REJEITADA = auto()

@dataclass
class Config:
    topo: float          # ângulo considerado "estendido"
    fundo: float         # ângulo que precisa ser atingido (amplitude mínima)
    margem: float = 12   # histerese
    frames_fundo: int = 3
    frames_topo: int = 3
    visib_min: float = 0.6
    suavizacao: float = 0.5   # EMA

AGACHAMENTO = Config(topo=160, fundo=100)
FLEXAO = Config(topo=155, fundo=90)

class Validador:
    def __init__(self, cfg: Config):
        self.cfg, self.estado = cfg, Estado.DETECCAO_INSUFICIENTE
        self.reps = self.rejeitadas = 0
        self.motivo = ""
        self._ema = None
        self._cont = 0
        self._falha = False

    def atualizar(self, angulo, visibilidade, postura_ok=True) -> Resultado:
        c = self.cfg
        if angulo is None or visibilidade < c.visib_min:
            self.estado, self._ema, self._cont = Estado.DETECCAO_INSUFICIENTE, None, 0
            return Resultado.NADA
        self._ema = angulo if self._ema is None else c.suavizacao*self._ema + (1-c.suavizacao)*angulo
        a, e = self._ema, self.estado
        if e == Estado.DETECCAO_INSUFICIENTE:
            self._cont = self._cont + 1 if a >= c.topo else 0
            if self._cont >= c.frames_topo:
                self.estado, self._cont = Estado.POSICAO_INICIAL, 0
        elif e == Estado.POSICAO_INICIAL:
            if a < c.topo - c.margem:
                self.estado, self._falha = Estado.DESCENDO, not postura_ok
        elif e == Estado.DESCENDO:
            if not postura_ok: self._falha = True
            if a <= c.fundo:
                self._cont += 1
                if self._cont >= c.frames_fundo:
                    self.estado, self._cont = Estado.NO_FUNDO, 0
            else:
                self._cont = 0
                if a >= c.topo:
                    return self._rejeitar("Movimento incompleto")
        elif e == Estado.NO_FUNDO:
            if a > c.fundo + c.margem: self.estado = Estado.SUBINDO
        elif e == Estado.SUBINDO:
            if not postura_ok: self._falha = True
            if a >= c.topo:
                self._cont += 1
                if self._cont >= c.frames_topo:
                    self._cont = 0
                    if self._falha: return self._rejeitar("Postura fora do critério")
                    self.estado, self.reps, self.motivo = Estado.POSICAO_INICIAL, self.reps+1, ""
                    return Resultado.VALIDA
            else:
                self._cont = 0
                if a <= c.fundo: self.estado = Estado.NO_FUNDO
        return Resultado.NADA

    def _rejeitar(self, motivo):
        self.estado, self.motivo, self._cont = Estado.POSICAO_INICIAL, motivo, 0
        self.rejeitadas += 1
        return Resultado.REJEITADA

PARALELAS = Config(topo=155, fundo=90)   # mergulho: sem exigência de alinhamento de tronco

class Isometrico:
    """Validação por tempo (prancha): só acumula segundos com postura válida e corpo visível.
    Perda de postura/detecção por mais de `tolerancia` s zera a contagem do bloco atual."""
    def __init__(self, meta_s, tolerancia=0.7, estabilizar=1.0, visib_min=0.6):
        self.meta, self.tol, self.estab, self.vmin = meta_s, tolerancia, estabilizar, visib_min
        self.segundos = 0.0      # tempo validado acumulado
        self.melhor_bloco = 0.0
        self._bloco = 0.0
        self._ini = None         # início da postura válida contínua
        self._ultimo_ok = None
        self._t_ant = None
        self.motivo = "Aguardando posição"

    @property
    def concluido(self): return self.segundos >= self.meta

    def atualizar(self, t, postura_ok, visibilidade):
        valido = postura_ok and visibilidade >= self.vmin
        if valido:
            if self._ini is None: self._ini = t
            self._ultimo_ok = t
            if t - self._ini >= self.estab:       # só conta após estabilizar
                if self._t_ant is not None: 
                    dt = t - self._t_ant
                    self.segundos += dt; self._bloco += dt
                self.motivo = "Mantendo posição"
            else: self.motivo = "Estabilizando"
        else:
            self.motivo = "Corpo não visível" if visibilidade < self.vmin else "Alinhe quadril e tronco"
            if self._ultimo_ok is not None and t - self._ultimo_ok > self.tol:
                self.melhor_bloco = max(self.melhor_bloco, self._bloco)
                self._bloco, self._ini = 0.0, None
        self._t_ant = t if valido else None
        return self.concluido
