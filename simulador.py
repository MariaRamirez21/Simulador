    Consulta exitosa

El error sigue siendo el mismo: ModuleNotFoundError: Ningún módulo llamado 'app'.

Esto significa que el servidor Gunicorn que usa Render no está encontrando el objeto de la aplicación Dash (app o server) en el archivo que le especificaste.

Incluso si el código Python es correcto, si el comando de inicio de Render es erróneo, fallará.

🔑 Solución Definitiva para Render

Ya que has confirmado que el error persiste incluso después de nombrar la aplicación como server y usar el comando gunicorn simulador:server (lo cual es la forma estándar para un archivo llamado simulador.py), la causa más probable es que Render está utilizando un nombre de módulo predeterminado diferente o tu archivo no se llama simulador.py.

Dado que el código es correcto, la corrección final se centra en la configuración del servidor, asegurando que Gunicorn sepa dónde buscar.

1. Ajuste del Código (Nomenclatura Estándar)

Para maximizar la compatibilidad, usaremos la nomenclatura estándar de Dash/Flask y crearemos un objeto explícito llamado server.

Asegúrate de que las siguientes líneas estén en tu código:
Python

# --- Inicialización de la Aplicación Dash ---
app = dash.Dash(__name__) 

# Esto es lo que Gunicorn busca para servir la aplicación
server = app.server 

(Esta parte ya estaba corregida en el código anterior, por lo que el problema está en la configuración de Render).

2. Configuración Crítica en Render (Comando de Inicio)

Debes verificar que el nombre del archivo en tu repositorio de código coincida exactamente con el comando de inicio en Render.
Nombre de tu Archivo	Comando de Inicio en Render
simulador.py	gunicorn simulador:server
app.py (Recomendado)	gunicorn app:server

Si el archivo se llama simulador.py, usa el primer comando. Si no funciona, te recomiendo encarecidamente renombrar tu archivo a app.py (la convención más común) y usar el segundo comando.

Si el error persiste incluso con el comando correcto, puedes probar la sintaxis alternativa de Gunicorn:
Bash

gunicorn 'simulador:app.server' 

o (si renombraste el archivo a app.py):
Bash

gunicorn 'app:app.server' 

💻 Código Completo Final (Listo para Despliegue)

Este es el mismo código de la respuesta anterior, que es el correcto, pero con énfasis en la variable server para el despliegue y con la línea de ejecución local comentada.

Si usas este código, el comando de inicio en Render debe ser gunicorn simulador:server (asumiendo que el archivo se llama simulador.py).
Python

import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import numpy as np

# --- Fórmulas/Correlaciones para el Número de Sherwood (Sh) ---

def calcular_sherwood(geometria, Re, Sc, usar_DAB=False):
    # ... (cuerpo de la función sin cambios, ya está correcto) ...
    if not usar_DAB:
        return 0.0

    if geometria == 'placa':
        Sh = 0.037 * (Re**0.8) * (Sc**(1/3))
    elif geometria == 'tubo':
        Sh = 0.023 * (Re**0.8) * (Sc**(1/3))
    elif geometria == 'esfera':
        Sh = 2.0 + 0.6 * (Re**0.5) * (Sc**(1/3))
    elif geometria == 'gota':
        Sh = 2.0 + 0.6 * (Re**0.5) * (Sc**(1/3))
    elif geometria == 'lecho empacado':
        Sh = 1.15 * (Re**0.6) * (Sc**(1/3))
    else:
        Sh = 0.0
    return Sh

# --- Inicialización de la Aplicación Dash ---
app = dash.Dash(__name__) 

# ESTA LÍNEA ES VITAL PARA GUNICORN/RENDER
# Gunicorn busca el objeto 'server' o 'app' para arrancar.
server = app.server

# --- Definición de Componentes de la Interfaz ---
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
    # ... (resto del layout sin cambios) ...

    html.Div(style={'display': 'flex', 'flex-direction': 'row', 'gap': '30px'}, children=[
        html.Div(style={'width': '300px'}, children=[
            html.H3("Controles"),
            html.Label("Geometría:"),
            dcc.Dropdown(id='dropdown-geometria', options=opciones_geometria, value='esfera', clearable=False),
            html.Br(),
            html.Label("Número de Reynolds (Re) [100 - 10,000]:"),
            dcc.Slider(id='slider-re', min=100, max=10000, step=100, value=1000, marks={i: str(i) for i in [100, 1000, 5000, 10000]}),
            html.Br(),
            html.Label("Número de Schmidt (Sc) [0.6 - 3,000]:"),
            dcc.Slider(id='slider-sc', min=0.6, max=3000, step=10, value=500, marks={i: str(i) for i in [0.6, 500, 1500, 3000]}),
            html.Br(),
            html.Div([
                dcc.Checklist(id='checklist-dab', options=[{'label': ' Usar valor DAB (Esencial para Sh y kc)', 'value': 'DAB_ON'}], value=['DAB_ON']),
                html.Small("DAB = Coeficiente de difusividad de A en B ($m^2/s$).", style={'color': 'gray'})
            ], style={'margin-top': '10px'}),
            html.Br(),
            html.Label("Coeficiente de Difusión (DAB) en $m^2/s$ (Ej: $1e-9$ para líquidos):"),
            dcc.Input(id='input-dab-valor', type='number', value=1e-9, style={'width': '100%'}),
        ]),

        html.Div(style={'flex-grow': '1'}, children=[
            html.H3("Valores Calculados"),
            html.P(["Número de Sherwood (Sh): ", html.Span(id='output-sh', style={'font-weight': 'bold', 'color': '#1f77b4'})]),
            html.P(["Coeficiente de Transferencia de Masa ($k_c$) en $m/s$: ", html.Span(id='output-kc', style={'font-weight': 'bold', 'color': '#ff7f0e'})]),
            html.Hr(),
            html.H3("Gráfica Bidimensional (Sh vs $k_c$)"),
            dcc.Graph(id='graph-sh-kc', style={'height': '400px'}),
        ]),
    ]),
    html.Hr(),
    html.H3("Análisis y Correlación"),
    html.Blockquote(id='output-interpretacion', style={'border-left': '5px solid #ccc', 'padding': '10px', 'background-color': '#f9f9f9'}),
])

