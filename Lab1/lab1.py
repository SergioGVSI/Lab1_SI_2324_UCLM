import json
from abc import abstractmethod, ABC
import time


# Clase que inicializa el problema
class Problema:
    def __init__(self, problema_json):
        # Bloque de código encargado de cargar el json que ha sido recibido como parámetro
        with open(problema_json, 'r') as f:
            ciudad = json.load(f)
        # Inicializamos los datos del problema y los almacenamos en variables
        self.filas = ciudad['city']['rows']
        self.columnas = ciudad['city']['columns']
        self.inicio = Nodo(Estado(ciudad['departure'][0], ciudad['departure'][1]))
        self.bloqueados = set(map(tuple, ciudad['city']['blocked']))
        self.peligros = set(map(tuple, ciudad['dangers']))
        self.destinos = set(map(tuple, ciudad['trapped']))
        self.personas_rescatadas = 0
        self.media_nodos_generados = 0.0
        self.media_nodos_expandidos = 0.0
        self.media_tiempo_ejecucion = 0.0
        self.media_tamaño_solucion = 0.0
        self.media_coste_solucion = 0.0

    # Verifica si ese estado es de peligro
    def es_peligro(self, estado):
        return (estado.fila, estado.columna) in self.peligros

    # Verifica si ese estado está bloqueado
    def es_bloqueado(self, estado):
        return (estado.fila, estado.columna) in self.bloqueados

    # Verifica si es un estado válido, se usará para generar los sucesores y que el agente no se salga de los límites
    def es_valido(self, estado):
        return 0 <= estado.fila < self.filas and 0 <= estado.columna < self.columnas and not self.es_bloqueado(estado)

    # Generamos las estadísticas globales tras el rescate de todas las personas y las reseteamos para poder usar otro algoritmo
    def estadisticas_globales(self):
        print("Final statistics")
        print("----------------")
        print("Number of rescued people:", self.personas_rescatadas, "of", len(self.destinos))
        print("Mean number of generated nodes:", (self.media_nodos_generados / len(self.destinos)))
        print("Mean number of expanded nodes:", (self.media_nodos_expandidos / len(self.destinos)))
        print("Mean execution time:", (self.media_tiempo_ejecucion / len(self.destinos)))
        print("Mean solution length:", (self.media_tamaño_solucion / len(self.destinos)))
        print("Mean solution cost:", (self.media_coste_solucion / len(self.destinos)))
        self.resetear_estadisticas()

    # Método usado para resetear las estadísticas
    # Debemos de hacerlo si queremos aplicar otro algoritmo
    def resetear_estadisticas(self):
        self.personas_rescatadas = 0
        self.media_nodos_generados = 0.0
        self.media_nodos_expandidos = 0.0
        self.media_tiempo_ejecucion = 0.0
        self.media_tamaño_solucion = 0.0
        self.media_coste_solucion = 0.0


