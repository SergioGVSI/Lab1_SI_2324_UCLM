import json

class Problema:
    def __init__ (self, problema_json):
        # Bloque de código encargado de cargar el json que ha sido recibido como parámetro
        with open(problema_json, 'r') as f:
            problema_json = json.load(f)



if __name__ == '__main__':
    problema = Problema('test.json') # Inicializamos el problema cargando el json y parametrizandolo
