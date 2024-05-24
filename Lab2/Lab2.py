import json
import numpy as np
import os
from draw_policy import *

class Entorno:
    def __init__(self, entorno_json, penalizacion, pen_peligro, estocasticidad):
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
        self.penalizacion_peligro = pen_peligro
        self.estocasticidad = estocasticidad

    # Verifica si ese estado es de peligro
    def es_peligro(self, estado):
        return (estado.fila, estado.columna) in self.peligros

    # Verifica si ese estado está bloqueado
    def es_bloqueado(self, estado):
        return (estado.fila, estado.columna) in self.bloqueados

    # Verifica si es un estado válido, se usará para generar los sucesores y que el agente no se salga de los límites
    def es_valido(self, estado):
        return 0 <= estado.fila < self.filas and 0 <= estado.columna < self.columnas and not self.es_bloqueado(estado)

    def es_destino(self, estado):
        return (estado.fila, estado.columna) in self.destinos or (estado.fila, estado.columna) in self.peligros_fatales

    def es_accion_valida(self, accion, estado):
        if accion == 0:
            return self.es_valido(Estado(estado.fila - 1, estado.columna))
        elif accion == 1:
            return self.es_valido(Estado(estado.fila, estado.columna + 1))
        elif accion == 2:
            return self.es_valido(Estado(estado.fila + 1, estado.columna))
        else:
            return self.es_valido(Estado(estado.fila, estado.columna - 1))

    # El agente sólo desea aplicar una accion en base a un estado, es el entorno el encargado de que esa aplicacion se ejecute
    # así como se obtenga la recompensa

    def mover_agente(self, accion_elegida, estado_actual, explorar):
        if explorar:
            accion_elegida = np.random.choice([0, 1, 2, 3])
        nuevo_estado, recompensa = self.aplicar_accion(accion_elegida, estado_actual)
        return nuevo_estado, recompensa

    def aplicar_accion(self, accion, estado):
        accion_elegida = accion
        estado_actual = estado

        if np.random.rand() > self.estocasticidad:
            accion_elegida = self.aplicar_estocasticidad(accion)

        if accion_elegida == 0:
            nuevo_estado = Estado(estado.fila - 1, estado.columna)
            if not self.es_valido(nuevo_estado):
                nuevo_estado = estado_actual  # Nos quedamos en el sitio si nos salimos de los límites
            recompensa = self.obtener_recompensa(nuevo_estado)
        elif accion_elegida == 1:
            nuevo_estado = Estado(estado.fila, estado.columna + 1)
            if not self.es_valido(nuevo_estado):
                nuevo_estado = estado_actual  # Nos quedamos en el sitio si nos salimos de los límites
            recompensa = self.obtener_recompensa(nuevo_estado)
        elif accion_elegida == 2:
            nuevo_estado = Estado(estado.fila + 1, estado.columna)
            if not self.es_valido(nuevo_estado):
                nuevo_estado = estado_actual  # Nos quedamos en el sitio si nos salimos de los límites
            recompensa = self.obtener_recompensa(nuevo_estado)
        else:
            nuevo_estado = Estado(estado.fila, estado.columna - 1)
            if not self.es_valido(nuevo_estado):
                nuevo_estado = estado_actual  # Nos quedamos en el sitio si nos salimos de los límites
            recompensa = self.obtener_recompensa(nuevo_estado)
        return nuevo_estado, recompensa

    def aplicar_estocasticidad(self, accion):
        movimientos = [0, 1, 2, 3]
        if accion == movimientos[0]:  # Si Arriba
            if np.random.rand() * 0.2 < 0.1:
                return movimientos[3]  # Izquierda
            else:
                return movimientos[1]  # Derecha

        if accion == movimientos[1]:  # Si Derecha
            if np.random.rand() * 0.2 < 0.1:
                return movimientos[0]  # Arriba
            else:
                return movimientos[2]  # Abajo

        if accion == movimientos[2]:  # Si Abajo
            if np.random.rand() * 0.2 < 0.1:
                return movimientos[1]  # Izquierda
            else:
                return movimientos[3]  # Derecha

        if accion == movimientos[3]:  # Si Izquierda
            if np.random.rand() * 0.2 < 0.1:
                return movimientos[2]  # Abajo
            else:
                return movimientos[0]  # Arriba

    def obtener_recompensa(self, estado):

        for destino in self.destinos:
            if (estado.fila, estado.columna) == destino:
                return self.destinos.get(destino)

        for peligro in self.peligros:
            if (estado.fila, estado.columna) == peligro:
                return self.penalizacion_peligro

        for peligro_fatal in self.peligros_fatales:
            if (estado.fila, estado.columna) == peligro_fatal:
                return self.peligros_fatales.get(peligro_fatal)
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
        return str(f"({self.fila},{self.columna})")


