Estrategia del Jugador Autónomo para HEX

El jugador autónomo implementado en SmartPlayer utiliza como método principal de decisión el algoritmo Monte Carlo Tree Search (MCTS), combinado con la extensión RAVE (Rapid Action Value Estimation) para acelerar la convergencia del árbol de búsqueda. A continuación se describe cada componente de la estrategia y cómo interactúan entre sí.


Representación del tablero y adyacencias

El tablero se modela como una matriz de NxN donde cada celda puede estar vacía (0), ocupada por el jugador 1 o por el jugador 2. Las adyacencias entre celdas se calculan siguiendo el sistema even-r layout, donde las filas pares están desplazadas a la derecha. Cada celda hexagonal tiene hasta 6 vecinos, y las direcciones válidas dependen de si la fila es par o impar. Al inicio de cada turno se precomputa un diccionario de vecinos para todas las celdas del tablero, evitando recalcularlos durante las simulaciones.


Decisiones inmediatas antes de MCTS

Antes de ejecutar el bucle principal de MCTS, el jugador realiza cuatro verificaciones rápidas que permiten ahorrar tiempo de cómputo:

Si el tablero está completamente vacío, se juega en el centro (N//2, N//2), ya que esta es la posición con mayor conectividad y control estratégico sobre el tablero.

Si solo queda una casilla vacía, se juega directamente en ella.

Se comprueba si existe alguna jugada que permita ganar de inmediato. Si se encuentra, se retorna esa jugada sin necesidad de simulaciones.

Se comprueba si el oponente tiene alguna jugada ganadora inmediata. Si la tiene, se bloquea jugando en esa posición. Esta verificación defensiva es fundamental para no perder partidas por omisión de amenazas obvias.


Monte Carlo Tree Search con RAVE

El núcleo de la estrategia es MCTS, un algoritmo que construye un árbol de búsqueda de forma incremental mediante cuatro fases repetidas dentro de un límite de tiempo de 2 segundos por turno.

Selección: Desde la raíz del árbol se desciende eligiendo en cada nodo el hijo más prometedor según una fórmula que combina UCT (Upper Confidence Bound for Trees) con valores RAVE. La fórmula UCT balancea explotación (tasa de victorias del nodo) con exploración (bonus proporcional al logaritmo de las visitas del padre dividido entre las visitas del hijo), usando un factor de exploración de 0.7. RAVE aporta información adicional: registra qué tan buena fue una jugada en cualquier posición de la simulación, no solo cuando fue jugada directamente. La combinación de ambas señales usa un parámetro beta que decrece a medida que el nodo acumula más visitas directas, dando más peso a la información UCT que es más precisa con suficientes datos, y más peso a RAVE cuando los datos directos son escasos. La constante RAVE utilizada es 300.

Cuando un movimiento ha aparecido muchas veces en simulaciones (amaf_visits alto) pero el nodo tiene pocas visitas propias, beta se acerca a 1 y se confía más en la estadística “global” RAVE. Conforme el nodo acumula visitas, beta se reduce y predomina la estimación UCT local. Esto acelera la convergencia inicial sin perder precisión cuando hay datos suficientes.

Expansión: Cuando se llega a un nodo con movimientos sin explorar, se elige uno al azar, se ejecuta en una copia del tablero y se crea un nuevo nodo hijo en el árbol.

Simulación: Desde el estado del nodo expandido se juega una partida completa hasta el final con movimientos aleatorios para ambos jugadores. Para determinar el ganador de forma eficiente se utiliza una estructura Union-Find (descrita más adelante), evitando la necesidad de ejecutar DFS al final de cada simulación.

Retropropagación: El resultado de la simulación se propaga hacia arriba por todos los nodos del camino recorrido, actualizando las estadísticas de visitas y victorias. Además se actualizan las estadísticas AMAF (All Moves As First): para cada nodo en el camino, se examinan todos los movimientos realizados durante la simulación por el jugador que le toca mover en ese nodo, y se registra si condujeron a victoria. Esto permite que movimientos que aparecen frecuentemente en simulaciones ganadoras sean explorados más rápido en iteraciones futuras.

Al finalizar el tiempo, se selecciona como jugada final el hijo de la raíz con mayor número de visitas, que es una estimación más robusta que elegir por tasa de victorias.


Simulaciones rápidas con Union-Find

Las simulaciones aleatorias (rollouts) necesitan determinar el ganador de una partida completa. Usar DFS en cada simulación sería costoso, así que se emplea una estructura de datos Union-Find con compresión de camino y unión por rango. Se crean dos instancias: una para el jugador 1 que rastrea la conexión entre los bordes izquierdo y derecho, y otra para el jugador 2 que rastrea la conexión entre los bordes superior e inferior. Se utilizan nodos virtuales (TOP, BOTTOM, LEFT, RIGHT) que representan los bordes del tablero. Cada vez que se coloca una ficha durante la simulación, se une su celda con las celdas vecinas del mismo jugador y, si corresponde, con el nodo virtual del borde. Al finalizar la simulación, basta verificar si LEFT y RIGHT están conectados (gana jugador 1) o si TOP y BOTTOM están conectados (gana jugador 2). La operación find con compresión de camino opera en tiempo casi constante, lo que permite ejecutar miles de simulaciones por turno.

 Detalle de implementación de _UF:
 - Cada celda (r, c) se mapea a un índice lineal r*size + c. Se añaden 4 índices extra para los bordes virtuales.
 - union(a, b) usa unión por rango; find(x) hace compresión de caminos. Ambos mantienen costo amortizado casi O(1).
 - connected(a, b) permite resolver la victoria con una sola consulta al final del rollout.
 - Esta estructura se recrea por simulación (dos instancias: jugador 1 y jugador 2) y evita re-correr el tablero completo al finalizar.


Evaluación heurística por camino más corto

El código incluye una función de evaluación basada en el algoritmo de Dijkstra que calcula el camino más corto para cada jugador entre sus dos bordes objetivo. Las celdas propias tienen costo 0, las vacías costo 1 y las del oponente costo 100 (un valor alto que hace prácticamente prohibitivo atravesarlas). La diferencia entre la distancia del oponente y la propia da una medida de ventaja posicional. Aunque esta heurística no se usa directamente en la versión final del bucle MCTS (que se basa puramente en simulaciones aleatorias con RAVE), está disponible como herramienta de evaluación y podría integrarse para guiar las simulaciones o como criterio de desempate.


Optimizaciones de rendimiento

Se utilizan __slots__ en las clases _UF y _MCTSNode para reducir el consumo de memoria y acelerar el acceso a atributos, lo cual es relevante dado que se crean miles de nodos durante la búsqueda.

El diccionario de vecinos se precomputa una sola vez al inicio de cada turno.

Las simulaciones con Union-Find copian el tablero como listas de Python puras (sin usar clone de HexBoard) para minimizar la sobrecarga.

Las estadísticas AMAF se almacenan en diccionarios directamente en cada nodo, evitando búsquedas adicionales en estructuras separadas.


La estrategia combina la solidez teórica de MCTS, que converge a la jugada óptima con suficiente tiempo, con la aceleración práctica de RAVE, que permite aprovechar información de simulaciones de manera transversal. Las verificaciones de victoria y bloqueo inmediato garantizan que no se pierdan oportunidades tácticas obvias. La estructura Union-Find permite realizar simulaciones extremadamente rápidas, maximizando el número de iteraciones dentro del límite de tiempo. El resultado es un jugador que equilibra exploración estratégica con eficiencia computacional para tomar decisiones competitivas en tableros de distintos tamaños.
