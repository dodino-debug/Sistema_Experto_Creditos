
from flask import Flask, render_template, request
import re

app = Flask(__name__)


# CONVERSIÓN DE VALORES MONETARIOS
def convertir_moneda(valor):
    """
    Convierte '2.500.000' en 2500000.
    Solo acepta pesos enteros no negativos.
    """
    valor = str(valor).strip()

    if not re.fullmatch(r"\d{1,3}(?:\.\d{3})*|\d+", valor):
        raise ValueError(
            "Ingresa cantidades válidas, por ejemplo: 2.500.000"
        )

    return int(valor.replace(".", ""))


# MOTOR DE REGLAS DEL SISTEMA EXPERTO
def evaluar_credito(ingresos, gastos, deudas, historial):

    disponible = ingresos - gastos - deudas
    endeudamiento = (deudas / ingresos) * 100

    razones = []
    criterios = []

    # REGLA 1: CAPACIDAD DE PAGO
    cumple_capacidad = disponible >= 600000

    criterios.append({
        "nombre": "Capacidad de pago",
        "cumple": cumple_capacidad,
        "detalle": "Mínimo requerido: $600.000"
    })

    if not cumple_capacidad:
        razones.append(
            "La capacidad de pago es inferior "
            "al mínimo requerido de $600.000."
        )

    # REGLA 2: ENDEUDAMIENTO
    cumple_endeudamiento = endeudamiento <= 30

    criterios.append({
        "nombre": "Nivel de endeudamiento",
        "cumple": cumple_endeudamiento,
        "detalle": "Máximo permitido: 30%"
    })

    if not cumple_endeudamiento:
        razones.append(
            "El nivel de endeudamiento supera "
            "el límite permitido del 30%."
        )

    # REGLA 3: HISTORIAL CREDITICIO
    cumple_historial = historial == "bueno"

    criterios.append({
        "nombre": "Historial crediticio",
        "cumple": cumple_historial,
        "detalle": "Se requiere historial bueno"
    })

    if not cumple_historial:
        razones.append(
            "El historial crediticio debe ser bueno. "
            "Los historiales regulares o malos no cumplen."
        )

    # DECISIÓN FINAL
    aprobado = (
        cumple_capacidad
        and cumple_endeudamiento
        and cumple_historial
    )

    if aprobado:
        estado = "APROBADO"
        razones.append(
            "El solicitante cumple con todos los "
            "criterios financieros establecidos."
        )
    else:
        estado = "REPROBADO"

    return {
        "estado": estado,
        "razones": razones,
        "criterios": criterios,
        "disponible": disponible,
        "endeudamiento": round(endeudamiento, 2)
    }


# RUTA PRINCIPAL
@app.route("/", methods=["GET", "POST"])
def inicio():

    resultado = None
    error = None

    datos = {
        "ingresos": "",
        "gastos": "",
        "deudas": "",
        "historial": "bueno"
    }

    if request.method == "POST":

        datos = {
            "ingresos": request.form.get("ingresos", ""),
            "gastos": request.form.get("gastos", ""),
            "deudas": request.form.get("deudas", ""),
            "historial": request.form.get("historial", "")
        }

        try:
            ingresos = convertir_moneda(datos["ingresos"])
            gastos = convertir_moneda(datos["gastos"])
            deudas = convertir_moneda(datos["deudas"])
            historial = datos["historial"]

            if ingresos <= 0:
                raise ValueError(
                    "Los ingresos deben ser mayores que cero."
                )

            if historial not in ("bueno", "regular", "malo"):
                raise ValueError(
                    "Selecciona un historial crediticio válido."
                )

            resultado = evaluar_credito(
                ingresos,
                gastos,
                deudas,
                historial
            )

        except ValueError as e:
            error = str(e)

    return render_template(
        "index.html",
        resultado=resultado,
        error=error,
        datos=datos
    )


if __name__ == "__main__":
    app.run(debug=True)
