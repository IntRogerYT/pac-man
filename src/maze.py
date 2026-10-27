import sys
try:
    from mazegenerator import MazeGenerator
except ModuleNotFoundError:
    print("Error: Missing module 'mazegenerator'. "
          "Run 'make install' to install it.", file=sys.stderr)
    exit(1)
mi_laberinto = MazeGenerator(
    size=(15, 15),
)

mi_laberinto.generate()

matriz_juego = mi_laberinto.maze
for r in matriz_juego:
    for c in r:
        print(c, end=" ")
    print()
