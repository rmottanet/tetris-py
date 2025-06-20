import pygame
import random
import sys

# --- Game definitions ---
CELL_SIZE = 20  # Tamanho de cada célula (bloco) em pixels
BOARD_WIDTH_CELLS = 10  # Largura do tabuleiro em células
BOARD_HEIGHT_CELLS = 20  # Altura do tabuleiro em células

# window size
WINDOW_WIDTH_PIXELS = BOARD_WIDTH_CELLS * CELL_SIZE
WINDOW_HEIGHT_PIXELS = BOARD_HEIGHT_CELLS * CELL_SIZE

# cores para as peças
COLORS = {
    "I": (0, 255, 255),    # Ciano
    "O": (255, 255, 0),    # Amarelo
    "T": (128, 0, 128),    # Roxo
    "S": (0, 255, 0),      # Verde
    "Z": (255, 0, 0),      # Vermelho
    "J": (0, 0, 255),      # Azul
    "L": (255, 165, 0)     # Laranja
}

# peças (matrizes 4x4, 1 para bloco, 0 para vazio)
# formas definidas de maneira que a coluna mais à esquerda e a linha mais acima
# que contenham um bloco '1' sejam consideradas a origem (0,0) da peça.
SHAPES = {
    "I": [[0,0,0,0], [1,1,1,1], [0,0,0,0], [0,0,0,0]],
    "O": [[1,1], [1,1]],
    "T": [[0,1,0], [1,1,1], [0,0,0]],
    "S": [[0,1,1], [1,1,0], [0,0,0]],
    "Z": [[1,1,0], [0,1,1], [0,0,0]],
    "J": [[0,0,1], [1,1,1], [0,0,0]],
    "L": [[1,0,0], [1,1,1], [0,0,0]]
}

# --- Game Variables ---
board = []  # tabuleiro (lista de listas)
current_piece = None
next_piece = None
piece_x, piece_y = 0, 0  # posição da peça no tabuleiro (células, 0-based)

drop_timer = 0
drop_interval = 0.5  # tempo em segundos para a peça cair
game_over = False

# --- Pygame Start ---
pygame.init()
screen = pygame.display.set_mode((WINDOW_WIDTH_PIXELS, WINDOW_HEIGHT_PIXELS))
pygame.display.set_caption("Tetris Pygame")
clock = pygame.time.Clock()

# --- Game Functions ---

def initialize_board():
    """Inicializa o tabuleiro do jogo com células vazias (0)."""
    global board
    board = [[0 for _ in range(BOARD_WIDTH_CELLS)] for _ in range(BOARD_HEIGHT_CELLS)]

def get_random_piece():
    """Gera uma nova peça aleatória."""
    piece_types = list(SHAPES.keys())
    random_type = random.choice(piece_types)
    return {
        "type": random_type,
        "shape": SHAPES[random_type],
        "color": COLORS[random_type]
    }

def spawn_new_piece():
    """Gera uma nova peça e a posiciona no topo do tabuleiro.
    Verifica game over se a peça nascer colidindo."""
    global current_piece, next_piece, piece_x, piece_y, game_over

    current_piece = next_piece if next_piece else get_random_piece()
    next_piece = get_random_piece()

    # centraliza a peça.
    # largura da peça é o número de colunas na primeira linha da sua forma.
    piece_width = len(current_piece["shape"][0])
    piece_x = (BOARD_WIDTH_CELLS - piece_width) // 2
    piece_y = 0  # peças começam na linha 0 do tabuleiro

    # game over se a peça já nasce colidindo
    if check_collision(current_piece, piece_x, piece_y):
        game_over = True
        print("Game Over!")

