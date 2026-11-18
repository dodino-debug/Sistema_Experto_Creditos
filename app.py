
from flask import Flask, render_template, request

app = Flask(__name__)



def convertir_moneda(valor):
    valor = str(valor).strip()

    # Eliminar puntos de miles y espacios
    valor = valor.replace(".", "").replace(" ", "")

    if not valor.isdigit():
        raise ValueError(f"Valor monetario inválido: {valor}")

    return int(valor)

def evaluar_credito(ingresos, gastos, deudas, historial):
    disponible = ingresos - gastos - deudas
    endeudamiento = (deudas / ingresos) * 100

    razones = []

    if disponible < 300000:
        razones.append("Capacidad de pago insuficiente.")

    if endeudamiento > 45:
        razones.append("Nivel de endeudamiento demasiado alto.")

    if historial == "malo":
        razones.append("Historial crediticio desfavorable.")

    if razones:
        estado = "RECHAZADO"

    elif disponible < 600000 or endeudamiento > 30 or historial == "regular":
        estado = "EN REVISIÓN"
        razones.append("La solicitud necesita una revisión adicional.")

    else:
        estado = "APROBADO"
        razones.append("Cumple con las condiciones financieras establecidas.")

    return {
        "estado": estado,
        "razones": razones,
        "disponible": disponible,
        "endeudamiento": round(endeudamiento, 2)
    }



@app.route("/", methods=["GET", "POST"])
def inicio():
    resultado = None
    error = None

    if request.method == "POST":
        try:
            ingresos = convertir_moneda(request.form["ingresos"])
            gastos = convertir_moneda(request.form["gastos"])
            deudas = convertir_moneda(request.form["deudas"])
            historial = request.form["historial"]

            print("Ingresos:", ingresos)
            print("Gastos:", gastos)
            print("Deudas:", deudas)
            print("Historial:", historial)

            if ingresos <= 0 or gastos < 0 or deudas < 0:
                raise ValueError("Los valores financieros no son válidos.")

            if historial not in ("bueno", "regular", "malo"):
                raise ValueError("El historial crediticio no es válido.")

            resultado = evaluar_credito(
                ingresos,
                gastos,
                deudas,
                historial
            )

        except (ValueError, KeyError) as e:
            print("ERROR EN LA EVALUACIÓN:", e)
            error = f"Error al procesar los datos: {e}"

    return render_template(
        "index.html",
        resultado=resultado,
        error=error
    )


if __name__ == "__main__":
    app.run(debug=True)
