# CALIVISION — calistenia validada por câmera (fases 1–4)
Treino validado por câmera: só conta repetição com ciclo completo (topo → fundo → topo).

## Instalar (Python 3.10–3.11 recomendado)
    python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
    pip install -r requirements.txt
## Usar
    python main.py cadastrar "Seu Nome" voce@email.com
    python main.py treinar voce@email.com --exercicio flexao --series 3 --reps 10
    python main.py treinar voce@email.com --exercicio prancha --series 3 --reps 30   # reps = segundos
Teclas: p = pausa, q = encerrar. Câmera de lado, corpo inteiro visível, boa luz.
## Testes (sem câmera)
    pytest
## Privacidade
Processamento local, sem gravar vídeo, dados em ~/.calivision/calivision.db.
## Limitações
Estimativa por pose 2D; não garante execução correta nem ausência de lesão.
