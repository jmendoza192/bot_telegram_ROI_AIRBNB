"""
🏠 Bot Analizador de Rentabilidad Airbnb CLOU v.Final
Plataforma: Telegram
Versión personalizada para Jancarlo Inmobiliario
Desarrollador: Jan
"""

from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    filters, ConversationHandler, ContextTypes
)
import logging
import os
import asyncio
import math

# ==========================================
# CONFIGURACIÓN
# ==========================================
TOKEN_TELEGRAM = os.getenv('TOKEN_TELEGRAM', 'TU_TOKEN_AQUI')

# Estados de la conversación (4 preguntas)
PRECIO, TARIFA, TCEA, PLAZO = range(4)

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==========================================
# FUNCIONES DE CÁLCULO
# ==========================================

def calcular_cuota(precio, tcea, plazo_anos):
    """
    Calcula la cuota hipotecaria con inicial del 20%
    """
    
    inicial = precio * 0.20
    prestamo = precio - inicial
    
    if prestamo <= 0:
        return None
    
    # Conversión de TCEA anual a mensual
    tcea_mensual = (tcea / 12) / 100
    
    # Número de meses
    n_meses = plazo_anos * 12
    
    # Fórmula de cuota
    factor = (tcea_mensual * (1 + tcea_mensual) ** n_meses) / ((1 + tcea_mensual) ** n_meses - 1)
    cuota_mensual = prestamo * factor
    
    return {
        "inicial": int(round(inicial)),
        "prestamo": int(round(prestamo)),
        "cuota_mensual": int(round(cuota_mensual))
    }

def calcular_rentabilidad_airbnb(precio, tarifa_diaria, tcea, plazo_anos, dias_mes):
    """
    Calcula el ROI anual para Airbnb considerando financiamiento
    """
    
    resultado_cuota = calcular_cuota(precio, tcea, plazo_anos)
    
    if not resultado_cuota:
        return None
    
    inicial = resultado_cuota['inicial']
    cuota_mensual = resultado_cuota['cuota_mensual']
    
    # Cálculos anuales
    dias_anuales = dias_mes * 12
    ingresos_anuales = tarifa_diaria * dias_anuales
    cuota_anual = cuota_mensual * 12
    gastos_operativos = ingresos_anuales * 0.15  # 15% de ingresos
    gastos_anuales = precio * 0.03  # 3% del precio
    
    # Utilidad neta
    utilidad_neta = ingresos_anuales - cuota_anual - gastos_operativos - gastos_anuales
    
    # ROI
    roi = (utilidad_neta / inicial) * 100
    
    return {
        "inicial": inicial,
        "prestamo": resultado_cuota['prestamo'],
        "cuota_mensual": cuota_mensual,
        "dias_anuales": dias_anuales,
        "ingresos_anuales": int(round(ingresos_anuales)),
        "cuota_anual": int(round(cuota_anual)),
        "gastos_operativos": int(round(gastos_operativos)),
        "gastos_anuales": int(round(gastos_anuales)),
        "utilidad_neta": int(round(utilidad_neta)),
        "roi": roi
    }

def formato_moneda(numero):
    """Convierte número a formato S/. X,XXX con comas como separadores de miles."""
    return f"S/. {numero:,}"

def formato_porcentaje(valor):
    """Formatea porcentaje con decimales"""
    if valor >= 0:
        return f"+{valor:.2f}%"
    else:
        return f"{valor:.2f}%"

# ==========================================
# MANEJADORES DE CONVERSACIÓN
# ==========================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inicia la conversación con 3 mensajes iniciales."""
    
    # MENSAJE 1: Bienvenida
    await update.message.reply_text(
        "👋 ¡Hola! Soy el asistente virtual de Jancarlo Inmobiliario.",
        parse_mode='Markdown'
    )
    
    # MENSAJE 2: Imagen sin texto
    url_imagen = "https://postimg.cc/HrD4x7YM"
    try:
        await update.message.reply_photo(photo=url_imagen)
    except:
        pass
    
    # MENSAJE 3: Propósito
    await update.message.reply_text(
        "Mi meta es ayudarte a analizar la *rentabilidad* de tu inversión en Airbnb. "
        "Con *4 preguntas simples*, sabrás exactamente cuál será tu ROI anual considerando el financiamiento.\n\n"
        "Esto te permitirá tomar decisiones de inversión inteligentes y maximizar tus ganancias con economía colaborativa.\n\n"
        "*¿Empezamos?*",
        parse_mode='Markdown'
    )
    
    # MENSAJE 4: Primera pregunta
    await update.message.reply_text(
        "📊 *Pregunta 1:* ¿Cuál es el *precio del depa* que deseas comprar?\n"
        "(En Soles)",
        parse_mode='Markdown'
    )
    
    return PRECIO

