import sys
try:
    from mazegenerator import MazeGenerator
except ModuleNotFoundError:
    print("[WARNING] Missing Module mazegenerator", file=sys.stderr)
    exit(1)
# 1. Instancias la clase usando los datos que leíste con Pydantic
# (Nota: Asegúrate de adaptar tu ancho/alto a una tupla (x, y))
mi_laberinto = MazeGenerator(
    size=(15, 15),
)

# 2. Ejecutas el algoritmo generador
mi_laberinto.generate()

# 3. Extraes el resultado final para usarlo en tu juego
matriz_juego = mi_laberinto.maze
for r in matriz_juego:
    for c in r:
        print(c, end=" ")
    print()