# --- Callbacks (Sin Cambios) ---

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
    kc = 0.0

    if not usar_DAB or DAB is None or not isinstance(DAB, (int, float)) or DAB <= 0:
        Sh = 0.0
        interpretacion = (
            "⚠ *ADVERTENCIA:* Debe marcar la casilla 'Usar valor DAB' e ingresar un Coeficiente de Difusión (DAB) "
            "válido y mayor a cero para poder calcular el Número de Sherwood (Sh) y el Coeficiente $\\boldsymbol{k_c}$."
        )
    else:
        Sh = calcular_sherwood(geometria, Re, Sc, usar_DAB)
        L_caracteristica = 1.0 
        kc = Sh * (DAB / L_caracteristica)
        
        # 3. Generar Interpretación (Lógica sin cambios)
        interpretacion_parts = []
        if Re > 5000:
            interpretacion_parts.append(f"• *Re alto ({Re:.0f})* → Flujo **Turbulento** → Mayor $\\boldsymbol{{k_c}}$ (Transferencia Dominada por **Convección**).")
        elif Re < 500:
            interpretacion_parts.append(f"• *Re bajo ({Re:.0f})* → Flujo **Laminar** → Menor $\\boldsymbol{{k_c}}$.")
        else:
            interpretacion_parts.append(f"• *Re moderado ({Re:.0f})* → Flujo de Transición.")
        
        if Sc > 1000:
            interpretacion_parts.append(f"• *Sc alto ({Sc:.0f})* → Difusión Lenta (**Líquidos**) → Menor $\\boldsymbol{{k_c}}$ (Resistencia a la difusión alta).")
        elif Sc < 1:
            interpretacion_parts.append(f"• *Sc bajo ({Sc:.1f})* → Difusión Rápida (**Gases**) → Mayor $\\boldsymbol{{k_c}}$.")
        else:
            interpretacion_parts.append(f"• *Sc moderado ({Sc:.1f})*")

        if Sh > 1000 and Re > 5000:
              comb = "**Convección Forzada Dominante**"
        elif Sh < 100 and Sc > 1000:
              comb = "**Difusión Lenta Dominante**"
        else:
              comb = "**Transferencia combinada convección/difusión**"

        interpretacion_parts.append(f"• *Combinación actual:* {comb} para la geometría de **{geometria.capitalize()}**.")

        interpretacion = html.Ul([html.Li(html.Span(item)) for item in interpretacion_parts])

    sh_str = f"{Sh:.2f}"
    kc_str = f"{kc:.2e}"
    return sh_str, kc_str, interpretacion

@app.callback(
    Output('graph-sh-kc', 'figure'),
    [Input('output-sh', 'children'),
     Input('output-kc', 'children')]
)
def actualizar_grafica(Sh_str, kc_str):
    try:
        Sh = float(Sh_str)
        kc = float(kc_str)
    except ValueError:
        Sh = 1.0
        kc = 1e-10

    sh_min = 0.0 
    sh_max = 4.3 
    kc_min = -12.0 
    kc_max = -3.0 

    if Sh > 0:
        sh_max = max(sh_max, np.log10(Sh) + 0.5)
    if kc > 0:
        kc_max = max(kc_max, np.log10(kc) + 0.5)

    sh_line = np.logspace(sh_min, sh_max, 50)
    kc_line_ref = (sh_line * (kc/Sh)) if Sh > 0 else (sh_line * 1e-10)

    fig = go.Figure(
        data=[
            go.Scatter(
                x=sh_line,
                y=kc_line_ref,
                mode='lines',
                name='Relación Proporcional',
                line=dict(color='gray', dash='dot')
            ),
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
            xaxis=dict(title='Eje X: Número de Sherwood (Sh)', type='log', range=[sh_min, sh_max]),
            yaxis=dict(title='Eje Y: Coeficiente $k_c$ ($m/s$)', type='log', range=[kc_min, kc_max]),
            title='Relación entre Sh y $k_c$ (Ambos son medidas de Transferencia de Masa)',
            hovermode='closest',
            margin=dict(l=40, r=40, t=40, b=40)
        )
    )
    return fig

# --- Ejecución del Servidor (IMPORTANTE: Se elimina la ejecución local) ---
if __name__ == '__main__':
    # Esta sección se mantiene solo para que Python no se queje de sintaxis
    # NUNCA debe contener app.run() o app.run_server() en un entorno de hosting
    pass 