async def obtener_precio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Captura el precio del depa."""
    try:
        precio = float(update.message.text.replace(",", "."))
        if precio <= 0:
            await update.message.reply_text("❌ Por favor ingresa un monto positivo.")
            return PRECIO
        
        context.user_data['precio'] = precio
        
        # MENSAJE 5
        await update.message.reply_text(
            f"✅ Precio del depa: {formato_moneda(int(precio))}",
            parse_mode='Markdown'
        )
        
        # MENSAJE 6
        await update.message.reply_text(
            "💰 *Pregunta 2:* ¿Cuál es la *tarifa diaria promedio* que cobrarás en Airbnb?\n"
            "(En Soles. Ej: 150, 180, 250)",
            parse_mode='Markdown'
        )
        return TARIFA
        
    except ValueError:
        await update.message.reply_text(
            "❌ Por favor ingresa un número válido."
        )
        return PRECIO

async def obtener_tarifa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Captura la tarifa diaria."""
    try:
        tarifa = float(update.message.text.replace(",", "."))
        
        if tarifa <= 0:
            await update.message.reply_text("❌ Por favor ingresa un monto positivo.")
            return TARIFA
        
        context.user_data['tarifa'] = tarifa
        
        # MENSAJE 7
        await update.message.reply_text(
            f"✅ Tarifa diaria: {formato_moneda(int(tarifa))}/día",
            parse_mode='Markdown'
        )
        
        # MENSAJE 8
        await update.message.reply_text(
            "📈 *Pregunta 3:* ¿Cuál es la *TCEA (Tasa de Costo Efectivo Anual)* que te ofrece el banco?\n"
            "(En porcentaje. Ej: 9.5, 8.2, 7.8. Incluye comisiones y seguros)",
            parse_mode='Markdown'
        )
        return TCEA
        
    except ValueError:
        await update.message.reply_text(
            "❌ Por favor ingresa un número válido."
        )
        return TARIFA

