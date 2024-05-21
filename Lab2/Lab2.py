import json

class Problema:
    def __init__(self, problema_json, penalizacion):
        # Bloque de código encargado de cargar el json que ha sido recibido como parámetro
        with open(problema_json, 'r') as f:
            ciudad = json.load(f)
        # Inicializamos los datos del problema y los almacenamos en variables
        self.filas = ciudad['city']['rows']
        self.columnas = ciudad['city']['columns']
        self.inicio = Estado(ciudad['departure'][0], ciudad['departure'][1])
        self.bloqueados = set(map(tuple, ciudad['city']['blocked']))
        self.peligros = set(map(tuple, ciudad['dangers']))
        self.peligros_fatales = {(x, y):z for x, y, z, in ciudad['fatal_dangers']}
        self.destinos = {(x, y):z for x, y, z, in ciudad['trapped']}
        self.recompensas_finales = list(self.destinos.values()) + list(self.peligros_fatales.values())
        self.penalizacion = penalizacion

    # Verifica si ese estado es de peligro
    def es_peligro(self, estado):
        return (estado.fila, estado.columna) in self.peligros

    # Verifica si ese estado está bloqueado
    def es_bloqueado(self, estado):
        return (estado.fila, estado.columna) in self.bloqueados

    # Verifica si es un estado válido, se usará para generar los sucesores y que el agente no se salga de los límites
    def es_valido(self, estado):
        return 0 <= estado.fila < self.filas and 0 <= estado.columna < self.columnas and not self.es_bloqueado(estado)

# Clase en la que definimos el estado
class Estado:
    def __init__(self, fila, columna):
        self.fila = fila
        self.columna = columna

    def __eq__(self, otro):
        return (self.fila, self.columna) == (otro.fila, otro.columna)

    # Usado para comprobar si un estado es o no destino
    def __hash__(self):
        return hash((self.fila, self.columna))

    def __repr__(self):
        return str(f"(fila {self.fila}, columna {self.columna})")

class Agente:
    pass

if __name__ == '__main__':
    # Inicializamos el problema cargando el json y parametrizandolo
    penalizacion_entorno = 0.5
    problema = Problema('./initial-rl-instances/lesson5-rl.json', penalizacion_entorno)
