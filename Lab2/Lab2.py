import json
import numpy as np


class Entorno:
    def __init__(self, entorno_json, penalizacion, penalizacion_peligro):
        # Bloque de código encargado de cargar el json que ha sido recibido como parámetro
        with open(entorno_json, 'r') as f:
            ciudad = json.load(f)
        # Inicializamos los datos del problema y los almacenamos en variables
        self.filas = ciudad['city']['rows']
        self.columnas = ciudad['city']['columns']
        self.inicio = Estado(ciudad['departure'][0], ciudad['departure'][1])
        self.bloqueados = set(map(tuple, ciudad['city']['blocked']))
        self.peligros = set(map(tuple, ciudad['dangers']))
        self.peligros_fatales = {(x, y): z for x, y, z, in ciudad['fatal_dangers']}
        self.destinos = {(x, y): z for x, y, z, in ciudad['trapped']}
        self.recompensas_finales = list(self.destinos.values()) + list(self.peligros_fatales.values())
        self.penalizacion = penalizacion
        self.penalizacion_peligro = penalizacion_peligro

    # Verifica si ese estado es de peligro
    def es_peligro(self, estado):
        return (estado.fila, estado.columna) in self.peligros

    # Verifica si ese estado está bloqueado
    def es_bloqueado(self, estado):
        return (estado.fila, estado.columna) in self.bloqueados

    # Verifica si es un estado válido, se usará para generar los sucesores y que el agente no se salga de los límites
    def es_valido(self, estado):
        return 0 <= estado.fila < self.filas and 0 <= estado.columna < self.columnas and not self.es_bloqueado(estado)

    # El agente sólo desea aplicar una accion en base a un estado, es el entorno el encargado de que esa aplicacion se ejecute
    # así como se obtenga la recompensa

    def aplicar_accion(self, accion, estado):
        if accion == 0:
            nuevo_estado = Estado(estado.fila + 1, estado.columna)
            recompensa = self.obtener_recompensa(nuevo_estado)
        elif accion == 1:
            nuevo_estado = Estado(estado.fila, estado.columna + 1)
            recompensa = self.obtener_recompensa(nuevo_estado)
        elif accion == 2:
            nuevo_estado = Estado(estado.fila - 1, estado.columna)
            recompensa = self.obtener_recompensa(nuevo_estado)
        else:
            nuevo_estado = Estado(estado.fila, estado.columna - 1)
            recompensa = self.obtener_recompensa(nuevo_estado)

        return nuevo_estado, recompensa

    def obtener_recompensa(self, estado):

        for destino in self.destinos:
            if (estado.fila, estado.columna) == destino:
                return self.destinos.get(destino)

        for peligro in self.peligros:
            if (estado.fila, estado.columna) == peligro:
                return self.penalizacion_peligro

        for peligro_fatal in self.peligros_fatales:
            if (estado.fila, estado.columna) == peligro_fatal:
                return self.destinos.get(peligro_fatal)

        return self.penalizacion


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
    # Constantes para decodificar los movimientos
    movimientos = [0, 1, 2, 3]
    direcciones = {
        0: "UP",
        1: "RIGHT",
        2: "DOWN",
        3: "LEFT"
    }

    def __init__(self, entorno):
        self.entorno = entorno
        self.movimientos = [Agente.direcciones[movimiento] for movimiento in
                            Agente.movimientos]  # Arriba, Derecha, Abajo, Izquierda respectivamente
        self.qtabla = np.zeros((entorno.filas, entorno.columnas, len(self.movimientos)))

    # El agente sólo desea aplicar una accion en base a un estado, es el entorno el encargado de que esa aplicacion se ejecute
    # así como se obtenga la recompensa
    def mover_agente(self, accion, estado):
        pass


if __name__ == '__main__':
    # Inicializamos el problema cargando el json y parametrizandolo
    penalizacion_entorno = 0.5
    penalizacion_peligro = -5
    problema = Entorno('./initial-rl-instances/lesson5-rl.json', penalizacion_entorno, penalizacion_peligro)
