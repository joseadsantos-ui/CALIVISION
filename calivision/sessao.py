"""Liga os pontos do corpo ao validador do exercício escolhido."""
from .validador import (Validador, Isometrico, Estado, Resultado,
                        AGACHAMENTO, FLEXAO, PARALELAS)

CFG = {"agachamento": AGACHAMENTO, "flexao": FLEXAO, "paralelas": PARALELAS}
MSG = {Estado.DETECCAO_INSUFICIENTE: "Ajuste seu posicionamento",
       Estado.POSICAO_INICIAL: "Posição inicial detectada",
       Estado.DESCENDO: "Descendo…", Estado.NO_FUNDO: "Amplitude atingida — suba",
       Estado.SUBINDO: "Subindo…"}

class Sessao:
    def __init__(self, exercicio, meta):
        self.ex, self.meta = exercicio, meta
        self.iso = exercicio == "prancha"
        self.val = Isometrico(meta) if self.iso else Validador(CFG[exercicio])
        self.log, self.msg, self._flash = [], "Posicione-se diante da câmera", 0

    @property
    def valor(self): return int(self.val.segundos) if self.iso else self.val.reps
    @property
    def concluida(self): return self.val.concluido if self.iso else self.val.reps >= self.meta

    def processar(self, lm, t):
        from .pose import angulo_joelho, angulo_cotovelo_e_alinhamento, alinhamento_corpo
        if self.iso:
            if lm is None: self.val.atualizar(t, False, 0); self.msg = "Corpo não detectado"; return
            ang, vis = alinhamento_corpo(lm)
            self.val.atualizar(t, ang >= 165, vis); self.msg = self.val.motivo
            if self.val.concluido and not self.log: self.log.append(("valida", vis, None))
            return
        if lm is None: self.val.atualizar(None, 0); self.msg = "Corpo não detectado"; return
        if self.ex == "agachamento": ang, vis = angulo_joelho(lm); ok = True
        else:
            ang, vis, ok = angulo_cotovelo_e_alinhamento(lm); ok = ok or self.ex == "paralelas"
        r = self.val.atualizar(ang, vis, ok)
        if r == Resultado.VALIDA:
            self.log.append(("valida", vis, None)); self.msg, self._flash = "Repetição validada ✓", t + 1.0
        elif r == Resultado.REJEITADA:
            self.log.append(("rejeitada", vis, self.val.motivo)); self.msg, self._flash = self.val.motivo, t + 1.5
        elif t >= self._flash: self.msg = MSG[self.val.estado]