# Clase en la que definimos el estado
class Estado:
    def __init__(self, fila, columna):
        self.fila = fila
        self.columna = columna

    def __eq__(self, otro):
        return (self.fila, self.columna) == (otro.fila, otro.columna)

    def __hash__(self):
        return hash((self.fila, self.columna))

    def __repr__(self):
        return str(f"(fila {self.fila}, columna {self.columna})")


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
    def __init__(self, estado, accion=None, padre=None, nid=0):
        self.estado = estado
        self.padre = padre
        self.coste = accion.coste + padre.coste if padre is not None else 0
        self.profundidad = padre.profundidad + 1 if padre is not None else 0
        self.accion = accion
        self.id = nid

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
    def extraer_nodo(self, nodo_lista):
        pass

    @abstractmethod
    def comprobar_vacio(self, nodo):
        pass

    def __init__(self, ciudad):
        self.ciudad = ciudad
        self.tiempo_ejecucion = None
        self.nodos_cerrados = set()
        self.nodos_abiertos = None  # En función del algoritmo se usará un tipo como nodos abiertos u otros
        self.nodos_expandidos = 0
        self.nodos_generados = 0
        self.coste = 0

    def generar_sucesores(self, nodo):
        # Posibles movimientos
        movimientos = [(-1, 0), (0, 1), (1, 0), (0, -1)]  # Arriba, derecha, abajo, izquierda
        sucesores = []
        # Realizamos todos los posibles movimientos, si son válidos y no son peligro se almacenan como sucesores
        # Tras generar los sucesores, consideramos el nodo ya expandido
        for mx, my in movimientos:
            nueva_fila = nodo.estado.fila + mx
            nueva_columna = nodo.estado.columna + my
            nuevo_estado = Estado(nueva_fila, nueva_columna)
            if self.ciudad.es_valido(nuevo_estado):
                accion_realizada = Accion(nuevo_estado, self.decodificar_accion((mx, my)), self.ciudad)
                nuevo_nodo = Nodo(nuevo_estado, accion_realizada, nodo, nodo.id + 1)
                sucesores.append(nuevo_nodo)
        self.nodos_expandidos += 1
        return sucesores

    # Método auxiliar para decodificar la acción para los sucesores
    def decodificar_accion(self, accion):
        if accion == (-1, 0):
            return 'UP'
        elif accion == (0, 1):
            return 'RIGHT'
        elif accion == (1, 0):
            return 'DOWN'
        elif accion == (0, -1):
            return 'LEFT'

    # Iniciamos la búsqueda a la persona recibida como parámetro
    # Al encontrar a la persona rescatada recuperamos el camino y generar las estadísticas de este rescate
    # En caso contrario genera sucesores viables y continua la búsqueda

    def iniciar_busqueda(self, rescate):
        iniciar_temporizador = time.perf_counter()
        self.insertar_nodo(self.ciudad.inicio, self.nodos_abiertos)
        print("Rescuing person at position:", (rescate.estado.fila, rescate.estado.columna))
        print("-----------------------------------")
        while not self.comprobar_vacio(self.nodos_abiertos):
            nodo = self.extraer_nodo(self.nodos_abiertos)
            if nodo.estado == rescate.estado:
                self.coste = nodo.coste
                finalizar_temporizador = time.perf_counter()
                self.tiempo_ejecucion = (finalizar_temporizador - iniciar_temporizador)
                camino = self.recuperar_camino(nodo)
                return self.generar_estadisticas(camino)
            else:
                if nodo.estado not in self.nodos_cerrados:
                    sucesores = self.generar_sucesores(nodo)
                    for sucesor in sucesores:
                        self.insertar_nodo(sucesor, self.nodos_abiertos)
                self.nodos_cerrados.add(nodo.estado)

    # Método auxiliar para recuperar el camino tras encontrar a la persona a rescatar
    def recuperar_camino(self, nodo):
        camino = []
        while nodo.padre:
            camino.append(nodo.accion.accion)
            nodo = nodo.padre
        return camino

    # Generamos las estadísticas de una búsqueda tras finalizar y almacenamos dichos datos para las estadísticas globales
    def generar_estadisticas(self, camino):
        print("Generated nodes:", self.nodos_generados)
        print("Expanded nodes:", self.nodos_expandidos)
        print("Execution time:", self.tiempo_ejecucion)
        print("Solution length:", len(camino))
        print("Solution cost:", float(self.coste))
        print("Solution:", list(reversed(camino)))
        print(" ")
        self.ciudad.personas_rescatadas += 1
        self.ciudad.media_nodos_generados += self.nodos_generados
        self.ciudad.media_nodos_expandidos += self.nodos_expandidos
        self.ciudad.media_tiempo_ejecucion += self.tiempo_ejecucion
        self.ciudad.media_tamaño_solucion += len(camino)
        self.ciudad.media_coste_solucion += float(self.coste)


# Algoritmo en anchura
class Anchura(Search):

    def __init__(self, ciudad):
        super().__init__(ciudad)
        self.nodos_abiertos = []

    def insertar_nodo(self, nodo, nodo_lista):
        nodo_lista.append(nodo)
        self.nodos_generados += 1

    def extraer_nodo(self, nodo_lista):
        return nodo_lista.pop(0)

    def comprobar_vacio(self, nodo_lista):
        return nodo_lista.__len__() == 0


if __name__ == '__main__':
    problema = Problema('Lab1/problemas/instance-20-20-33-8-33-2023.json')  # Inicializamos el problema cargando el json y parametrizandolo
    #problema = Problema('test.json')
    nodos_de_rescate = []
    for persona in problema.destinos:
        nodos_de_rescate.append(Nodo(Estado(persona[0], persona[1])))
    for persona_a_rescatar in nodos_de_rescate:
        Anchura(problema).iniciar_busqueda(persona_a_rescatar)
    problema.estadisticas_globales()