def move_piece(dx, dy):
    """Tenta mover a peça em dx (horizontal) e dy (vertical).
    Se colidir e for um movimento para baixo, a peça é fixada."""
    global piece_x, piece_y, drop_timer

    new_x = piece_x + dx
    new_y = piece_y + dy

    # se a nova posição NÃO CAUSA colisão, move a peça.
    if not check_collision(current_piece, new_x, new_y):
        piece_x = new_x
        piece_y = new_y
        return True # movimento bem-sucedido
    else:
        # se colidiu, e o movimento era para baixo (dy > 0), a peça deve ser fixada.
        if dy > 0:
            lock_piece()
            clear_lines()
            spawn_new_piece()
        return False # movimento falhou

def rotate_piece():
    """Rotaciona a peça 90 graus no sentido horário e tenta realizar um "wall kick"."""
    global current_piece, piece_x, piece_y

    original_shape = current_piece["shape"]
    n = len(original_shape) # assumindo que a peça é quadrada (n x n)

    # cria uma nova matriz para a peça rotacionada
    new_shape = [[0 for _ in range(n)] for _ in range(n)]

    # lógica de rotação 90 graus no sentido horário
    for y in range(n):
        for x in range(n):
            new_shape[x][n - 1 - y] = original_shape[y][x]

    # salva a forma atual para poder restaurar se a rotação colidir e não houver "wall kick"
    temp_original_shape = current_piece["shape"]
    current_piece["shape"] = new_shape  # aplica a nova forma temporariamente para checar colisão

    # verifica colisão após a rotação
    if check_collision(current_piece, piece_x, piece_y):
        # se colidiu, tenta ajustar a posição (simples "wall kick" para o lado)
        # tenta mover para a esquerda, depois para a direita
        if not check_collision(current_piece, piece_x - 1, piece_y):
            piece_x -= 1
        elif not check_collision(current_piece, piece_x + 1, piece_y):
            piece_x += 1
        else:
            # se nenhuma tentativa de ajuste funcionou, reverte a rotação
            current_piece["shape"] = temp_original_shape
    # rotação foi bem-sucedida ou revertida, a forma da peça já está atualizada ou restaurada.


def check_collision(piece, x, y):
    """Verifica se a peça colide com as bordas do tabuleiro ou blocos existentes."""
    shape = piece["shape"]

    for sy, row in enumerate(shape): # sy é a linha dentro da forma da peça (0-based)
        for sx, cell_value in enumerate(row): # sx é a coluna dentro da forma da peça (0-based)
            if cell_value == 1: # se há um bloco nesta parte da forma da peça
                board_x = x + sx # calcula a coordenada X no tabuleiro (0-based)
                board_y = y + sy # calcula a coordenada Y no tabuleiro (0-based)

                # verifica colisão com as bordas do tabuleiro
                if board_x < 0 or board_x >= BOARD_WIDTH_CELLS or \
                   board_y >= BOARD_HEIGHT_CELLS:
                    return True # colidiu com uma borda (esquerda, direita ou chão)

                # verifica colisão com blocos já fixos no tabuleiro
                # garante que board_y é válido antes de acessar o tabuleiro
                if board_y >= 0 and board[board_y][board_x] != 0:
                    return True # colidiu com um bloco já existente
    return False # nenhuma colisão detectada

def lock_piece():
    """Fixa a peça atual no tabuleiro."""
    shape = current_piece["shape"]
    piece_color = current_piece["color"]

    for sy, row in enumerate(shape):
        for sx, cell_value in enumerate(row):
            if cell_value == 1:
                board_x = piece_x + sx
                board_y = piece_y + sy
                # garante que só se fixa blocos dentro dos limites válidos do tabuleiro
                if 0 <= board_y < BOARD_HEIGHT_CELLS and 0 <= board_x < BOARD_WIDTH_CELLS:
                    board[board_y][board_x] = piece_color

