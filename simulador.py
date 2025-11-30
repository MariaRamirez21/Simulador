import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import numpy as np

# --- Fórmulas/Correlaciones para el Número de Sherwood (Sh) ---
# Se usan los operadores de potencia (**) CORRECTAMENTE.

def calcular_sherwood(geometria, Re, Sc, usar_DAB=False):
    """
    Calcula un valor representativo de Sherwood (Sh)
    usando correlaciones simplificadas.
    """
    if not usar_DAB:
        return 0.0

    # Correlaciones simplificadas (ejemplos):
    if geometria == 'placa':
        # Analogía con placa plana (turbulento): Sh = 0.037 * Re^0.8 * Sc^(1/3)
        Sh = 0.037 * (Re**0.8) * (Sc**(1/3))
    elif geometria == 'tubo':
        # Analogía con flujo en tubo (turbulento): Sh = 0.023 * Re^0.8 * Sc^(1/3)
        Sh = 0.023 * (Re**0.8) * (Sc**(1/3))
    elif geometria == 'esfera':
        # Correlación de Frössling/Ranz-Marshall: Sh = 2 + 0.6 * Re^0.5 * Sc^0.33
        Sh = 2.0 + 0.6 * (Re**0.5) * (Sc**(1/3))
    elif geometria == 'gota':
        # Similar a la esfera
        Sh = 2.0 + 0.6 * (Re**0.5) * (Sc**(1/3))
    elif geometria == 'lecho empacado':
        # Correlación simplificada: Sh ~ Re^0.6 * Sc^(1/3)
        Sh = 1.15 * (Re**0.6) * (Sc**(1/3))
    else:
        Sh = 0.0

    return Sh

# --- Inicialización de la Aplicación Dash ---
app = dash.Dash(__name__)

# --- Definición de Componentes de la Interfaz ---
# Opciones para el menú desplegable de geometría
opciones_geometria = [
    {'label': 'Placa Plana', 'value': 'placa'},
    {'label': 'Tubo', 'value': 'tubo'},
    {'label': 'Esfera', 'value': 'esfera'},
    {'label': 'Gota', 'value': 'gota'},
    {'label': 'Lecho Empacado', 'value': 'lecho empacado'},
]

# Diseño de la aplicación
app.layout = html.Div(style={'padding': '20px'}, children=[
    html.H1("⚙ Simulador Interactivo de Transferencia de Masa"),
    html.Hr(),

    # --- Controles (Input) ---
    html.Div(style={'display': 'flex', 'flex-direction': 'row', 'gap': '30px'}, children=[

        # Columna de controles
        html.Div(style={'width': '300px'}, children=[
            html.H3("Controles"),

            # 1. Menú Geometría
            html.Label("Geometría:"),
            dcc.Dropdown(
                id='dropdown-geometria',
                options=opciones_geometria,
                value='esfera', # Valor inicial
                clearable=False
            ),
            html.Br(),

            # 2. Slider Reynolds (Re)
            html.Label("Número de Reynolds (Re) [100 - 10,000]:"),
            dcc.Slider(
                id='slider-re',
                min=100,
                max=10000,
                step=100,
                value=1000, # Valor inicial
                marks={i: str(i) for i in [100, 1000, 5000, 10000]}
            ),
            html.Br(),

            # 3. Slider Schmidt (Sc)
            html.Label("Número de Schmidt (Sc) [0.6 - 3,000]:"),
            dcc.Slider(
                id='slider-sc',
                min=0.6,
                max=3000,
                step=10,
                value=500, # Valor inicial
                marks={i: str(i) for i in [0.6, 500, 1500, 3000]}
            ),
            html.Br(),

            # 4. Casilla DAB (Coeficiente de difusividad)
            html.Div([
                dcc.Checklist(
                    id='checklist-dab',
                    options=[{'label': ' Usar valor DAB (Esencial para Sh y kc)', 'value': 'DAB_ON'}],
                    value=['DAB_ON'] # Marcado por defecto
                ),
                html.Small("DAB = Coeficiente de difusividad de A en B ($m^2/s$).", style={'color': 'gray'})
            ], style={'margin-top': '10px'}),
            html.Br(),

            # 5. Parámetro adicional: Coeficiente de Difusión (DAB) para calcular kc
            html.Label("Coeficiente de Difusión (DAB) en $m^2/s$ (Ej: $1e-9$ para líquidos):"),
            dcc.Input(
                id='input-dab-valor',
                type='number',
                value=1e-9, # Valor inicial común para líquidos
                style={'width': '100%'}
            ),
        ]),

        # Columna de Resultados y Gráfica
        html.Div(style={'flex-grow': '1'}, children=[
            # --- Valores Calculados en Tiempo Real ---
            html.H3("Valores Calculados"),
            html.P([
                "Número de Sherwood (Sh): ",
                html.Span(id='output-sh', style={'font-weight': 'bold', 'color': '#1f77b4'})
            ]),
            html.P([
                "Coeficiente de Transferencia de Masa ($k_c$) en $m/s$: ",
                html.Span(id='output-kc', style={'font-weight': 'bold', 'color': '#ff7f0e'})
            ]),
            html.Hr(),

            # --- Gráfica Bidimensional ---
            html.H3("Gráfica Bidimensional (Sh vs $k_c$)"),
            dcc.Graph(id='graph-sh-kc', style={'height': '400px'}),
        ]),
    ]),

    html.Hr(),

    # --- Interpretación Automática Breve ---
    html.H3("Análisis y Correlación"),
    html.Blockquote(id='output-interpretacion', style={'border-left': '5px solid #ccc', 'padding': '10px', 'background-color': '#f9f9f9'}),
])

