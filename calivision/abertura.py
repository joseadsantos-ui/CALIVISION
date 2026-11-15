"""Tela de abertura: logo com o nome do aplicativo logo abaixo."""
import os
import cv2
import numpy as np

LOGO = os.path.join(os.path.dirname(__file__), "..", "assets", "logo.png")
NOME = "CALIVISION"
CIANO_BGR = (255, 217, 0)

def montar_abertura(largura=900, altura=700):
    tela = np.zeros((altura, largura, 3), dtype=np.uint8)
    logo = cv2.imread(LOGO)
    altura_texto = 110                      # espaço reservado para o nome abaixo do logo
    if logo is not None:
        h_max = altura - altura_texto - 40
        esc = min(h_max / logo.shape[0], (largura - 80) / logo.shape[1])
        logo = cv2.resize(logo, None, fx=esc, fy=esc, interpolation=cv2.INTER_AREA)
        y0, x0 = 20, (largura - logo.shape[1]) // 2
        tela[y0:y0+logo.shape[0], x0:x0+logo.shape[1]] = logo
        y_nome = y0 + logo.shape[0] + 70
    else:
        y_nome = altura // 2
    fonte, esp = cv2.FONT_HERSHEY_DUPLEX, 2
    (tw, _), _ = cv2.getTextSize(NOME, fonte, 1.8, esp)
    cv2.putText(tela, NOME, ((largura - tw) // 2, y_nome), fonte, 1.8, CIANO_BGR, esp, cv2.LINE_AA)
    return tela

def mostrar_abertura(duracao_ms=2500):
    cv2.imshow("CALIVISION", montar_abertura())
    cv2.waitKey(duracao_ms)
    cv2.destroyAllWindows()
