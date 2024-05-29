import json
import numpy as np
import os
from draw_policy import *
from time import time


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

    # Verifica si ese estado está bloqueado
    def es_bloqueado(self, estado):
        return (estado.fila, estado.columna) in self.bloqueados

    # Verifica si es un estado válido, se usará para generar los sucesores y que el agente no se salga de los límites
    def es_valido(self, estado):
        return 0 <= estado.fila < self.filas and 0 <= estado.columna < self.columnas and not self.es_bloqueado(estado)

    # Verifica si es estado de destino
    def es_destino(self, estado):
        return (estado.fila, estado.columna) in self.destinos or (estado.fila, estado.columna) in self.peligros_fatales

    # Verifica si esa acción es válida
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

    # Método encargado de aplicar la acción, aquí se tiene en cuenta la estocasticidad del entorno
    # Si el valor es superior a la estocasticidad, se aplica el correspondiente método
    def aplicar_accion(self, accion, estado):
        accion_elegida = accion
        estado_actual = estado
        # Genera un valor entre 0 y 1, si es superior al valor de estocasticidad llamamos al susodicho método
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

    # Método encargado de la estocasticidad, se aplica a las perpendiculares, tal como viene definido en los apuntes
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

    # Obtención de las recompensas asociadas a cada estado, obtenidas de las variables en forma de diccionario

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
    direcciones_vector = {
        "UP": (-1, 0),
        "RIGHT": (0, 1),
        "DOWN": (1, 0),
        "LEFT": (0, -1)
    }

    def __init__(self, entorno, alpha, gamma, epsilon, decaimiento_epsilon, json_dir):
        self.entorno = entorno
        self.movimientos = [Agente.direcciones[movimiento] for movimiento in
                            Agente.mov_numericos]  # Arriba, Derecha, Abajo, Izquierda respectivamente
        self.qtabla = np.zeros((entorno.filas, entorno.columnas, len(self.mov_numericos)))
        self.u_tabla = {}
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.decaimiento_epsilon = decaimiento_epsilon
        self.politica = None
        self.json_dir = json_dir
        self.tiempo_ejecucion = None
        self.politica_it = {}

    # El agente sólo desea aplicar una accion en base a un estado, es el entorno el encargado de que esa aplicacion se ejecute
    # así como se obtenga la recompensa
    def realizar_movimiento(self, accion_elegida, estado_actual):
        explorar = np.random.rand() < self.epsilon  # Es el agente quien decide o no explorar
        nuevo_estado, recompensa = self.entorno.mover_agente(accion_elegida, estado_actual, explorar)
        return nuevo_estado, recompensa

    # Se selecciona el máximo valor para un estado en la Q tabla asociada a una accion de las 4 posibles en cada nodo
    def max_q(self, estado):
        posibles_acciones = [self.qtabla[estado.fila][estado.columna][accion] for accion in self.mov_numericos]
        aux = posibles_acciones
        for accion in range(len(aux)):
            if not self.entorno.es_accion_valida(accion, estado):
                # Con esto, descartamos los índices que llevan a acciones no válidas
                # Sin esto el agente se dispersa mucho
                aux[accion] = np.min(self.entorno.recompensas_finales) - 50
        indices_maximos = np.where(aux == np.max(aux))[0]
        accion_elegida = np.random.choice(indices_maximos)  # En caso de tener varios índices iguales
        return accion_elegida

    # Aplicación directa de la fórmula de los apuntes, se encarga de actualizar la Q Tabla
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

    # Ejecución del algoritmo en función del número de episodios
    def ejecutar_algoritmo(self, num_episodios):
        self.tiempo_ejecucion = time()
        for i in range(num_episodios):
            self.episodio()
        self.tiempo_ejecucion = time() - self.tiempo_ejecucion
        return self.obtener_politica()

    # Método encargado de aplicar un episodio, finaliza cuando llega a un estado de meta y actualiza la Q Tabla
    # Aplicación directa del pseucocódigo de los apuntes
    def episodio(self):
        estado_actual = self.entorno.inicio
        destino = False
        while not destino:
            accion_elegida = self.max_q(estado_actual)
            nuevo_estado, recompensa = self.realizar_movimiento(accion_elegida, estado_actual)
            if self.entorno.es_destino(nuevo_estado):
                destino = True
                self.epsilon *= self.decaimiento_epsilon  # Decaimiento de épsilon en cada final de episodio
            self.actualizar_qtabla(estado_actual, accion_elegida, recompensa, nuevo_estado, destino)
            estado_actual = nuevo_estado

    # Con esto obtenemos la política dentro de todos los estados posibles que no sean ni destinos ni bloqueados
    # En función de los valores máximos de la Q Tabla en cada nodo
    def obtener_politica(self):
        politica = {}
        estados_posibles = [(fila, columna) for fila in range(self.entorno.filas) for columna in
                            range(self.entorno.columnas)]
        for estado in estados_posibles:
            if estado not in self.entorno.destinos and estado not in self.entorno.peligros_fatales and estado not in self.entorno.bloqueados:
                politica[estado[0], estado[1]] = self.direcciones.get(self.max_q(Estado(estado[0], estado[1])))
        self.politica = politica
        self.estadisticas()
        return politica

    def estadisticas(self):
        destinos = []
        for estados in self.entorno.destinos.keys():
            destinos.append(estados)

        print("----ALGORITMO QLEARNING----")
        print("\n ")
        print(f"Estado inicial: {self.entorno.inicio}")
        print(f"Personas a rescatar: {destinos}")
        print(f"Tamaño de la ciudad: {self.entorno.filas} x {self.entorno.columnas}")
        print(f"Tiempo de ejecución del Algoritmo: {self.tiempo_ejecucion:.2f} segundos")
        print("\n ")
        print("----QTabla----")
        print("\n ")
        print(self.qtabla)
        print("\n ")
        print("----POLÍTICA OBTENIDA CON QQLEARNING----")
        for estado, accion in self.politica.items():
            print(f"\"({estado[0]}, {estado[1]})\": \"{accion}\"")
        print("----MAPA DE LA POLÍTICA OBTENIDA QQLEARNING----")
        print("\n ")
        draw_policy_map(json_dir, self.politica)

    # ---------------------------------- EJERCICIO PARTE EXTRAORDINARIA ----------------------------------
    def iteracion_de_politicas(self, num_episodios):
        estados_posibles = [(fila, columna) for fila in range(self.entorno.filas) for columna in
                            range(self.entorno.columnas) if (fila, columna) not in self.entorno.bloqueados]
        # Inicializamos la Tabla de Utilidades
        for estado in estados_posibles:
            e = Estado(estado[0], estado[1])
            if self.entorno.es_destino(e):
                d_aux = {estado: self.entorno.obtener_recompensa(e)}
                self.u_tabla.update(d_aux)
            else:
                d_aux = {estado: 0}
                self.u_tabla.update(d_aux)
        # Iniciamos las iteraciones
        for i in range(num_episodios):
            self.evaluacion_de_politica(estados_posibles)

        # print(f"UTabla {self.u_tabla}")
        # Mejoramos la política
        self.mejora_politica()
        # Diseño del Entorno con la política iterada
        draw_policy_map(json_dir, self.politica_it)
        return self.politica_it

    def evaluacion_de_politica(self, estados_posibles):
        # Utilizamos una copia para tener en cuenta el valor previo a la actualización
        u_tabla_aux = self.u_tabla.copy()
        mayor_cambio = 0
        for estado in estados_posibles:
            estado_actual = Estado(estado[0], estado[1])
            if not self.entorno.es_destino(estado_actual):
                # print(f"Estado actual -> {estado_actual}")
                siguiente_estado = self.siguiente_estado(estado)
                recompensa = self.entorno.obtener_recompensa(estado_actual)
                # print(f"Recompensa de dicho estado -> {recompensa}")
                probabilidad_transicionar = self.entorno.estocasticidad
                # print(f"Estado siguiente -> {siguiente_estado}")
                self.u_tabla[estado] = recompensa + self.gamma * np.sum(
                    probabilidad_transicionar * u_tabla_aux[siguiente_estado])
                mayor_cambio = max(mayor_cambio, abs(self.u_tabla[estado] - u_tabla_aux[estado]))
                # print("\n ")

    def mejora_politica(self):
        politica_aux = {}
        max_estado = None
        # Valor de mejora iniciado a menos infinito
        valor = float('-inf')
        estados_posibles = [(fila, columna) for fila in range(self.entorno.filas) for columna in
                            range(self.entorno.columnas)]

        probabilidad_transicionar = self.entorno.estocasticidad
        for estado in estados_posibles:
            if estado not in self.entorno.destinos and estado not in self.entorno.peligros_fatales and estado not in self.entorno.bloqueados:
                # print(f"Estado -> {estado}")
                # Miramos los sucesores de ese estado, es decir, transiciones válidas en el entorno
                sucesores = self.sucesores(estado)
                # print(f"Sucesores -> {sucesores}")
                for nuevo_estado in sucesores:
                    # Calculamos el valor para esa accion que conlleva a un nuevo estado sucesor
                    actual = probabilidad_transicionar * self.u_tabla[nuevo_estado]
                    if actual > valor:
                        # Si hay mejora actualizamos y determinamos el nuevo estado al que transicionar
                        valor = actual
                        max_estado = nuevo_estado
                # print(f"Nuevo estado encontrado -> {max_estado}")
                # Calculamos la diferencia para determinar qué accion ha llevado a ese estado y decodificarla en su string
                accion_v = (max_estado[0] - estado[0], max_estado[1] - estado[1])
                accion = self.decodificar_accion(accion_v)
                # print(f"Accion V {accion_v}")
                # print(f"Accion {accion}")
                # Nos quedamos con esa acción y actualizamos la política
                politica_aux.update({(estado[0], estado[1]): accion})
                # Reseteamos los valores para el siguiente estado
                valor = float('-inf')
                actual = None
        self.politica_it = politica_aux

    def decodificar_accion(self, accion):
        for key, value in self.direcciones_vector.items():
            if value == accion:
                return key

    # Sucesores válidos para un determinado estado
    def sucesores(self, estado):
        movimientos = [(-1, 0), (0, 1), (1, 0), (0, -1)]
        sucesores = []
        for mx, my in movimientos:
            nueva_fila = estado[0] + mx
            nueva_columna = estado[1] + my
            if self.entorno.es_valido(Estado(nueva_fila, nueva_columna)):
                sucesores.append((nueva_fila, nueva_columna))
        return sucesores

    # Cálculo del siguiente estado en la política inicial heredada de Q-Learning
    def siguiente_estado(self, estado):
        # print(f"Estado -> {estado}")
        aux = self.politica.get(estado)
        accion = self.direcciones_vector.get(aux)
        nueva_fila = estado[0] + accion[0]
        nueva_columna = estado[1] + accion[1]
        siguiente_estado = (nueva_fila, nueva_columna)
        # print(f"Siguiente estado -> {siguiente_estado}")
        return siguiente_estado


if __name__ == '__main__':
    # Inicializamos el problema cargando el json y parametrizandolo
    penalizacion_entorno = -0.04
    penalizacion_peligro = -5
    estocasticidad_entorno = 0.8
    numero_episodios = 100
    alpha = 0.2
    gamma = 0.9
    epsilon = 0.2
    decaimiento_epsilon = 0.05

    # Parámetro necesario para dibujar la política
    json_dir = os.path.join(os.getcwd(), './initial-rl-instances/lesson5-rl.json')
    # Definimos el entorno con las variables parametrizadas
    entorno = Entorno('./initial-rl-instances/lesson5-rl.json', penalizacion_entorno, penalizacion_peligro,
                      estocasticidad_entorno)
    # Inicializamos el Algoritmo
    algoritmo = Agente(entorno, alpha, gamma, epsilon, decaimiento_epsilon, json_dir)

    # Ejecutamos el Algoritmo con el nº de episodios y obtenemos la política y la imprimimos
    # Posteriormente la dibujamos
    algoritmo.ejecutar_algoritmo(numero_episodios)
    # Parte correspondiente a la evaluación extraordinaria
    algoritmo.iteracion_de_politicas(numero_episodios)