def clear_lines():
    """Remove linhas completas do tabuleiro e move as linhas acima para baixo."""
    global board
    lines_cleared = 0
    # itera de baixo para cima
    y = BOARD_HEIGHT_CELLS - 1
    while y >= 0:
        line_full = True
        for x in range(BOARD_WIDTH_CELLS):
            if board[y][x] == 0:  # Se algum bloco estiver vazio, a linha não está completa
                line_full = False
                break

        if line_full:
            lines_cleared += 1
            # remove a linha completa e insere uma nova linha vazia no topo
            board.pop(y)
            board.insert(0, [0 for _ in range(BOARD_WIDTH_CELLS)])
            # não decrementa 'y' pois a próxima linha a ser verificada (que desceu)
            # agora está na posição 'y' atual.
        else:
            y -= 1 # move para a próxima linha acima se a linha atual não estiver cheia
    # TODO: Implementar pontuação

# --- Draw Functions ---

def draw_board(surface):
    """Desenha o tabuleiro com os blocos fixos na tela."""
    for y in range(BOARD_HEIGHT_CELLS):
        for x in range(BOARD_WIDTH_CELLS):
            cell_color = board[y][x]
            if cell_color != 0:
                pygame.draw.rect(surface, cell_color,
                                 (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE), 0) # Preenchido
                pygame.draw.rect(surface, (0, 0, 0),
                                 (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE), 1) # Borda preta

def draw_current_piece(surface):
    """Desenha a peça que está caindo na tela."""
    if current_piece:
        shape = current_piece["shape"]
        piece_color = current_piece["color"]

        for sy, row in enumerate(shape):
            for sx, cell_value in enumerate(row):
                if cell_value == 1:
                    # calcula a posição em pixels para o bloco da peça
                    # piece_x/y é a origem da peça no tabuleiro (0-based)
                    # sx/sy é a posição do bloco dentro da forma (0-based)
                    draw_x = (piece_x + sx) * CELL_SIZE
                    draw_y = (piece_y + sy) * CELL_SIZE

                    pygame.draw.rect(surface, piece_color,
                                     (draw_x, draw_y, CELL_SIZE, CELL_SIZE), 0) # Preenchido
                    pygame.draw.rect(surface, (0, 0, 0),
                                     (draw_x, draw_y, CELL_SIZE, CELL_SIZE), 1) # Borda preta

def draw_grid(surface):
    """Desenha a grade do tabuleiro."""
    grid_color = (50, 50, 50) # cor cinza escuro para a grade

    # linhas verticais
    for x_pixel in range(0, WINDOW_WIDTH_PIXELS + 1, CELL_SIZE):
        pygame.draw.line(surface, grid_color, (x_pixel, 0), (x_pixel, WINDOW_HEIGHT_PIXELS))
    # linhas horizontais
    for y_pixel in range(0, WINDOW_HEIGHT_PIXELS + 1, CELL_SIZE):
        pygame.draw.line(surface, grid_color, (0, y_pixel), (WINDOW_WIDTH_PIXELS, y_pixel))

# --- Main Loop ---
initialize_board()
spawn_new_piece()

running = True
while running:
    # --- tratamento de eventos ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                move_piece(-1, 0)
            elif event.key == pygame.K_RIGHT:
                move_piece(1, 0)
            elif event.key == pygame.K_DOWN:
                move_piece(0, 1)
                drop_timer = 0 # reseta o timer para queda mais rápida
            elif event.key == pygame.K_UP or event.key == pygame.K_x: # 'up' ou 'x' para girar
                rotate_piece()

    if game_over:
        # apenas encerra o jogo.
        running = False
        continue # pula o restante do loop se o jogo acabou

    # --- Atualização do Estado do Jogo ---
    dt = clock.get_time() / 1000.0  # tempo desde o último frame em segundos
    drop_timer += dt

    if drop_timer >= drop_interval:
        move_piece(0, 1) # tenta mover a peça para baixo
        drop_timer = 0

    # --- Renderização ---
    screen.fill((0, 0, 0))  # limpa a tela com preto
    draw_board(screen)
    draw_current_piece(screen)
    draw_grid(screen)

    pygame.display.flip()  # atualiza a tela inteira
    clock.tick(60)  # limita o framerate a 60 FPS

pygame.quit()
sys.exit()
