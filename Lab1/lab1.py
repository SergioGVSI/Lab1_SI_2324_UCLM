import json
from abc import abstractmethod, ABC


# Clase que inicializa el problema
class Problema:
    def __init__(self, problema_json):
        # Bloque de código encargado de cargar el json que ha sido recibido como parámetro
        with open(problema_json, 'r') as f:
            ciudad = json.load(f)
        # Inicializamos los datos del problema y los almacenamos en variables
        self.filas = ciudad['city']['rows']
        self.columnas = ciudad['city']['columns']
        self.inicio = ciudad['departure']
        self.bloqueados = set(map(tuple, ciudad['city']['blocked']))
        self.peligros = set(map(tuple, ciudad['dangers']))
        self.destinos = set(map(tuple, ciudad['trapped']))

    # Verifica si ese estado es de peligro
    def es_peligro(self, estado):
        return estado in self.bloqueados

    # Verifica si ese estado es de destino
    def es_destino(self, estado):
        return estado in self.destinos

    # Verifica si es un estado válido, se usará para generar los sucesores y que el agente no se salga de los límites
    def es_valido(self, estado):
        return 0 <= estado.fila < self.filas and 0 <= estado.columna < self.columnas and not self.es_peligro(estado)


# Clase en la que definimos el estado
class Estado:
    def __init__(self, fila, columna):
        self.fila = fila
        self.columna = columna

    def __eq__(self, otro):
        return (self.fila, self.columna) == (otro.fila, otro.columna)


# Clase encargada de realizar la acción y el coste de ella misma
class Accion:
    def __init__(self, estado, accion, ciudad):
        self.coste = self.calcular_coste(estado, ciudad)
        self.accion = accion

    def calcular_coste(self, estado, ciudad):
        if not ciudad.es_peligro(estado):
            coste = 1
        else:
            coste = 5
        return coste


# Clase en la que definimos un Nodo
# En función de si el nodo es raíz, tendrá padre así como la acción por la que se ha llegado al nodo
class Nodo:
    def __init__(self, estado, accion=None, padre=None, id=0):
        self.estado = estado
        self.padre = padre
        self.coste = accion.coste + padre.coste if padre is not None else 0
        self.profundidad = padre.profundidad + 1 if padre is not None else 0
        self.accion = accion
        self.id = id

    def __eq__(self, otro):
        return hash(self.estado) == hash(otro)

    def __lt__(self, otro):
        return self.id < otro.id


# Clase genérica Search que se usará como herencia para los distintos tipos de algoritmos
class Search(ABC):
    @abstractmethod
    def insertar_nodo(self, nodo, nodo_lista):
        pass

    @abstractmethod
    def extraer_nodo(self, nodo, nodo_lista):
        pass

    @abstractmethod
    def comprobar_vacio(self, nodo, nodo_lista):
        pass

    def __init__(self, ciudad):
        self.ciudad = ciudad
        self.tiempo_ejecucion = None
        self.nodos_cerrados = set()
        self.nodos_abiertos = None  # En función del algoritmo se usará un tipo como nodos abiertos u otros
        self.nodos_expandidos = 0
        self.coste = 0

    def generar_sucesores(self, nodo):
        # Posibles movimientos
        movimientos = [(-1, 0), (0, 1), (1, 0), (0, -1)]  # Arriba, derecha, abajo, izquierda
        sucesores = []
        # Realizamos todos los posibles movimientos, si son válidos y no son peligro se almacenan como sucesores
        for mx, my in movimientos:
            nueva_fila = nodo.estado.fila + my
            nueva_columna = nodo.estado.columna + mx
            nuevo_estado = Estado(nueva_fila, nueva_columna)
            accion_realizada = Accion(nuevo_estado, self.decodificar_accion((mx, my)), self.ciudad)
            nuevo_nodo = Nodo(nuevo_estado, accion_realizada, nodo, nodo.id + 1)
            if self.ciudad.es_valido(nuevo_nodo) and not self.ciudad.es_peligro(nuevo_nodo):
                sucesores.append(nuevo_nodo)
        return sucesores

    def decodificar_accion(self, accion):
        if accion == (-1, 0):
            return 'UP'
        elif accion == (0, 1):
            return 'RIGHT'
        elif accion == (1, 0):
            return 'DOWN'
        elif accion == (0, -1):
            return 'LEFT'


if __name__ == '__main__':
    problema = Problema('./Lab1/test.json')  # Inicializamos el problema cargando el json y parametrizandolo