# --- Callbacks para la Lógica del Simulador ---

# Callback para actualizar los valores de Sh, kc, y la interpretación
@app.callback(
    [Output('output-sh', 'children'),
     Output('output-kc', 'children'),
     Output('output-interpretacion', 'children')],
    [Input('dropdown-geometria', 'value'),
     Input('slider-re', 'value'),
     Input('slider-sc', 'value'),
     Input('checklist-dab', 'value'),
     Input('input-dab-valor', 'value')]
)
def actualizar_resultados(geometria, Re, Sc, checklist_dab, DAB):
    usar_DAB = 'DAB_ON' in checklist_dab
    kc = 0.0 # Valor inicial

    # Verificación de que DAB es un número válido y positivo
    if not usar_DAB or DAB is None or not isinstance(DAB, (int, float)) or DAB <= 0:
        Sh = 0.0
        interpretacion = (
            "⚠ *ADVERTENCIA:* Debe marcar la casilla 'Usar valor DAB' e ingresar un Coeficiente de Difusión (DAB) "
            "válido y mayor a cero para poder calcular el Número de Sherwood (Sh) y el Coeficiente $\\boldsymbol{k_c}$."
        )
    else:
        # 1. Calcular Sherwood (Sh)
        Sh = calcular_sherwood(geometria, Re, Sc, usar_DAB)
        
        # 2. Calcular Coeficiente de Transferencia de Masa (kc)
        # k_c = Sh * (DAB / L_caracteristica). Asumimos L_caracteristica = 1.0 m.
        L_caracteristica = 1.0 
        kc = Sh * (DAB / L_caracteristica)

        # 3. Generar Interpretación
        interpretacion_parts = []
        # - Re
        if Re > 5000:
            interpretacion_parts.append(f"• *Re alto ({Re:.0f})* → Flujo **Turbulento** → Mayor $\\boldsymbol{{k_c}}$ (Transferencia Dominada por **Convección**).")
        elif Re < 500:
            interpretacion_parts.append(f"• *Re bajo ({Re:.0f})* → Flujo **Laminar** → Menor $\\boldsymbol{{k_c}}$.")
        else:
            interpretacion_parts.append(f"• *Re moderado ({Re:.0f})* → Flujo de Transición.")
        
        # - Sc
        if Sc > 1000:
            interpretacion_parts.append(f"• *Sc alto ({Sc:.0f})* → Difusión Lenta (**Líquidos**) → Menor $\\boldsymbol{{k_c}}$ (Resistencia a la difusión alta).")
        elif Sc < 1:
            interpretacion_parts.append(f"• *Sc bajo ({Sc:.1f})* → Difusión Rápida (**Gases**) → Mayor $\\boldsymbol{{k_c}}$.")
        else:
            interpretacion_parts.append(f"• *Sc moderado ({Sc:.1f})*")

        # - Combinación Actual
        if Sh > 1000 and Re > 5000:
              comb = "**Convección Forzada Dominante**"
        elif Sh < 100 and Sc > 1000:
              comb = "**Difusión Lenta Dominante**"
        else:
              comb = "**Transferencia combinada convección/difusión**"

        interpretacion_parts.append(f"• *Combinación actual:* {comb} para la geometría de **{geometria.capitalize()}**.")

        interpretacion = html.Ul([html.Li(html.Span(item)) for item in interpretacion_parts])

    # Formateo de los valores de salida
    sh_str = f"{Sh:.2f}"
    kc_str = f"{kc:.2e}" # Notación científica para kc

    return sh_str, kc_str, interpretacion