class Agente:
    # Constantes para decodificar los movimientos
    mov_numericos = [0, 1, 2, 3]
    direcciones = {
        0: "UP",
        1: "RIGHT",
        2: "DOWN",
        3: "LEFT"
    }

    def __init__(self, entorno, alpha, gamma, epsilon, decaimiento_epsilon):
        self.entorno = entorno
        self.movimientos = [Agente.direcciones[movimiento] for movimiento in
                            Agente.mov_numericos]  # Arriba, Derecha, Abajo, Izquierda respectivamente
        self.qtabla = np.zeros((entorno.filas, entorno.columnas, len(self.mov_numericos)))
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.decaimiento_epsilon = decaimiento_epsilon

    # El agente sólo desea aplicar una accion en base a un estado, es el entorno el encargado de que esa aplicacion se ejecute
    # así como se obtenga la recompensa
    def realizar_movimiento(self, accion_elegida, estado_actual):
        explorar = np.random.rand() < self.epsilon  # Es el agente quien decide o no explorar
        nuevo_estado, recompensa = self.entorno.mover_agente(accion_elegida, estado_actual, explorar)
        return nuevo_estado, recompensa

    def max_q(self, estado):
        posibles_acciones = [self.qtabla[estado.fila][estado.columna][accion] for accion in self.mov_numericos]
        aux = posibles_acciones
        for accion in range(len(aux)):
            if not self.entorno.es_accion_valida(accion, estado):
                # Con esto, descartamos los índices que llevan a acciones no válidas
                aux[accion] = np.min(self.entorno.recompensas_finales) - 50
        indices_maximos = np.where(aux == np.max(aux))[0]
        accion_elegida = np.random.choice(indices_maximos)  # En caso de tener varios índices iguales
        return accion_elegida

    def actualizar_qtabla(self, estado_actual, accion_elegida, recompensa, nuevo_estado, destino):
        if destino:
            nuevo_valor = (1.0 - self.alpha) * self.qtabla[estado_actual.fila][estado_actual.columna][
                accion_elegida] + self.alpha * recompensa
            self.qtabla[estado_actual.fila][estado_actual.columna][accion_elegida] = nuevo_valor

        else:
            nuevo_valor = (1.0 - self.alpha) * self.qtabla[estado_actual.fila][estado_actual.columna][
                accion_elegida] + self.alpha * (
                                  recompensa + self.gamma * self.qtabla[nuevo_estado.fila][nuevo_estado.columna][
                              self.max_q(nuevo_estado)])
            self.qtabla[estado_actual.fila][estado_actual.columna][accion_elegida] = nuevo_valor
        return nuevo_valor

    def ejecutar_algoritmo(self, num_episodios):
        for i in range(num_episodios):
            self.episodio()
        return self.obtener_politica()

    def episodio(self):
        estado_actual = self.entorno.inicio
        destino = False
        while not destino:
            # print("-------------------")
            # print(f"Estado actual {estado_actual}")
            accion_elegida = self.max_q(estado_actual)
            # print(f"Accion elegida {self.movimientos[accion_elegida]}")
            nuevo_estado, recompensa = self.realizar_movimiento(accion_elegida, estado_actual)
            # print(f"Nuevo estado {nuevo_estado}")
            # print(f"Recompensa {recompensa}")
            if self.entorno.es_destino(nuevo_estado):
                destino = True
                self.epsilon *= self.decaimiento_epsilon  # Decaimiento de épsilon en cada final de episodio
            self.actualizar_qtabla(estado_actual, accion_elegida, recompensa, nuevo_estado, destino)
            estado_actual = nuevo_estado

    def obtener_politica(self):
        politica = {}
        estados_posibles = [(fila, columna) for fila in range(self.entorno.filas) for columna in
                            range(self.entorno.columnas)]
        for estado in estados_posibles:
            if estado not in self.entorno.destinos and estado not in self.entorno.peligros_fatales and estado not in self.entorno.bloqueados:
                politica[estado[0], estado[1]] = self.direcciones.get(self.max_q(Estado(estado[0], estado[1])))
        print(self.qtabla)
        return politica


if __name__ == '__main__':
    # Inicializamos el problema cargando el json y parametrizandolo
    penalizacion_entorno = -0.04
    penalizacion_peligro = -5
    estocasticidad_entorno = 0.8
    numero_episodios = 1000
    alpha = 0.2
    gamma = 0.9
    epsilon = 0.2
    decaimiento_epsilon = 0.05

    entorno = Entorno('./initial-rl-instances/lesson5-rl.json', penalizacion_entorno, penalizacion_peligro,
                      estocasticidad_entorno)
    algoritmo = Agente(entorno, alpha, gamma, epsilon, decaimiento_epsilon)

    json_dir = os.path.join(os.getcwd(), './initial-rl-instances/lesson5-rl.json')

    politica = algoritmo.ejecutar_algoritmo(numero_episodios)

    for estado, accion in politica.items():
        print(f"\"({estado[0]}, {estado[1]})\": \"{accion}\"")

    draw_policy_map(json_dir, politica)
