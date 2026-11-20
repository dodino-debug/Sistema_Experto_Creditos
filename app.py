from decimal import Decimal, InvalidOperation
from flask import Flask, render_template, request

app = Flask(__name__)

# Valores de DEMOSTRACIÓN: no representan tasas comerciales ni ofertas reales.
PRODUCTOS = {
    "consumo": {"nombre": "Crédito de consumo", "tasa_ea": 0.19, "minimo": 500_000, "maximo": 30_000_000, "plazos": [6, 12, 24, 36, 48]},
    "libre": {"nombre": "Libre inversión", "tasa_ea": 0.22, "minimo": 500_000, "maximo": 50_000_000, "plazos": [6, 12, 24, 36, 48, 60]},
    "micro": {"nombre": "Microcrédito", "tasa_ea": 0.28, "minimo": 500_000, "maximo": 15_000_000, "plazos": [6, 12, 18, 24, 36]},
}


def dinero(valor):
    texto = str(valor).strip()
    if not texto or not texto.replace('.', '').isdigit():
        raise ValueError("Los valores monetarios deben contener solo números y puntos de miles.")
    partes = texto.split('.')
    if len(partes) > 1 and (not 1 <= len(partes[0]) <= 3 or any(len(p) != 3 for p in partes[1:])):
        raise ValueError("Usa un formato válido, por ejemplo 2.500.000.")
    return int(''.join(partes))


def cuota_fija(capital, tasa_mensual, meses):
    if capital <= 0:
        return 0.0
    if tasa_mensual == 0:
        return capital / meses
    factor = (1 + tasa_mensual) ** meses
    return capital * tasa_mensual * factor / (factor - 1)


def evaluar_credito(nombre, ingresos, gastos, deudas, historial, tipo, solicitado, plazo):
    producto = PRODUCTOS[tipo]
    tasa_ea = producto['tasa_ea']
    tasa_mensual = (1 + tasa_ea) ** (1 / 12) - 1
    disponible = ingresos - gastos - deudas
    endeudamiento_actual = 100 * deudas / ingresos
    # Dos límites prudenciales internos de la simulación:
    # 1) no destinar más del 60% del disponible a la nueva cuota
    # 2) deudas actuales + cuota nueva <= 40% del ingreso
    limite_por_disponible = max(0, disponible * 0.60)
    limite_por_ingreso = max(0, ingresos * 0.40 - deudas)
    cuota_maxima = min(limite_por_disponible, limite_por_ingreso)

    factor_cuota = cuota_fija(1, tasa_mensual, plazo)
    capacidad_capital = cuota_maxima / factor_cuota
    tope = min(solicitado, producto['maximo'], capacidad_capital)
    # Redondear hacia abajo a múltiplos de 100.000, sin exceder capacidad
    aprobado_monto = int(tope // 100_000) * 100_000

    criterios = [
        {"nombre": "Historial crediticio bueno", "cumple": historial == 'bueno', "detalle": "Se requiere historial bueno."},
        {"nombre": "Endeudamiento actual máximo del 30%", "cumple": endeudamiento_actual <= 30, "detalle": f"Actual: {endeudamiento_actual:.2f}%."},
        {"nombre": "Capacidad para una nueva cuota", "cumple": cuota_maxima > 0, "detalle": "Se consideran gastos, deudas y un margen de seguridad."},
        {"nombre": "Monto mínimo del producto", "cumple": aprobado_monto >= producto['minimo'], "detalle": f"Mínimo: ${producto['minimo']:,.0f}.".replace(',', '.')},
    ]
    razones = [f"No cumple: {c['nombre'].lower()}." for c in criterios if not c['cumple']]
    aprobado = all(c['cumple'] for c in criterios)
    if not aprobado:
        aprobado_monto = 0
    cuota = cuota_fija(aprobado_monto, tasa_mensual, plazo) if aprobado else 0
    total = cuota * plazo
    if aprobado:
        if aprobado_monto < solicitado:
            razones.append("Se aprobó un monto inferior al solicitado para respetar la capacidad de pago y los límites del producto.")
        else:
            razones.append("El monto solicitado cumple los criterios del simulador.")
    return {
        'estado': 'APROBADO' if aprobado else 'REPROBADO',
        'nombre': nombre,
        'producto': producto['nombre'],
        'solicitado': solicitado,
        'aprobado': aprobado_monto,
        'plazo': plazo,
        'tasa_ea': tasa_ea * 100,
        'tasa_mensual': tasa_mensual * 100,
        'cuota': cuota,
        'total': total,
        'intereses': total - aprobado_monto,
        'disponible': disponible,
        'endeudamiento_actual': endeudamiento_actual,
        'cuota_maxima': cuota_maxima,
        'criterios': criterios,
        'razones': razones,
    }


@app.template_filter('cop')
def formato_pesos(valor):
    return '$' + f'{valor:,.0f}'.replace(',', '.')


@app.route('/', methods=['GET', 'POST'])
def inicio():
    datos = {'nombre': '', 'ingresos': '', 'gastos': '', 'deudas': '', 'historial': 'bueno', 'tipo': 'consumo', 'solicitado': '', 'plazo': '24'}
    resultado, error = None, None
    if request.method == 'POST':
        datos = {clave: request.form.get(clave, '').strip() for clave in datos}
        try:
            nombre = datos['nombre']
            if len(nombre) < 3 or len(nombre) > 100:
                raise ValueError('Ingresa un nombre de 3 a 100 caracteres.')
            ingresos, gastos, deudas = (dinero(datos[c]) for c in ('ingresos', 'gastos', 'deudas'))
            solicitado = dinero(datos['solicitado'])
            if ingresos <= 0 or solicitado <= 0:
                raise ValueError('Los ingresos y el monto solicitado deben ser mayores que cero.')
            if datos['historial'] not in ('bueno', 'regular', 'malo'):
                raise ValueError('Historial crediticio inválido.')
            if datos['tipo'] not in PRODUCTOS:
                raise ValueError('Tipo de crédito inválido.')
            plazo = int(datos['plazo'])
            if plazo not in PRODUCTOS[datos['tipo']]['plazos']:
                raise ValueError('El plazo no está disponible para el tipo de crédito seleccionado.')
            resultado = evaluar_credito(nombre, ingresos, gastos, deudas, datos['historial'], datos['tipo'], solicitado, plazo)
        except (ValueError, KeyError, OverflowError) as exc:
            error = str(exc)
    return render_template('index.html', datos=datos, resultado=resultado, error=error, productos=PRODUCTOS, plazos_por_tipo={k: v['plazos'] for k, v in PRODUCTOS.items()})


if __name__ == '__main__':
    app.run(debug=True)