async def obtener_tcea(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Captura la TCEA."""
    try:
        tcea = float(update.message.text.replace(",", "."))
        
        if tcea <= 0 or tcea > 50:
            await update.message.reply_text("❌ Por favor ingresa una TCEA válida (entre 0 y 50%).")
            return TCEA
        
        context.user_data['tcea'] = tcea
        
        # MENSAJE 9
        await update.message.reply_text(
            f"✅ TCEA: {tcea}%",
            parse_mode='Markdown'
        )
        
        # MENSAJE 10
        await update.message.reply_text(
            "⏱️ *Pregunta 4 (última):* ¿En cuántos años deseas pagar el depa?\n"
            "(Opciones: 10, 15, 20 o 25 años)",
            parse_mode='Markdown'
        )
        return PLAZO
        
    except ValueError:
        await update.message.reply_text(
            "❌ Por favor ingresa un número válido."
        )
        return TCEA

async def obtener_plazo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Captura el plazo y calcula los resultados."""
    try:
        plazo = int(update.message.text.strip())
        plazos_validos = [10, 15, 20, 25]
        
        if plazo not in plazos_validos:
            await update.message.reply_text(
                "❌ Por favor ingresa un plazo válido: 10, 15, 20 o 25 años."
            )
            return PLAZO
        
        context.user_data['plazo'] = plazo
        
        # Obtener datos
        precio = context.user_data['precio']
        tarifa = context.user_data['tarifa']
        tcea = context.user_data['tcea']
        
        # Calcular rentabilidad para escenario base (20 días/mes)
        resultado_base = calcular_rentabilidad_airbnb(precio, tarifa, tcea, plazo, 20)
        
        if not resultado_base:
            await update.message.reply_text("❌ Error en el cálculo. Por favor intenta de nuevo.")
            return PLAZO
        
        # MENSAJE 11: Resultado - PARTE 1 (Datos principales)
        respuesta_parte1 = (
            f"📌 *RESULTADO DE TU ANÁLISIS AIRBNB*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"• Precio del depa: *{formato_moneda(int(precio))}*\n"
            f"• Tarifa diaria: *{formato_moneda(int(tarifa))}/día*\n"
            f"• TCEA: *{tcea}%*\n"
            f"• Plazo financiamiento: *{plazo} años*\n"
            f"• Cuota mensual: *{formato_moneda(resultado_base['cuota_mensual'])}*"
        )
        
        await update.message.reply_text(respuesta_parte1, parse_mode='Markdown')
        await asyncio.sleep(0.5)
        
        # MENSAJE 12: Resultado - PARTE 2 (Análisis escenario base)
        estado_roi = "❌ NO RENTABLE" if resultado_base['roi'] < 0 else "✅ MUY RENTABLE"
        
        respuesta_parte2 = (
            f"💡 *ANÁLISIS AIRBNB - ESCENARIO BASE (20 días/mes ocupados):*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Inicial requerida (20%): *{formato_moneda(resultado_base['inicial'])}*\n"
            f"Préstamo: *{formato_moneda(resultado_base['prestamo'])}*\n"
            f"\n"
            f"Ingresos anuales (240 días): *{formato_moneda(resultado_base['ingresos_anuales'])}*\n"
            f"Cuota anual: *{formato_moneda(resultado_base['cuota_anual'])}*\n"
            f"Gastos operativos Airbnb (15%): *{formato_moneda(resultado_base['gastos_operativos'])}*\n"
            f"Gastos anuales (3%): *{formato_moneda(resultado_base['gastos_anuales'])}*\n"
            f"\n"
            f"Utilidad neta anual: *{formato_moneda(resultado_base['utilidad_neta'])}*\n"
            f"*ROI anual: {formato_porcentaje(resultado_base['roi'])}* {estado_roi}"
        )
        
        await update.message.reply_text(respuesta_parte2, parse_mode='Markdown')
        await asyncio.sleep(0.5)
        
        # MENSAJE 13: Tabla comparativa (3 escenarios)
        resultado_15 = calcular_rentabilidad_airbnb(precio, tarifa, tcea, plazo, 15)
        resultado_25 = calcular_rentabilidad_airbnb(precio, tarifa, tcea, plazo, 25)
        
        respuesta_parte3 = (
            f"📊 *ESCENARIOS SEGÚN OCUPACIÓN MENSUAL:*\n"
            f"(Mismo precio y tarifa)\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        )
        
        if resultado_15:
            estado_15 = "❌" if resultado_15['roi'] < 0 else "✅"
            respuesta_parte3 += f"Escenario 1: 15 días/mes ocupados (180 días/año)\n"
            respuesta_parte3 += f"Ingresos: {formato_moneda(resultado_15['ingresos_anuales'])} → *ROI: {formato_porcentaje(resultado_15['roi'])}* {estado_15}\n\n"
        
        estado_base = "❌" if resultado_base['roi'] < 0 else "✅"
        respuesta_parte3 += f"Escenario 2: 20 días/mes ocupados (240 días/año)\n"
        respuesta_parte3 += f"Ingresos: {formato_moneda(resultado_base['ingresos_anuales'])} → *ROI: {formato_porcentaje(resultado_base['roi'])}* {estado_base} (Base)\n\n"
        
        if resultado_25:
            estado_25 = "❌" if resultado_25['roi'] < 0 else "✅"
            respuesta_parte3 += f"Escenario 3: 25 días/mes ocupados (300 días/año)\n"
            respuesta_parte3 += f"Ingresos: {formato_moneda(resultado_25['ingresos_anuales'])} → *ROI: {formato_porcentaje(resultado_25['roi'])}* {estado_25}"
        
        await update.message.reply_text(respuesta_parte3, parse_mode='Markdown')
        await asyncio.sleep(0.5)
        
        # MENSAJE 14: Consideraciones importantes
        await update.message.reply_text(
            "⚠️ *CONSIDERACIONES IMPORTANTES:*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "💡 Gastos operativos Airbnb (15%): Comisión Airbnb, limpieza entre huéspedes, mantenimiento.\n\n"
            "💡 Gastos anuales (3%): Predial, impuestos, servicios básicos cuando está vacío.\n\n"
            "💡 El ROI es sobre tu capital inicial invertido (inicial del 20%).\n\n"
            "💡 Este análisis no incluye plusvalía (aumento del valor del depa).\n\n"
            "💡 Ocupación: 15-20 días/mes es conservador, 25+ días es excelente.",
            parse_mode='Markdown'
        )
        await asyncio.sleep(0.5)
        
        # MENSAJE 15: Información referencial
        await update.message.reply_text(
            "ℹ️ Este cálculo es *referencial*. Si deseas un análisis completo con proyecciones a 5 o 10 años incluyendo plusvalía, "
            "entonces necesitas una *asesoría personalizada de inversión*. 📞 Puedes agendarla al Whatsapp 📲 920605559 o al siguiente link:",
            parse_mode='Markdown'
        )
        await asyncio.sleep(0.5)
        
        # MENSAJE 16: Link de WhatsApp
        await update.message.reply_text(
            "https://wa.link/9nuspm"
        )
        await asyncio.sleep(0.5)
        
        # MENSAJE 17: Opción de nuevo cálculo
        await update.message.reply_text(
            "¿Deseas hacer otro análisis? Escribe /start"
        )
        
        # Limpiar datos del usuario
        context.user_data.clear()
        
        return ConversationHandler.END
        
    except ValueError:
        await update.message.reply_text(
            "❌ Por favor ingresa un número válido."
        )
        return PLAZO

async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancela la conversación."""
    await update.message.reply_text(
        "❌ Operación cancelada.\n\nEscribe /start para comenzar de nuevo.",
        parse_mode='Markdown'
    )
    return ConversationHandler.END

async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra la ayuda."""
    await update.message.reply_text(
        "🆘 *AYUDA - Bot Analizador de Rentabilidad Airbnb*\n\n"
        "*Comandos disponibles:*\n"
        "/start - Iniciar nuevo análisis\n"
        "/ayuda - Ver esta ayuda\n"
        "/info - Información sobre el bot",
        parse_mode='Markdown'
    )

async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra información del bot."""
    await update.message.reply_text(
        "ℹ️ *INFORMACIÓN DEL BOT*\n\n"
        "*Bot:* Analizador de Rentabilidad Airbnb v.Final\n"
        "*Desarrollador:* Jancarlo Inmobiliario\n"
        "*Plataforma:* Telegram\n\n"
        "*Parámetros:*\n"
        "• Inicial: 20% del precio (fijo)\n"
        "• Financiamiento: 100% automático\n"
        "• TCEA: Incluye comisiones y seguros\n"
        "• Gastos operativos Airbnb: 15% de ingresos\n"
        "• Gastos anuales: 3% del precio\n"
        "• Plazos: 10, 15, 20, 25 años",
        parse_mode='Markdown'
    )

# ==========================================
# MAIN - Inicializar Bot
# ==========================================

def main():
    """Inicia el bot."""
    
    if TOKEN_TELEGRAM == 'TU_TOKEN_AQUI':
        logger.error("❌ ERROR: Debes configurar tu TOKEN_TELEGRAM")
        return
    
    application = Application.builder().token(TOKEN_TELEGRAM).build()
    
    # Manejador de conversación
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            PRECIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, obtener_precio)],
            TARIFA: [MessageHandler(filters.TEXT & ~filters.COMMAND, obtener_tarifa)],
            TCEA: [MessageHandler(filters.TEXT & ~filters.COMMAND, obtener_tcea)],
            PLAZO: [MessageHandler(filters.TEXT & ~filters.COMMAND, obtener_plazo)],
        },
        fallbacks=[CommandHandler('cancelar', cancelar)]
    )
    
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler('ayuda', ayuda))
    application.add_handler(CommandHandler('info', info))
    
    logger.info("🚀 Bot Analizador de Rentabilidad Airbnb iniciado correctamente")
    application.run_polling()

if __name__ == '__main__':
    main()
