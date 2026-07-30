from typing import Any, Dict

# The common visual separator for premium messages
SEPARATOR = "━━━━━━━━━━━━━━━━"
HEADER = "✈️ SANS AIRLINES\n" + SEPARATOR
FOOTER = SEPARATOR + "\nАвтоматическое уведомление\nSANS Airlines"

def generate_flight_notification(event_type: str, passenger: Any, flight: Any, language: str = 'ru') -> str:
    """
    Generates a premium flight notification message similar to Emirates or Qatar Airways.
    """
    
    # Safe extraction of fields
    flight_number = flight.flight_number if hasattr(flight, 'flight_number') else getattr(flight, 'flight_id', '')
    gate = getattr(flight, 'gate', 'TBD')
    if not gate:
        gate = 'TBD'
    
    terminal = getattr(flight, 'terminal', 'TBD')
    if not terminal:
        terminal = 'TBD'
        
    airport = "Аэропорт Туркестан" if language == 'ru' else "Түркістан әуежайы" if language == 'kk' else "Turkistan Airport"
    passenger_name = getattr(passenger, 'name', None) or getattr(passenger, 'first_name', "Пассажир")
    
    time_val = ""
    if hasattr(flight, 'scheduled_departure') and flight.scheduled_departure:
        time_val = flight.scheduled_departure.strftime("%H:%M")
        
    origin = getattr(flight, 'origin', '')
    dest = getattr(flight, 'destination', '')

    # Base dictionary for different languages
    templates: Dict[str, Dict[str, str]] = {
        'ru': {
            'GREETING': f"Уважаемый(ая) {passenger_name}!",
            'DELAYED_TITLE': "🔔 Внимание: Задержка рейса",
            'DELAYED_BODY': f"Ваш рейс:\n✈️ Рейс: {flight_number}\n\nК сожалению, время вылета изменено.\n\n⏰ Новое время вылета: {time_val}\n📍 Gate: {gate}",
            
            'CANCELLED_TITLE': "🚫 Внимание: Рейс отменен",
            'CANCELLED_BODY': f"Ваш рейс:\n✈️ Рейс: {flight_number}\n\nК сожалению, рейс отменен. Пожалуйста, обратитесь к представителям авиакомпании для переоформления билета.",
            
            'GATE_CHANGED_TITLE': "🔔 Важное обновление по вашему рейсу",
            'GATE_CHANGED_BODY': f"Ваш рейс:\n✈️ Рейс: {flight_number}\n\nПроизошло изменение зоны посадки:\n\n🛫 Новый выход на посадку:\n📍 Gate {gate}",
            
            'BOARDING_TITLE': "🛫 Посадка открыта",
            'BOARDING_BODY': f"Ваш рейс:\n✈️ Рейс: {flight_number}\n\nПросим пассажиров пройти к выходу на посадку.\n\n📍 Gate: {gate}",
            
            'BOARDING_CLOSED_TITLE': "🛑 Посадка завершена",
            'BOARDING_CLOSED_BODY': f"Ваш рейс:\n✈️ Рейс: {flight_number}\n\nПосадка на ваш рейс успешно завершена.",
            
            'TIME_CHANGED_TITLE': "⏰ Изменение времени вылета",
            'TIME_CHANGED_BODY': f"Ваш рейс:\n✈️ Рейс: {flight_number}\n\nВремя вылета было обновлено:\n\n⏰ Новый вылет: {time_val}",
            
            'TERMINAL_CHANGED_TITLE': "🏢 Изменение терминала",
            'TERMINAL_CHANGED_BODY': f"Ваш рейс:\n✈️ Рейс: {flight_number}\n\nВаш рейс будет обслуживаться в другом терминале:\n\n🏢 Новый терминал: {terminal}",
            
            'ON_TIME_TITLE': "✅ Статус рейса: По расписанию",
            'ON_TIME_BODY': f"Ваш рейс:\n✈️ Рейс: {flight_number}\n\nВаш рейс готовится к вылету по расписанию.\n\n⏰ Время вылета: {time_val}\n📍 Gate: {gate}",
            
            'FOOTER_MSG': f"🏢 Аэропорт:\n{airport}\n\nПожалуйста, направляйтесь к выходу на посадку заранее.\nСпасибо, что выбираете SANS Airlines.\nЖелаем вам приятного полёта! ✈️"
        },
        'en': {
            'GREETING': f"Dear {passenger_name},",
            'DELAYED_TITLE': "🔔 Attention: Flight Delayed",
            'DELAYED_BODY': f"Your flight:\n✈️ Flight: {flight_number}\n\nUnfortunately, the departure time has been changed.\n\n⏰ New departure: {time_val}\n📍 Gate: {gate}",
            
            'CANCELLED_TITLE': "🚫 Attention: Flight Cancelled",
            'CANCELLED_BODY': f"Your flight:\n✈️ Flight: {flight_number}\n\nUnfortunately, this flight has been cancelled. Please contact airline staff for assistance.",
            
            'GATE_CHANGED_TITLE': "🔔 Important Flight Update",
            'GATE_CHANGED_BODY': f"Your flight:\n✈️ Flight: {flight_number}\n\nThere is a change in your boarding gate:\n\n🛫 New Gate:\n📍 Gate {gate}",
            
            'BOARDING_TITLE': "🛫 Boarding Now",
            'BOARDING_BODY': f"Your flight:\n✈️ Flight: {flight_number}\n\nBoarding has commenced. Please proceed to the gate.\n\n📍 Gate: {gate}",
            
            'BOARDING_CLOSED_TITLE': "🛑 Boarding Closed",
            'BOARDING_CLOSED_BODY': f"Your flight:\n✈️ Flight: {flight_number}\n\nBoarding for this flight is now closed.",
            
            'TIME_CHANGED_TITLE': "⏰ Departure Time Update",
            'TIME_CHANGED_BODY': f"Your flight:\n✈️ Flight: {flight_number}\n\nThe departure time has been updated:\n\n⏰ New departure: {time_val}",
            
            'TERMINAL_CHANGED_TITLE': "🏢 Terminal Change",
            'TERMINAL_CHANGED_BODY': f"Your flight:\n✈️ Flight: {flight_number}\n\nYour flight will now operate from a different terminal:\n\n🏢 New Terminal: {terminal}",
            
            'ON_TIME_TITLE': "✅ Flight Status: On Time",
            'ON_TIME_BODY': f"Your flight:\n✈️ Flight: {flight_number}\n\nYour flight is operating on schedule.\n\n⏰ Departure: {time_val}\n📍 Gate: {gate}",
            
            'FOOTER_MSG': f"🏢 Airport:\n{airport}\n\nPlease proceed to the gate in advance.\nThank you for choosing SANS Airlines.\nWe wish you a pleasant flight! ✈️"
        },
        'kk': {
            'GREETING': f"Құрметті {passenger_name}!",
            'DELAYED_TITLE': "🔔 Назар аударыңыз: Рейс кешіктірілді",
            'DELAYED_BODY': f"Сіздің рейсіңіз:\n✈️ Рейс: {flight_number}\n\nӨкінішке орай, ұшу уақыты өзгерді.\n\n⏰ Жаңа ұшу уақыты: {time_val}\n📍 Gate: {gate}",
            
            'CANCELLED_TITLE': "🚫 Назар аударыңыз: Рейс болдырылмады",
            'CANCELLED_BODY': f"Сіздің рейсіңіз:\n✈️ Рейс: {flight_number}\n\nРейс болдырылмады. Билетті қайта ресімдеу үшін авиакомпания өкілдеріне хабарласыңыз.",
            
            'GATE_CHANGED_TITLE': "🔔 Рейс бойынша маңызды жаңалық",
            'GATE_CHANGED_BODY': f"Сіздің рейсіңіз:\n✈️ Рейс: {flight_number}\n\nОтырғызу аймағы өзгерді:\n\n🛫 Жаңа гейт:\n📍 Gate {gate}",
            
            'BOARDING_TITLE': "🛫 Отырғызу басталды",
            'BOARDING_BODY': f"Сіздің рейсіңіз:\n✈️ Рейс: {flight_number}\n\nЖолаушыларды отырғызу қақпасына өтуін сұраймыз.\n\n📍 Gate: {gate}",
            
            'BOARDING_CLOSED_TITLE': "🛑 Отырғызу аяқталды",
            'BOARDING_CLOSED_BODY': f"Сіздің рейсіңіз:\n✈️ Рейс: {flight_number}\n\nОтырғызу сәтті аяқталды.",
            
            'TIME_CHANGED_TITLE': "⏰ Ұшу уақыты өзгерді",
            'TIME_CHANGED_BODY': f"Сіздің рейсіңіз:\n✈️ Рейс: {flight_number}\n\nҰшу уақыты жаңартылды:\n\n⏰ Жаңа ұшу уақыты: {time_val}",
            
            'TERMINAL_CHANGED_TITLE': "🏢 Терминал өзгерді",
            'TERMINAL_CHANGED_BODY': f"Сіздің рейсіңіз:\n✈️ Рейс: {flight_number}\n\nРейс басқа терминалдан қызмет көрсетеді:\n\n🏢 Жаңа терминал: {terminal}",
            
            'ON_TIME_TITLE': "✅ Рейс статусы: Кесте бойынша",
            'ON_TIME_BODY': f"Сіздің рейсіңіз:\n✈️ Рейс: {flight_number}\n\nРейс кестеге сай ұшуға дайындалуда.\n\n⏰ Ұшу уақыты: {time_val}\n📍 Gate: {gate}",
            
            'FOOTER_MSG': f"🏢 Әуежай:\n{airport}\n\nОтырғызу қақпасына алдын ала баруыңызды сұраймыз.\nSANS Airlines таңдағаныңызға рахмет.\nАқ жол тілейміз! ✈️"
        }
    }

    # Fallback to English if language not supported
    t = templates.get(language) or templates['en']
    
    title_key = f"{event_type}_TITLE"
    body_key = f"{event_type}_BODY"
    
    title = t.get(title_key, t.get('ON_TIME_TITLE'))
    body = t.get(body_key, t.get('ON_TIME_BODY'))
    
    # Compose final message
    lines = [
        HEADER,
        "",
        t['GREETING'],
        "",
        title,
        "",
        body,
        "",
        t['FOOTER_MSG'],
        "",
        FOOTER
    ]
    
    return "\n".join(lines)
