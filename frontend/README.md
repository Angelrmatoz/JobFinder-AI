# 💻 JobFinder AI — Frontend Application

Esta es la aplicación cliente para **JobFinder AI**, construida con **React 19**, **Vite** y **Tailwind CSS**. Proporciona una experiencia de usuario interactiva y fluida para cargar currículums mediante Drag & Drop, visualizar logs en tiempo real durante el análisis, desplegar vacantes de empleo con sus puntajes de afinidad y chatear con el Asesor de Carrera por IA.

---

## Estructura del Código

```
frontend/
├── src/
│   ├── components/            # Componentes React modulares
│   │   ├── Badge.jsx          # Etiquetas para estados y tecnologías
│   │   ├── Section.jsx        # Contenedor semántico de secciones
│   │   ├── LoadingPulse.jsx   # Indicador animado de estado de carga y progreso
│   │   ├── ResultsPanel.jsx   # Despliegue de perfil del candidato y ofertas de empleo
│   │   ├── ChatPanel.jsx      # Panel interactivo de chat con la IA
│   │   └── __tests__/         # Pruebas unitarias de componentes
│   │       ├── Badge.test.jsx
│   │       ├── ResultsPanel.test.jsx
│   │       └── ChatPanel.test.jsx
│   │
│   ├── __tests__/
│   │   └── App.integration.test.jsx # Prueba de integración del flujo de subida y renderizado
│   │
│   ├── e2e/
│   │   └── app.spec.js        # Prueba E2E multiplataforma (Chromium/Webkit)
│   │
│   ├── App.jsx                # Componente principal / Orquestador de la UI
│   ├── main.jsx               # Archivo de entrada de React
│   ├── index.css              # Directivas de Tailwind CSS y estilos globales
│   └── setupTests.js          # Configuración global de pruebas unitarias
│
├── index.html                 # Plantilla HTML base
├── playwright.config.js       # Configuración del servidor de pruebas E2E (Playwright)
├── vite.config.js             # Configuración de empaquetado y pruebas (Vitest)
└── package.json               # Dependencias y scripts
```

---

## Ejecución Local

1. **Instalar dependencias**:
   ```bash
   pnpm install
   ```
2. **Iniciar servidor de desarrollo**:
   ```bash
   pnpm run dev
   ```
   Abre tu navegador en `http://localhost:5173`.

---

## Suite de Pruebas

El frontend incluye pruebas unitarias, de integración y pruebas de interfaz de extremo a extremo (E2E).

### 1. Pruebas Unitarias e Integración (Vitest)
Evalúan los componentes de forma aislada y simulan el comportamiento del DOM utilizando mocks de red (`axios`).
```bash
pnpm test run
```

### 2. Pruebas E2E (Playwright)
Prueban la interfaz en navegadores reales (Chrome y Safari de forma simultánea).
```bash
# Instala los navegadores necesarios (solo la primera vez)
pnpm exec playwright install

# Corre el servidor local e inicia las pruebas E2E
pnpm test:e2e
```