# Callback para actualizar la gráfica
@app.callback(
    Output('graph-sh-kc', 'figure'),
    [Input('output-sh', 'children'),
     Input('output-kc', 'children')]
)
def actualizar_grafica(Sh_str, kc_str):
    try:
        # Convertir las cadenas de texto (ej. "3.02e-03") a flotante.
        Sh = float(Sh_str)
        kc = float(kc_str)
    except ValueError:
        # En caso de error o valor inicial "0.0", usar un punto de referencia seguro.
        Sh = 1.0
        kc = 1e-10

    # Definir rangos logarítmicos fijos y dinámicos para el eje Y (kc)
    sh_min = 0.0 
    sh_max = 4.3 
    kc_min = -12.0 
    kc_max = -3.0 

    # Asegurar que el punto actual caiga bien dentro de la gráfica
    if Sh > 0:
        sh_max = max(sh_max, np.log10(Sh) + 0.5)
    if kc > 0:
        kc_max = max(kc_max, np.log10(kc) + 0.5)

    # Línea de referencia Sh ~ kc
    sh_line = np.logspace(sh_min, sh_max, 50)
    kc_line_ref = (sh_line * (kc/Sh)) if Sh > 0 else (sh_line * 1e-10)

    fig = go.Figure(
        data=[
            # Línea de referencia Sh ~ kc
            go.Scatter(
                x=sh_line,
                y=kc_line_ref,
                mode='lines',
                name='Relación Proporcional',
                line=dict(color='gray', dash='dot')
            ),
            # Punto Actual
            go.Scatter(
                x=[Sh],
                y=[kc],
                mode='markers+text',
                marker=dict(size=15, color='Red'),
                name='Punto Actual',
                text=f'Sh: {Sh:.2f}<br>kc: {kc:.2e}',
                textposition="top center"
            )
        ],
        layout=go.Layout(
            # Se usan los logaritmos de los rangos en el parámetro 'range' del eje logarítmico
            xaxis=dict(title='Eje X: Número de Sherwood (Sh)', type='log', range=[sh_min, sh_max]),
            yaxis=dict(title='Eje Y: Coeficiente $k_c$ ($m/s$)', type='log', range=[kc_min, kc_max]),
            title='Relación entre Sh y $k_c$ (Ambos son medidas de Transferencia de Masa)',
            hovermode='closest',
            margin=dict(l=40, r=40, t=40, b=40)
        )
    )
    return fig

# --- Ejecución del Servidor ---
if __name__ == '__main__':
    # CORRECCIÓN FINAL: Cambiar app.run_server(debug=True) por app.run(debug=True)
    app.run(debug=True)
