from django.core.management.base import BaseCommand
from django.db import transaction
from exercises.models import MovementPattern, MuscleGroup, Agonist, Exercise

class Command(BaseCommand):
    help = 'Puebla la base de datos con la taxonomía de ejercicios e información detallada.'

    def handle(self, *args, **kwargs):
        # 1. Definición de la jerarquía anatómica
        TAXONOMY = {
            "Push": {
                "Pecho": ["Pectoral mayor", "Pectoral menor"],
                "Hombros/Deltoides": ["Deltoides anterior", "Deltoides lateral"],
                "Tríceps": ["Tríceps braquial"]
            },
            "Pull": {
                "Espalda": ["Trapecio", "Romboides"],
                "Dorsales": ["Dorsal ancho"],
                "Hombros/Deltoides": ["Deltoides posterior"],
                "Bíceps": ["Bíceps braquial"],
                "Antebrazos": ["Braquial", "Braquiorradial", "Flexores del antebrazo"]
            },
            "Leg": {
                "Cuádriceps": ["Recto femoral", "Vasto lateral", "Vasto medial"],
                "Isquiotibiales": ["Bíceps femoral", "Semitendinoso", "Semimembranoso"],
                "Glúteos": ["Glúteo mayor", "Glúteo medio"],
                "Aductores": ["Aductor mayor"],
                "Pantorrillas": ["Gastrocnemio", "Sóleo"]
            },
            "Core": {
                "Core": ["Recto abdominal", "Oblicuo externo", "Oblicuo interno", "Transverso abdominal"]
            },
            "Cardio": {
                "Cardio": ["Corazón", "Diafragma"]
            }
        }

        # 2. Dataset de ejercicios normalizado
        EXERCISES_DATA = [
            {"name": "Bicicletas Abdominales", "pattern": "Core", "group": "Core", "agonist": "Recto abdominal", "type": "STRENGTH", "tracks_weight": True, "desc": "Ejercicio de flexión y rotación de tronco que enfatiza el recto abdominal y los oblicuos. Recomendación: Mantener la zona lumbar en contacto con el suelo (retroversión pélvica) para evitar compensaciones con el psoas ilíaco. La rotación debe ser torácica, buscando llevar el codo al encuentro de la rodilla opuesta sin traccionar el cuello."},
            {"name": "Burpees", "pattern": "Cardio", "group": "Cardio", "agonist": "Corazón", "type": "FULL_BODY", "tracks_weight": False, "desc": "Movimiento multiarticular de alta demanda metabólica que combina una sentadilla, una flexión de brazos (push-up) y un salto vertical. Recomendación: Priorizar la alineación de la columna durante la fase de plancha para evitar el colapso lumbar. La transición de la fase de decúbito a la bipedestación debe realizarse con una base de pies amplia para proteger las rodillas."},
            {"name": "Caminadora", "pattern": "Cardio", "group": "Cardio", "agonist": "Corazón", "type": "CARDIO", "tracks_weight": False, "desc": "Actividad de desplazamiento cíclico que estimula el sistema oxidativo y la musculatura del tren inferior. Recomendación: Mantener una postura erguida, evitando sujetarse de los pasamanos para no alterar la mecánica natural de la marcha. Ajustar la inclinación puede reducir el impacto articular en las rodillas al modificar el vector de carga."},
            {"name": "Curl Martillo", "pattern": "Pull", "group": "Antebrazos", "agonist": "Braquiorradial", "type": "STRENGTH", "tracks_weight": True, "desc": "Variante de flexión de codo con agarre neutro. El objetivo principal es el braquiorradial y el braquial anterior, además del bíceps braquial. Recomendación: Mantener los codos pegados al torso y evitar el balanceo del cuerpo (cheating). La fase excéntrica debe ser controlada para maximizar el tiempo bajo tensión en el antebrazo."},
            {"name": "Curl de Bíceps (Barra)", "pattern": "Pull", "group": "Bíceps", "agonist": "Bíceps braquial", "type": "STRENGTH", "tracks_weight": True, "desc": "Ejercicio de flexión de codo en supinación. Permite manejar cargas elevadas debido a la estabilidad de la barra. Recomendación: Evitar la hiperextensión lumbar al levantar el peso. El rango de movimiento debe ser completo, extendiendo casi totalmente el codo en la fase inferior sin perder la tensión muscular."},
            {"name": "Curl de Bíceps (Mancuerna)", "pattern": "Pull", "group": "Bíceps", "agonist": "Bíceps braquial", "type": "STRENGTH", "tracks_weight": True, "desc": "Flexión de codo que permite una mayor libertad de rotación (supinación durante el ascenso). Recomendación: Puede realizarse de forma bilateral o unilateral para corregir asimetrías. Es vital evitar el movimiento del hombro (flexión anterior) para no involucrar el deltoides anterior en el movimiento."},
            {"name": "Curl de Pierna (Leg Curl)", "pattern": "Leg", "group": "Isquiotibiales", "agonist": "Bíceps femoral", "type": "STRENGTH", "tracks_weight": True, "desc": "Ejercicio de aislamiento para los isquiotibiales (bíceps femoral, semitendinoso y semimembranoso). Recomendación: En máquina sentada o acostada, asegurar que el eje de rotación de la máquina coincida con la articulación de la rodilla. Evitar despegar la pelvis del banco para no involucrar la zona lumbar."},
            {"name": "Dominadas / Pull up", "pattern": "Pull", "group": "Dorsales", "agonist": "Dorsal ancho", "type": "STRENGTH", "tracks_weight": True, "desc": "Ejercicio poliarticular de tracción vertical. Involucra principalmente el dorsal ancho, trapecio inferior y bíceps. Recomendación: Iniciar el movimiento con una depresión escapular (bajar los hombros) antes de flexionar los brazos. El pecho debe dirigirse hacia la barra para asegurar una activación óptima de la espalda."},
            {"name": "Dominadas / Pull up (asistidas)", "pattern": "Pull", "group": "Dorsales", "agonist": "Dorsal ancho", "type": "STRENGTH", "tracks_weight": True, "desc": "Variante mecánica para usuarios que no poseen la fuerza relativa para mover su peso corporal. Recomendación: Utilizar la plataforma o banda elástica para mantener un tempo controlado, enfocándose en la retracción escapular en la parte superior del movimiento."},
            {"name": "Elevaciones Laterales (Mancuernas)", "pattern": "Push", "group": "Hombros/Deltoides", "agonist": "Deltoides lateral", "type": "STRENGTH", "tracks_weight": True, "desc": "Ejercicio de aislamiento para el deltoides lateral mediante la abducción del hombro. Recomendación: Realizar el movimiento en el 'plano escapular' (unos 30° hacia adelante) para evitar el pinzamiento subacromial. No es necesario elevar las mancuernas por encima de la línea del hombro."},
            {"name": "Elevación de Pantorrilla Sentado", "pattern": "Leg", "group": "Pantorrillas", "agonist": "Sóleo", "type": "STRENGTH", "tracks_weight": True, "desc": "Ejercicio que enfatiza el músculo sóleo, ya que la flexión de rodilla acorta el gastrocnemio. Recomendación: Realizar una pausa en la máxima extensión (fase de estiramiento) para disipar la energía elástica del tendón de Aquiles y obligar al músculo a trabajar."},
            {"name": "Elevación de pantorrilla de píe", "pattern": "Leg", "group": "Pantorrillas", "agonist": "Gastrocnemio", "type": "STRENGTH", "tracks_weight": True, "desc": "Trabaja el complejo gastrocnemio-sóleo. Recomendación: Mantener las rodillas con una microflexión (no bloqueadas) y buscar el máximo rango de movimiento tanto en la flexión plantar como en la dorsiflexión."},
            {"name": "Extensión de Tríceps (Copa)", "pattern": "Push", "group": "Tríceps", "agonist": "Tríceps braquial", "type": "STRENGTH", "tracks_weight": True, "desc": "Extensión de codo por encima de la cabeza, lo que pone a la cabeza larga del tríceps en estiramiento previo. Recomendación: Mantener los codos lo más cerca posible de las orejas y evitar la apertura excesiva de los mismos para proteger la articulación del codo."},
            {"name": "Extensión de Tríceps (Polea)", "pattern": "Push", "group": "Tríceps", "agonist": "Tríceps braquial", "type": "STRENGTH", "tracks_weight": True, "desc": "Aislamiento del tríceps braquial mediante extensión de codo hacia abajo. Recomendación: Mantener el húmero estático al costado del cuerpo. El uso de cuerda permite un mayor rango de movimiento al final de la fase concéntrica (pronación)."},
            {"name": "Extensor de piernas", "pattern": "Leg", "group": "Cuádriceps", "agonist": "Recto femoral", "type": "STRENGTH", "tracks_weight": True, "desc": "Aislamiento del cuádriceps mediante extensión de rodilla. Recomendación: Ajustar el rodillo justo por encima del empeine. Evitar el bloqueo brusco de la rodilla en la parte superior y controlar el descenso para proteger el ligamento cruzado anterior."},
            {"name": "Face Pulls", "pattern": "Pull", "group": "Hombros/Deltoides", "agonist": "Deltoides posterior", "type": "STRENGTH", "tracks_weight": True, "desc": "Ejercicio para el deltoides posterior, manguito rotador y trapecio medio/superior. Recomendación: Tirar de la cuerda hacia la frente o rostro mientras se separan los extremos, buscando una rotación externa del hombro. Es clave para la salud postural."},
            {"name": "Flexiones (Push-ups)", "pattern": "Push", "group": "Pecho", "agonist": "Pectoral mayor", "type": "STRENGTH", "tracks_weight": True, "desc": "Empuje horizontal de peso corporal. Involucra pectoral mayor, deltoides anterior y tríceps. Recomendación: Mantener el core activado (plancha sólida) y los codos en un ángulo de 45° respecto al torso para optimizar la fuerza y proteger los hombros."},
            {"name": "Fondos (Dips)", "pattern": "Push", "group": "Pecho", "agonist": "Pectoral mayor", "type": "STRENGTH", "tracks_weight": True, "desc": "Ejercicio poliarticular para pectoral inferior y tríceps. Recomendación: Una inclinación del torso hacia adelante prioriza el pecho, mientras que una posición vertical prioriza el tríceps. Evitar bajar más allá de los 90° de flexión de codo si existe molestia en el hombro."},
            {"name": "Fondos asistidos", "pattern": "Push", "group": "Pecho", "agonist": "Pectoral mayor", "type": "STRENGTH", "tracks_weight": True, "desc": "Regresión técnica de los fondos mediante máquina o banda. Recomendación: Mantener los hombros alejados de las orejas (depresión escapular) durante todo el rango de movimiento para evitar tensiones innecesarias en el trapecio superior."},
            {"name": "Hip Thrust", "pattern": "Leg", "group": "Glúteos", "agonist": "Glúteo mayor", "type": "STRENGTH", "tracks_weight": True, "desc": "Empuje de cadera diseñado para la activación máxima del glúteo mayor. Recomendación: Mantener la barbilla pegada al pecho y las tibias perpendiculares al suelo en la parte superior. Realizar un bloqueo de cadera (retroversión pélvica) sin arquear la zona lumbar."},
            {"name": "Hollow Body Hold", "pattern": "Core", "group": "Core", "agonist": "Recto abdominal", "type": "STRENGTH", "tracks_weight": False, "desc": "Ejercicio isométrico de estabilización anterior. Recomendación: Presionar la zona lumbar contra el suelo de forma constante. Los brazos y piernas deben estar extendidos pero la altura de los mismos dependerá de la capacidad de mantener la espalda plana."},
            {"name": "Jalón al Pecho", "pattern": "Pull", "group": "Dorsales", "agonist": "Dorsal ancho", "type": "STRENGTH", "tracks_weight": True, "desc": "Tracción vertical en máquina. Alternativa a la dominada. Recomendación: No llevar la barra detrás de la nuca (riesgo articular). El movimiento debe terminar con la barra cerca de la parte superior del esternón, retrayendo activamente las escápulas."},
            {"name": "Leg Raise acostado", "pattern": "Core", "group": "Core", "agonist": "Recto abdominal", "type": "STRENGTH", "tracks_weight": True, "desc": "Elevación de piernas para trabajar el recto abdominal inferior y flexores de cadera. Recomendación: El descenso de las piernas debe detenerse antes de que la zona lumbar se despegue del suelo. Mantener las piernas extendidas aumenta el brazo de palanca y la dificultad."},
            {"name": "Leg Raise en Barra", "pattern": "Core", "group": "Core", "agonist": "Recto abdominal", "type": "STRENGTH", "tracks_weight": True, "desc": "Elevación de piernas suspendido. Recomendación: Evitar el balanceo (inercia). El movimiento debe ser controlado, buscando llevar los pies hacia la barra o las rodillas al pecho mediante la flexión de la pelvis sobre el tronco."},
            {"name": "Peck Fly (Aperturas)", "pattern": "Push", "group": "Pecho", "agonist": "Pectoral mayor", "type": "STRENGTH", "tracks_weight": True, "desc": "Aislamiento del pectoral mediante aducción horizontal. Recomendación: Mantener una ligera flexión en los codos para reducir la tensión en el tendón del bíceps. El enfoque debe estar en 'juntar los bíceps' en el centro del pecho."},
            {"name": "Peso Muerto (Convencional)", "pattern": "Leg", "group": "Isquiotibiales", "agonist": "Bíceps femoral", "type": "FULL_BODY", "tracks_weight": True, "desc": "Movimiento de tracción desde el suelo que involucra cadena posterior y erector espinal. Recomendación: La barra debe viajar pegada a las tibias. Mantener una columna neutra es innegociable. La fuerza debe nacer del empuje de las piernas contra el suelo, no de 'tirar' con la espalda alta."},
            {"name": "Peso Muerto Rumano", "pattern": "Leg", "group": "Isquiotibiales", "agonist": "Semitendinoso", "type": "STRENGTH", "tracks_weight": True, "desc": "Variante que enfatiza isquiotibiales y glúteos mediante la bisagra de cadera. Recomendación: Bajar la carga solo hasta donde la flexibilidad de los isquiotibiales permita sin redondear la espalda. Las rodillas permanecen semiflexionadas y fijas."},
            {"name": "Plancha Abdominal (Plank)", "pattern": "Core", "group": "Core", "agonist": "Transverso abdominal", "type": "STRENGTH", "tracks_weight": True, "desc": "Estabilización isométrica del raquis. Recomendación: Evitar que la cadera caiga. Mantener una línea recta desde los talones hasta la cabeza. La activación del glúteo ayuda a estabilizar la pelvis en posición neutra."},
            {"name": "Prensa de pierna 45°", "pattern": "Leg", "group": "Cuádriceps", "agonist": "Vasto lateral", "type": "STRENGTH", "tracks_weight": True, "desc": "Empuje de cadena cerrada para cuádriceps y glúteos. Recomendación: No bloquear las rodillas en la extensión máxima. Evitar que la pelvis se levante del respaldo en la fase profunda (flexión excesiva), ya que esto genera una tensión peligrosa en los discos lumbares."},
            {"name": "Press Militar (Barra)", "pattern": "Push", "group": "Hombros/Deltoides", "agonist": "Deltoides anterior", "type": "STRENGTH", "tracks_weight": True, "desc": "Empuje vertical de hombros en bipedestación. Recomendación: Realizar una contracción fuerte de glúteos y core para estabilizar la columna. La barra debe pasar cerca de la cara y terminar bloqueada sobre el centro de gravedad (cabeza)."},
            {"name": "Press Militar (Mancuernas)", "pattern": "Push", "group": "Hombros/Deltoides", "agonist": "Deltoides anterior", "type": "STRENGTH", "tracks_weight": True, "desc": "Variante que permite un rango de movimiento más natural y trabajo unilateral. Recomendación: Las mancuernas no deben chocar arriba. Mantener los antebrazos verticales respecto al suelo durante todo el recorrido para optimizar la transferencia de fuerza."},
            {"name": "Press de Banca Inclinado (Barra)", "pattern": "Push", "group": "Pecho", "agonist": "Pectoral mayor", "type": "STRENGTH", "tracks_weight": True, "desc": "Empuje horizontal con inclinación (30-45°) para enfatizar el haz clavicular del pectoral. Recomendación: Evitar ángulos demasiado pronunciados que trasladen toda la carga al deltoides anterior. Mantener los pies firmes en el suelo (leg drive)."},
            {"name": "Press de Banca Inclinado (Mancuernas)", "pattern": "Push", "group": "Pecho", "agonist": "Pectoral mayor", "type": "STRENGTH", "tracks_weight": True, "desc": "Variante con mancuernas del empuje inclinado. Recomendación: Permite un mayor rango de movimiento y convergencia en la parte superior. Controlar la fase excéntrica para no sobreestirar la articulación del hombro."},
            {"name": "Press de Banca Plano (Barra)", "pattern": "Push", "group": "Pecho", "agonist": "Pectoral mayor", "type": "STRENGTH", "tracks_weight": True, "desc": "Ejercicio básico para pectoral mayor, deltoides anterior y tríceps. Recomendación: Mantener una retracción escapular (hombros hacia atrás y abajo) para crear una base estable y proteger el manguito rotador. La barra debe tocar suavemente el esternón antes de subir."},
            {"name": "Press de Banca Plano (Mancuernas)", "pattern": "Push", "group": "Pecho", "agonist": "Pectoral mayor", "type": "STRENGTH", "tracks_weight": True, "desc": "Empuje horizontal que otorga mayor libertad articular. Recomendación: Mantener los antebrazos completamente verticales en todo momento. Presionar las mancuernas hacia arriba y ligeramente hacia adentro."},
            {"name": "Pull Over (Polea)", "pattern": "Pull", "group": "Dorsales", "agonist": "Dorsal ancho", "type": "STRENGTH", "tracks_weight": True, "desc": "Movimiento de extensión de hombro con tensión continua. Recomendación: Mantener los codos fijos y ligeramente flexionados. Centrarse en llevar la barra hacia los muslos usando solo la contracción del dorsal."},
            {"name": "Pull over (Mancuerna)", "pattern": "Pull", "group": "Dorsales", "agonist": "Dorsal ancho", "type": "STRENGTH", "tracks_weight": True, "desc": "Extensión de hombro en banco plano. Involucra dorsal y secundariamente pectoral. Recomendación: Bajar la mancuerna de forma controlada por detrás de la cabeza sin perder la curvatura natural de la columna lumbar."},
            {"name": "Remo con marcuerna", "pattern": "Pull", "group": "Dorsales", "agonist": "Dorsal ancho", "type": "STRENGTH", "tracks_weight": True, "desc": "Tracción unilateral con apoyo en banco. Recomendación: El movimiento debe iniciar con la retracción escapular. El codo debe viajar hacia la cadera en un movimiento pendular, no verticalmente hacia el techo."},
            {"name": "Remo inclinado (Mancuernas)", "pattern": "Pull", "group": "Espalda", "agonist": "Romboides", "type": "STRENGTH", "tracks_weight": True, "desc": "Tracción horizontal bilateral libre. Recomendación: Mantener el torso a unos 45° con la espalda neutra. Las mancuernas deben traccionarse hacia la zona del ombligo, apretando las escápulas en la contracción final."},
            {"name": "Remo inclinado T", "pattern": "Pull", "group": "Espalda", "agonist": "Romboides", "type": "STRENGTH", "tracks_weight": True, "desc": "Tracción con barra anclada (Landmine) o máquina específica. Recomendación: La posición del torso es crítica; evitar el uso de inercia lumbar (balanceo vertical) para levantar el peso."},
            {"name": "Remo invertido", "pattern": "Pull", "group": "Espalda", "agonist": "Trapecio", "type": "STRENGTH", "tracks_weight": True, "desc": "Tracción horizontal usando el peso corporal en una barra fija. Recomendación: Mantener el cuerpo rígido como una tabla desde los talones hasta la cabeza. A mayor horizontalidad del cuerpo, mayor es la dificultad biomecánica."},
            {"name": "Remo renegado (Mancuernas)", "pattern": "Pull", "group": "Dorsales", "agonist": "Dorsal ancho", "type": "STRENGTH", "tracks_weight": True, "desc": "Plancha alta combinada con remos unilaterales. Recomendación: El objetivo no es solo la tracción, sino evitar la rotación compensatoria de la cadera, requiriendo estabilidad antirotacional del core extrema."},
            {"name": "Remo sentado", "pattern": "Pull", "group": "Espalda", "agonist": "Trapecio", "type": "STRENGTH", "tracks_weight": True, "desc": "Tracción horizontal en máquina de polea baja. Recomendación: Mantener una ligera flexión de rodillas y el torso perpendicular al suelo. Evitar inclinarse hacia atrás excesivamente durante la fase de tracción."},
            {"name": "Remo sentado (Agarre con barra)", "pattern": "Pull", "group": "Espalda", "agonist": "Trapecio", "type": "STRENGTH", "tracks_weight": True, "desc": "Variante de remo sentado utilizando una barra recta para un agarre más amplio (pronado o supinado). Recomendación: Enfocarse en la aducción escapular. Un agarre más ancho incide más en la espalda alta (romboides y trapecio medio)."},
            {"name": "Sentadillas", "pattern": "Leg", "group": "Cuádriceps", "agonist": "Recto femoral", "type": "STRENGTH", "tracks_weight": True, "desc": "Ejercicio poliarticular rey para el tren inferior ejecutado con peso corporal. Recomendación: La profundidad debe ser la máxima que permita mantener la neutralidad de la columna. El peso debe distribuirse en el centro del pie."},
            {"name": "Sentadillas con barra", "pattern": "Leg", "group": "Cuádriceps", "agonist": "Recto femoral", "type": "STRENGTH", "tracks_weight": True, "desc": "Sentadilla con carga axial (barra libre). Recomendación: Romper el paralelo (cadera bajo la línea de la rodilla) optimiza la activación de glúteos y cuádriceps, siempre que la movilidad del tobillo y cadera lo permitan sin generar 'butt wink' (retroversión lumbar)."},
            {"name": "Sumo Squat (Mancuerna)", "pattern": "Leg", "group": "Aductores", "agonist": "Aductor mayor", "type": "STRENGTH", "tracks_weight": True, "desc": "Sentadilla con base de sustentación amplia y rotación externa de cadera. Recomendación: Mantener el torso lo más vertical posible y asegurar que las rodillas sigan la dirección de la punta de los pies para proteger la articulación femoropatelar."},
            {"name": "Superman", "pattern": "Core", "group": "Core", "agonist": "Transverso abdominal", "type": "STRENGTH", "tracks_weight": False, "desc": "Extensión lumbar y de cadera simultánea en decúbito prono. Recomendación: Fortalece los erectores espinales. Realizar movimientos lentos y controlados, realizando una pausa isométrica en la contracción y evitando hiperextensiones bruscas del raquis cervical."},
            {"name": "Zancadas (Lunges)", "pattern": "Leg", "group": "Cuádriceps", "agonist": "Vasto medial", "type": "STRENGTH", "tracks_weight": True, "desc": "Trabajo unilateral de dominancia de rodilla y cadera. Recomendación: Dar un paso longitudinal suficiente para que ambas rodillas formen ángulos cercanos a 90° en la máxima flexión. Mantener el core contraído para evitar la inestabilidad pélvica en el plano frontal."},
            {"name": "Curl Bayesian unilateral (polea)", "pattern": "Pull", "group": "Bíceps", "agonist": "Bíceps braquial", "type": "STRENGTH", "tracks_weight": True, "desc": "Curl de bíceps en polea dando la espalda a la torre. Recomendación: Al iniciar el movimiento con el hombro en extensión, se maximiza el torque y el estiramiento de la cabeza larga del bíceps. Controlar de manera estricta la fase excéntrica del movimiento."}
        ]

        with transaction.atomic():
            # 3. Poblar Taxonomía Base
            self.stdout.write("Insertando Taxonomía de Movimiento...")
            
            for pat_name, groups_dict in TAXONOMY.items():
                pattern_obj, _ = MovementPattern.objects.get_or_create(name=pat_name)
                
                for grp_name, agonists_list in groups_dict.items():
                    group_obj, _ = MuscleGroup.objects.get_or_create(
                        pattern=pattern_obj,
                        name=grp_name
                    )
                    
                    for ago_name in agonists_list:
                        Agonist.objects.get_or_create(
                            muscle_group=group_obj,
                            name=ago_name
                        )

            # 4. Poblar Ejercicios
            self.stdout.write("Insertando Ejercicios...")
            
            for ex in EXERCISES_DATA:
                try:
                    # Recuperar el agonista a través de la cadena jerárquica para evitar colisiones de nombres idénticos en distintos grupos
                    agonist_obj = Agonist.objects.get(
                        name=ex["agonist"],
                        muscle_group__name=ex["group"],
                        muscle_group__pattern__name=ex["pattern"]
                    )
                    
                    # Update or Create para idempotencia
                    Exercise.objects.update_or_create(
                        name=ex["name"],
                        defaults={
                            "description": ex["desc"],
                            "agonist": agonist_obj,
                            "exercise_type": ex["type"],
                            "tracks_weight": ex["tracks_weight"],
                            "is_active": True
                        }
                    )
                except Agonist.DoesNotExist:
                    self.stderr.write(f"Error: No se encontró la ruta jerárquica para el agonista {ex['agonist']} en el ejercicio {ex['name']}")
                except Exception as e:
                    self.stderr.write(f"Error procesando {ex['name']}: {str(e)}")

        self.stdout.write(self.style.SUCCESS('¡Poblamiento de la base de datos completado con éxito!'))